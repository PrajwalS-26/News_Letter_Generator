"""Main CLI for newsletter generation."""

import os
import sys
import yaml
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.llm.ollama_client import OllamaClient, GroqClient
from src.collector.rss_collector import RSSCollector
from src.processor.content_filter import ContentFilter
from src.processor.newsletter_gen import NewsletterGenerator
from src.renderer.html_renderer import HTMLRenderer
from src.renderer.pdf_renderer import PDFRenderer
from src.distribution.email_sender import EmailSender
from src.distribution.slack_poster import SlackPoster


def load_config():
    """Load configuration files."""
    config_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config")

    with open(os.path.join(config_dir, "feeds.yaml"), "r") as f:
        feeds_config = yaml.safe_load(f)

    with open(os.path.join(config_dir, "newsletter.yaml"), "r") as f:
        newsletter_config = yaml.safe_load(f)

    return feeds_config, newsletter_config


def main():
    parser = argparse.ArgumentParser(
        description="Generate newsletter for Salesforce AAA UVCE"
    )
    parser.add_argument("--date", type=str, help="Newsletter date (YYYY-MM-DD)")
    parser.add_argument("--preview", action="store_true", help="Preview without sending")
    parser.add_argument("--send", nargs="+", choices=["email", "slack"],
                        help="Send to specific channels")
    parser.add_argument("--output-dir", type=str, help="Output directory")
    parser.add_argument("--model", type=str, help="LLM model to use")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")

    args = parser.parse_args()

    # Load environment variables
    load_dotenv()

    # Load config
    feeds_config, newsletter_config = load_config()

    # Override model if specified
    if args.model:
        newsletter_config["newsletter"]["llm"]["model"] = args.model

    llm_config = newsletter_config["newsletter"]["llm"]

    print("=" * 50)
    print("Newsletter Generator - Salesforce AAA UVCE")
    print("=" * 50)

    # Initialize components
    print("\n[1/6] Initializing LLM client...")
    api_key = os.getenv("GROQ_API_KEY", "")

    # Auto-switch: Use Groq if API key available, else Ollama
    if api_key:
        llm_client = GroqClient(
            api_key=api_key,
            model=llm_config.get("model", "llama-3.1-70b-versatile")
        )
        print("   Using Groq cloud API (fast, free)")
    else:
        llm_client = OllamaClient(
            host=os.getenv("OLLAMA_HOST", llm_config["host"]),
            model=llm_config["model"]
        )
        if not llm_client.is_available():
            print(f"Warning: Model '{llm_config['model']}' not found in Ollama")
            print("Available models:", llm_client.list_models())
            print("\nPull the model with: ollama pull", llm_config["model"])
            response = input("Continue anyway? (y/N): ")
            if response.lower() != "y":
                return
        print("   Using Ollama local LLM")

    # Collect articles
    print("\n[2/6] Collecting articles from RSS feeds...")
    collector = RSSCollector(feeds_config)
    articles = collector.collect_all(days_back=7)
    print(f"   Found {len(articles)} articles")

    if not articles:
        print("No articles found. Check your RSS feed configuration.")
        return

    # Filter and rank
    print("\n[3/6] Filtering and ranking content...")
    content_filter = ContentFilter(
        max_per_section=newsletter_config["newsletter"].get("max_articles_per_section", 5)
    )
    categorized = content_filter.filter_and_rank(articles)
    for cat, arts in categorized.items():
        print(f"   {cat}: {len(arts)} articles")

    # Generate newsletter content
    print("\n[4/6] Generating newsletter content with LLM...")
    generator = NewsletterGenerator(llm_client, newsletter_config)
    newsletter_content = generator.generate(categorized)
    print(f"   Title: {newsletter_content['title']}")

    # Determine output directory
    output_dir = args.output_dir or newsletter_config["newsletter"]["output"]["directory"]
    os.makedirs(output_dir, exist_ok=True)

    # Generate date string
    if args.date:
        date_str = args.date
    else:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Render HTML
    print("\n[5/6] Rendering HTML newsletter...")
    html_renderer = HTMLRenderer()
    html_path = os.path.join(output_dir, f"newsletter_{date_str}.html")
    html_renderer.render(newsletter_content, html_path)
    print(f"   Saved: {html_path}")

    # Render PDF
    pdf_path = None
    if not args.no_pdf:
        print("\n[6/6] Generating PDF...")
        try:
            pdf_renderer = PDFRenderer()
            pdf_path = os.path.join(output_dir, f"newsletter_{date_str}.pdf")
            pdf_renderer.render(html_path, pdf_path)
            print(f"   Saved: {pdf_path}")
        except Exception as e:
            print(f"   PDF generation failed: {e}")
            print("   HTML newsletter is still available")
    else:
        print("\n[6/6] Skipping PDF generation")

    # Distribution
    if not args.preview and args.send:
        print("\n--- Distribution ---")
        dist_config = newsletter_config["newsletter"]["distribution"]

        if "email" in args.send and dist_config["email"]["enabled"]:
            print("\nSending via Email...")
            email_config = dist_config["email"]
            sender = EmailSender(
                smtp_host=os.getenv("SMTP_HOST", email_config["smtp_host"]),
                smtp_port=int(os.getenv("SMTP_PORT", email_config["smtp_port"])),
                username=os.getenv("SMTP_USERNAME", email_config.get("sender_email", "")),
                password=os.getenv("SMTP_PASSWORD", "")
            )
            with open(html_path, "r") as f:
                html_content = f.read()
            sender.send(
                subject=f"{newsletter_content['title']} - {date_str}",
                html_content=html_content,
                recipients=email_config.get("recipients", []),
                attachment_path=pdf_path
            )

        if "slack" in args.send and dist_config["slack"]["enabled"]:
            print("\nPosting to Slack...")
            slack_config = dist_config["slack"]
            webhook_url = os.getenv("SLACK_WEBHOOK_URL", slack_config.get("webhook_url", ""))
            if webhook_url:
                poster = SlackPoster(webhook_url)
                summary = f"*{newsletter_content['title']}*\n\n{newsletter_content['introduction'][:200]}..."
                poster.post_message(
                    title=newsletter_content["title"],
                    summary=summary,
                    channel=slack_config.get("channel")
                )
            else:
                print("   Slack webhook URL not configured")

    # Summary
    print("\n" + "=" * 50)
    print("Newsletter generation complete!")
    print(f"HTML: {html_path}")
    if pdf_path:
        print(f"PDF:  {pdf_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
