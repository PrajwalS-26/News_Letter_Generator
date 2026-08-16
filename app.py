"""Streamlit Web UI for Newsletter Generator."""

import os
import sys
import yaml
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm.ollama_client import OllamaClient, GroqClient
from src.collector.rss_collector import RSSCollector
from src.processor.content_filter import ContentFilter
from src.processor.newsletter_gen import NewsletterGenerator
from src.renderer.html_renderer import HTMLRenderer
from src.renderer.pdf_renderer import PDFRenderer


def load_config():
    """Load configuration files."""
    config_dir = os.path.join(os.path.dirname(__file__), "config")

    with open(os.path.join(config_dir, "feeds.yaml"), "r") as f:
        feeds_config = yaml.safe_load(f)

    with open(os.path.join(config_dir, "newsletter.yaml"), "r") as f:
        newsletter_config = yaml.safe_load(f)

    return feeds_config, newsletter_config


def main():
    st.set_page_config(
        page_title="Newsletter Generator",
        page_icon="📰",
        layout="wide"
    )

    st.title("📰 Newsletter Generator - Salesforce AAA UVCE")
    st.markdown("Generate weekly newsletters using AI-powered content curation.")

    # Load environment variables
    load_dotenv()

    # Load config
    feeds_config, newsletter_config = load_config()
    llm_config = newsletter_config["newsletter"]["llm"]

    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")

        # Auto-detect backend
        api_key = os.getenv("GROQ_API_KEY", "")

        if api_key:
            st.info("🔑 Groq API key detected - Using cloud (fast)")
            model = st.selectbox("Model", ["llama-3.1-70b-versatile", "llama-3.1-8b-versatile"])
            llm_client = GroqClient(api_key=api_key, model=model)
            st.success("✅ Groq ready")
        else:
            st.info("💡 No API key - Using local Ollama")
            model = st.text_input("Ollama Model", value=llm_config["model"])
            host = st.text_input("Ollama Host", value=llm_config.get("host", "http://localhost:11434"))
            llm_client = OllamaClient(host=host, model=model)
            if llm_client.is_available():
                st.success("✅ Ollama connected")
            else:
                st.error("❌ Ollama not running")

        st.divider()

        # Output options
        generate_pdf = st.checkbox("Generate PDF", value=True)
        days_back = st.slider("Days to look back", 1, 14, 7)

    # Main content
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("📝 Newsletter Configuration")

        org_name = st.text_input(
            "Organization Name",
            value=newsletter_config["newsletter"]["organization"]
        )

        tagline = st.text_input(
            "Tagline",
            value=newsletter_config["newsletter"]["tagline"]
        )

        max_articles = st.slider(
            "Max articles per section",
            min_value=3,
            max_value=10,
            value=newsletter_config["newsletter"].get("max_articles_per_section", 5)
        )

    with col2:
        st.subheader("📊 Feed Sources")

        # Show configured feeds
        total_feeds = sum(len(feeds) for feeds in feeds_config.values())
        st.metric("Total RSS Feeds", total_feeds)

        for category, feeds in feeds_config.items():
            with st.expander(f"{category.title()} ({len(feeds)} feeds)"):
                for feed in feeds:
                    st.write(f"• {feed['name']}")

    # Generate button
    st.divider()

    if st.button("🚀 Generate Newsletter", type="primary", use_container_width=True):
        generate_newsletter(
            llm_client=llm_client,
            feeds_config=feeds_config,
            newsletter_config=newsletter_config,
            org_name=org_name,
            tagline=tagline,
            max_articles=max_articles,
            generate_pdf=generate_pdf,
            days_back=days_back
        )


def generate_newsletter(llm_client, feeds_config, newsletter_config, org_name,
                        tagline, max_articles, generate_pdf, days_back):
    """Generate the newsletter with progress tracking."""

    # Update config with UI values
    newsletter_config["newsletter"]["organization"] = org_name
    newsletter_config["newsletter"]["tagline"] = tagline
    newsletter_config["newsletter"]["max_articles_per_section"] = max_articles

    progress = st.progress(0)
    status = st.empty()

    try:
        # Step 1: Check LLM
        status.text("🔌 Checking LLM connection...")
        progress.progress(10)

        if not llm_client.is_available():
            st.error("❌ Cannot connect to LLM. Check your settings.")
            return

        # Step 2: Collect articles
        status.text("📰 Collecting articles from RSS feeds...")
        progress.progress(20)

        collector = RSSCollector(feeds_config)
        articles = collector.collect_all(days_back=days_back)
        st.info(f"Found {len(articles)} articles")

        if not articles:
            st.warning("No articles found. Check your RSS feed configuration.")
            return

        progress.progress(40)

        # Step 3: Filter content
        status.text("🔍 Filtering and ranking content...")
        content_filter = ContentFilter(max_per_section=max_articles)
        categorized = content_filter.filter_and_rank(articles)

        for cat, arts in categorized.items():
            st.write(f"• {cat}: {len(arts)} articles selected")

        progress.progress(60)

        # Step 4: Generate content
        status.text("🤖 Generating newsletter content with AI...")
        generator = NewsletterGenerator(llm_client, newsletter_config)
        newsletter_content = generator.generate(categorized)

        progress.progress(80)

        # Step 5: Render output
        status.text("📄 Rendering newsletter...")
        output_dir = newsletter_config["newsletter"]["output"]["directory"]
        os.makedirs(output_dir, exist_ok=True)

        date_str = datetime.now().strftime("%Y-%m-%d")

        # HTML
        html_renderer = HTMLRenderer()
        html_path = os.path.join(output_dir, f"newsletter_{date_str}.html")
        html_renderer.render(newsletter_content, html_path)

        # PDF
        pdf_path = None
        if generate_pdf:
            try:
                pdf_renderer = PDFRenderer()
                pdf_path = os.path.join(output_dir, f"newsletter_{date_str}.pdf")
                pdf_renderer.render(html_path, pdf_path)
            except Exception as e:
                st.warning(f"PDF generation failed: {e}")

        progress.progress(100)
        status.text("✅ Newsletter generated successfully!")

        # Show results
        st.success("Newsletter generated!")
        st.balloons()

        st.subheader("📥 Download")

        col1, col2 = st.columns(2)

        with col1:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.download_button(
                label="📄 Download HTML",
                data=html_content,
                file_name=f"newsletter_{date_str}.html",
                mime="text/html",
                use_container_width=True
            )

        with col2:
            if pdf_path and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_content = f.read()
                st.download_button(
                    label="📑 Download PDF",
                    data=pdf_content,
                    file_name=f"newsletter_{date_str}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

        # Preview
        st.subheader("👀 Preview")
        with st.expander("View HTML Preview", expanded=True):
            st.components.v1.html(html_content, height=600, scrolling=True)

    except Exception as e:
        st.error(f"Error: {e}")
        progress.progress(0)
        status.text("")


if __name__ == "__main__":
    main()
