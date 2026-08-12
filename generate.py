#!/usr/bin/env python3
"""Static Site Generator for the Salesforce AAA UVCE Official Digest.

Fetches RSS feeds, summarizes the top stories with the Groq (or local
Ollama) LLM, and renders a single production-grade page at
``public/index.html`` for GitHub Pages.

Designed to run headlessly on a cron schedule (e.g. every Monday via
GitHub Actions), so it never blocks on interactive prompts.

Usage:
    python generate.py                          # Build public/index.html
    python generate.py --preview                # Build without sending
    python generate.py --send email slack       # Build and distribute
    python generate.py --model llama-3.1-8b-instruction-following   # custom model
    python generate.py --date 2026-08-10        # Override edition date
"""

import os
import sys
import yaml
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path so `src.*` imports resolve regardless of CWD.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

from src.llm.ollama_client import OllamaClient, GroqClient
from src.collector.rss_collector import RSSCollector
from src.processor.content_filter import ContentFilter
from src.processor.newsletter_gen import NewsletterGenerator
from src.renderer.html_renderer import HTMLRenderer
from src.distribution.slack_poster import SlackPoster
from src.distribution.email_sender import EmailSender

OUTPUT_FILE = os.path.join(PROJECT_ROOT, "public", "index.html")


def load_config():
    """Load the RSS feed and newsletter YAML configuration files."""
    config_dir = os.path.join(PROJECT_ROOT, "config")

    with open(os.path.join(config_dir, "feeds.yaml"), "r", encoding="utf-8") as f:
        feeds_config = yaml.safe_load(f)

    with open(os.path.join(config_dir, "newsletter.yaml"), "r", encoding="utf-8") as f:
        newsletter_config = yaml.safe_load(f)

    return feeds_config, newsletter_config


def build_llm_client(llm_config: dict):
    """Prefer Groq when a key is present, otherwise fall back to Ollama."""
    api_key = os.getenv("GROQ_API_KEY", "")

    if api_key:
        print("   Engine: Groq cloud API")
        return GroqClient(
            api_key=api_key,
            model=llm_config.get("model", "openai/gpt-oss-120b")
        )
    else:
        raise RuntimeError("GROQ_API_KEY not set.")

def distribute(args, newsletter_content: dict, dist_config: dict, html_path: str, date_str: str):
    """Send the edition to the configured channels. No attachments: the site
    is static HTML, so channels receive a message linking back to it."""
    if not dist_config:
        return

    # --- Email ---
    email_config = dist_config.get("email", {})
    if "email" in args.send and email_config.get("enabled"):
        print("\nDelivering via Email...")
        try:
            sender = EmailSender(
                smtp_host=os.getenv("SMTP_HOST", email_config.get("smtp_host", "")),
                smtp_port=int(os.getenv("SMTP_PORT", email_config.get("smtp_port", 587))),
                username=os.getenv("SMTP_USERNAME", email_config.get("sender_email", "")),
                password=os.getenv("SMTP_PASSWORD", ""),
            )
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            sender.send(
                subject=f"{newsletter_content['title']} - {date_str}",
                html_content=html_content,
                recipients=email_config.get("recipients", []),
            )
        except Exception as e:
            print(f"   Email failed: {e}")

    # --- Slack ---
    slack_config = dist_config.get("slack", {})
    if "slack" in args.send and slack_config.get("enabled"):
        print("\nPosting to Slack...")
        webhook_url = os.getenv("SLACK_WEBHOOK_URL", slack_config.get("webhook_url", ""))
        if webhook_url:
            poster = SlackPoster(webhook_url)
            summary = f"*{newsletter_content['title']}*\n\n{newsletter_content['introduction'][:200]}..."
            poster.post_message(
                title=newsletter_content["title"],
                summary=summary,
                channel=slack_config.get("channel"),
            )
        else:
            print("   Slack webhook URL not configured")


def run_cli(argv=None) -> int:
    """Parse arguments and execute the static site generation pipeline."""
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=__doc__,
    )
    parser.add_argument("--date", type=str, help="Edition date (YYYY-MM-DD)")
    parser.add_argument("--preview", action="store_true", help="Build without sending")
    parser.add_argument("--send", nargs="+", choices=["email", "slack"], help="Send to specific channels")
    parser.add_argument("--model", type=str, help="LLM model to use")
    args = parser.parse_args(argv)

    # Seed environment from .env once available.
    load_dotenv()

    # Load config.
    feeds_config, newsletter_config = load_config()
    newsletter = newsletter_config["newsletter"]
    llm_config = newsletter["llm"]

    # Optional model override.
    if args.model:
        llm_config["model"] = args.model

    print("=" * 60)
    print("Salesforce AAA UVCE - Official Digest (Static Site Generator)")
    print("=" * 60)

    # 1. Initialize the engine.
    print("\n[1/6] Initializing composer engine...")
    client = build_llm_client(llm_config)
    if not client.is_available():
        print("   ERROR: Composer engine is unreachable.")
        print("   Provide GROQ_API_KEY or ensure Ollama is running.")
        return 1

    # 2. Collect articles.
    print("\n[2/6] Collecting articles from RSS feeds...")
    collector = RSSCollector(feeds_config)
    articles = collector.collect_all(days_back=7)
    print(f"   Found {len(articles)} candidate stories")

    if not articles:
        print("   ERROR: No articles found. Check the RSS feed configuration.")
        return 1

    # 3. Filter and rank.
    print("\n[3/6] Filtering and ranking content...")
    content_filter = ContentFilter(
        max_per_section=newsletter.get("max_articles_per_section", 5)
    )
    categorized = content_filter.filter_and_rank(articles)
    for cat, arts in categorized.items():
        print(f"   {cat}: {len(arts)} articles")

    # 4. Compose with the LLM.
    print("\n[4/6] Composing edition with the LLM...")
    generator = NewsletterGenerator(client, newsletter_config)
    newsletter_content = generator.generate(categorized)
    print(f"   Title: {newsletter_content['title']}")

    # 5. Render the static site.
    print("\n[5/6] Rendering static site...")
    html_renderer = HTMLRenderer()
    html_path = html_renderer.render(newsletter_content)
    print(f"   Published: {html_path}")

    # 6. Distribute.
    print("\n[6/6] Distribution...")
    date_str = args.date or datetime.now().strftime("%Y-%m-%d")
    if args.preview:
        print("   Preview mode - skipping distribution")
    elif args.send:
        distribute(args, newsletter_content, newsletter.get("distribution"), html_path, date_str)
    else:
        print("   No channels requested - use --send email slack to distribute")

    print("\n" + "=" * 60)
    print(f"Site published to {html_path}")
    print("=" * 60)
    return 0


def main(argv=None):
    sys.exit(run_cli(argv))


if __name__ == "__main__":
    main()