"""Salesforce AAA UVCE - Newsletter Publishing Dashboard

Enterprise-grade Streamlit interface for the Newsletter Generator.
Overlays a Liquid Glassmorphism + Bento Grid design system on top of the
existing collection, curation, generation and distribution pipeline.
"""

import os
import sys
import yaml
import streamlit as st
from datetime import datetime
from dotenv import load_dotenv

# Add project root to path so `src.*` imports resolve regardless of CWD.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.llm.ollama_client import OllamaClient, GroqClient
from src.collector.rss_collector import RSSCollector
from src.processor.content_filter import ContentFilter
from src.processor.newsletter_gen import NewsletterGenerator
from src.renderer.html_renderer import HTMLRenderer
from src.distribution.slack_poster import SlackPoster
from src.distribution.email_sender import EmailSender


# --------------------------------------------------------------------------
# Design system
# --------------------------------------------------------------------------

GLASS_CSS = """
<style>
/* ============ Hide streamlit default chrome ============ */
#MainMenu {visibility: hidden;}
header[data-testid="stHeader"] {display: none;}
footer[data-testid="stFooter"] {visibility: hidden;}
[data-testid="stToolbar"] {display: none;}
#stDecoration {display: none;}
[data-testid="stStatusWidget"] {display: none;}

/* ============ App canvas - deep slate gradient ============ */
[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(1100px 620px at 12% -12%, rgba(0,161,224,0.16), transparent 58%),
        radial-gradient(820px 500px at 88% 6%, rgba(0,86,181,0.20), transparent 55%),
        radial-gradient(900px 600px at 50% 110%, rgba(0,45,96,0.28), transparent 60%),
        linear-gradient(160deg, #0A1B33 0%, #071428 48%, #040A16 100%);
    color: #FFFFFF;
}
[data-testid="stAppViewContainer"] .main .block-container {
    padding-top: 2.2rem;
    padding-bottom: 4.5rem;
    max-width: 1400px;
}

/* ============ Sidebar - control center ============ */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(7,20,45,0.96) 0%, rgba(4,13,30,0.98) 100%);
    border-right: 1px solid rgba(255,255,255,0.08);
}
[data-testid="stSidebar"] .block-container {
    padding-top: 0.5rem;
    padding-bottom: 2rem;
}
/* Flush brand header - strip default padding around the logo image */
[data-testid="stSidebar"] [data-testid="stImage"] {
    margin: -1.4rem -1.1rem 0.2rem -1.1rem;
    padding: 1.2rem 1.1rem 1rem 1.1rem;
    background: linear-gradient(135deg, #0176D3 0%, #00A1E0 60%, #7CD4F8 100%);
    border-bottom: 1px solid rgba(255,255,255,0.18);
}
[data-testid="stSidebar"] [data-testid="stImage"] img {
    border-radius: 10px;
    box-shadow: 0 10px 24px -10px rgba(0,0,0,0.6);
}

/* Sidebar section title */
.side-title {
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #7CD4F8;
    margin: 1.4rem 0 0.4rem 0;
}

/* ============ Flat glass inputs in sidebar ============ */
[data-testid="stSidebar"] [data-testid="stSelectbox"] label,
[data-testid="stSidebar"] [data-testid="stSlider"] label,
[data-testid="stSidebar"] [data-testid="stToggle"] label {
    color: #AFC4DC;
    font-size: 0.82rem;
    letter-spacing: 0.02em;
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    color: #FFFFFF;
    backdrop-filter: blur(8px);
}
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover {
    border-color: rgba(0,161,224,0.55);
}
[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stSliderThumbValue"] {
    color: #7CD4F8;
}
[data-testid="stSidebar"] [data-testid="stToggle"] [data-testid="stWidgetLabel"] p {
    color: #E9F1FA;
    font-weight: 550;
}

/* ============ Dashboard primary title - gradient fill ============ */
.dash-title {
    font-size: 2.7rem;
    font-weight: 800;
    letter-spacing: -0.02em;
    line-height: 1.05;
    margin: 0 0 0.15rem 0;
    background: linear-gradient(92deg, #FFFFFF 0%, #8FD8F8 38%, #00A1E0 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
    color: transparent;
}
.dash-subtitle {
    color: #9FB4D2;
    font-size: 0.95rem;
    letter-spacing: 0.01em;
    margin: 0 0 1.6rem 0;
}

/* ============ Bento metric cards - liquid glass ============ */
.metric-card {
    border-radius: 16px;
    padding: 1.45rem 1.6rem;
    height: 100%;
    background: linear-gradient(145deg, rgba(255,255,255,0.10) 0%, rgba(255,255,255,0.03) 100%);
    border: 1px solid rgba(255,255,255,0.14);
    box-shadow:
        0 18px 40px -18px rgba(0,0,0,0.65),
        inset 0 1px 0 rgba(255,255,255,0.10);
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    transition: transform 0.25s ease, box-shadow 0.25s ease, border-color 0.25s ease;
}
.metric-card:hover {
    transform: translateY(-3px);
    border-color: rgba(0,161,224,0.55);
    box-shadow:
        0 26px 50px -20px rgba(0,45,96,0.85),
        inset 0 1px 0 rgba(255,255,255,0.12);
}
.metric-label {
    display: block;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #AFCBE8;
    margin-bottom: 0.55rem;
}
.metric-value {
    display: block;
    font-size: 1.18rem;
    font-weight: 650;
    letter-spacing: 0.01em;
    color: #FFFFFF;
}
.metric-accent { color: #5BC4F5; }
.metric-dim    { color: #8FA6C4; }

/* ============ Primary action - Salesforce Astro Blue ============ */
.st-key-generate-btn button[kind="primary"] {
    background: linear-gradient(135deg, #00A1E0 0%, #0176D3 100%);
    border: 1px solid rgba(255,255,255,0.22);
    border-radius: 12px;
    color: #FFFFFF;
    font-weight: 650;
    letter-spacing: 0.02em;
    box-shadow: 0 14px 30px -12px rgba(0,161,224,0.55);
    transition: all 0.22s ease;
}
.st-key-generate-btn button[kind="primary"]:hover {
    transform: translateY(-2px);
    background: linear-gradient(135deg, #0FA9E6 0%, #0288DB 100%);
    box-shadow: 0 22px 42px -14px rgba(0,161,224,0.75);
    border-color: rgba(255,255,255,0.35);
}
.st-key-generate-btn button[kind="primary"]:active {
    transform: translateY(0px);
    box-shadow: 0 8px 18px -8px rgba(0,161,224,0.5);
}

/* ============ Generic Streamlit surface polish ============ */
[data-testid="stVerticalBlockBorderWrapper"],
div[data-testid="stExpander"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 14px;
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}
.stAlert {
    border-radius: 12px;
}
</style>
"""


# --------------------------------------------------------------------------
# Configuration helpers
# --------------------------------------------------------------------------

def load_config():
    """Load the RSS feed and newsletter YAML configuration files."""
    config_dir = os.path.join(os.path.dirname(__file__), "config")

    with open(os.path.join(config_dir, "feeds.yaml"), "r") as f:
        feeds_config = yaml.safe_load(f)

    with open(os.path.join(config_dir, "newsletter.yaml"), "r") as f:
        newsletter_config = yaml.safe_load(f)

    return feeds_config, newsletter_config


def create_llm_client(llm_config):
    """Instantiate the appropriate LLM client and describe the active engine.

    Groq (cloud) is preferred when a GROQ_API_KEY is present, otherwise the
    app falls back to a local Ollama instance.
    """
    api_key = os.getenv("GROQ_API_KEY", "")

    if api_key:
        model = st.session_state.get("cfg_model", "llama-3.1-70b-versatile")
        client = GroqClient(api_key=api_key, model=model)
        client_kind = "Groq 70B"
        client_meta = f"groq · {model}"
    else:
        model = llm_config.get("model", "llama3.1:8b")
        host = llm_config.get("host", "http://localhost:11434")
        client = OllamaClient(host=host, model=model)
        client_kind = "Ollama Local"
        client_meta = f"ollama · {model}"

    return client, client_kind, client_meta


# --------------------------------------------------------------------------
# UI builders
# --------------------------------------------------------------------------

def inject_design_system():
    """Inject the global design system, glass tokens and targeted key CSS."""
    st.markdown(GLASS_CSS, unsafe_allow_html=True)


def render_sidebar(llm_config):
    """Build the sidebar Control Center and return the collected controls."""
    with st.sidebar:
        # Brand header - sits flush at the very top of the sidebar.
        st.image(
            "WhatsApp Image 2026-08-10 at 8.30.12 PM_2.jpeg",
            use_container_width=True,
        )

        # Control section title.
        st.markdown('<div class="side-title">Configuration</div>', unsafe_allow_html=True)

        # ---- Editorial controls ----
        audience = st.selectbox(
            "Target Audience",
            options=[
                "General Membership",
                "Salesforce Enthusiasts",
                "AI & ML Community",
                "New Graduates & Aspirants",
                "Alumni & Industry Practitioners",
            ],
            key="audience_sel",
            help="The readership this edition is curated for.",
        )

        tone = st.selectbox(
            "Tone",
            options=[
                "Professional",
                "Friendly",
                "Motivational",
                "Insightful",
                "Concise",
            ],
            key="tone_sel",
            help="The editorial voice carried through the edition.",
        )

        article_count = st.slider(
            "Article Count",
            min_value=3,
            max_value=12,
            value=6,
            step=1,
            key="article_count",
            help="Maximum articles curated per section.",
        )

        st.markdown('<div class="side-title">Distribution</div>', unsafe_allow_html=True)

        # ---- Distribution switches ----
        send_slack = st.toggle(
            "Send to Slack",
            value=False,
            key="toggle_slack",
            help="Post the published PDF to the configured Slack channel.",
        )
        send_email = st.toggle(
            "Send via Email",
            value=False,
            key="toggle_email",
            help="Deliver the edition to the configured recipients.",
        )

    return {
        "audience": audience,
        "tone": tone,
        "article_count": article_count,
        "send_slack": send_slack,
        "send_email": send_email,
    }


def render_dashboard_header():
    """Render the gradient H1 title and the editor-style subtitle."""
    st.markdown(
        '<div class="dash-title">Publishing Dashboard</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="dash-subtitle">Curate, compose and publish the weekly edition for the Salesforce AAA UVCE community.</div>',
        unsafe_allow_html=True,
    )


def render_bento(client_kind, client_meta):
    """Render the three-column Bento Grid with glass metric cards."""
    col_engine, col_status, col_format = st.columns(3)

    with col_engine:
        st.markdown(
            f"""
            <div class="metric-card">
                <span class="metric-label">Engine</span>
                <span class="metric-value metric-accent">{client_kind}</span>
                <span class="metric-value metric-dim" style="font-size:0.8rem;">{client_meta}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_status:
        st.markdown(
            """
            <div class="metric-card">
                <span class="metric-label">Status</span>
                <span class="metric-value metric-accent">System: Standby</span>
                <span class="metric-value metric-dim" style="font-size:0.8rem;">Ready to synthesize</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_format:
        st.markdown(
            """
            <div class="metric-card">
                <span class="metric-label">Edition</span>
                <span class="metric-value metric-accent">Format: HTML + PDF</span>
                <span class="metric-value metric-dim" style="font-size:0.8rem;">Responsive + printable</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("")


# --------------------------------------------------------------------------
# Distribution helpers
# --------------------------------------------------------------------------

def distribute_via_slack(html_path, title):
    """Post the published edition to Slack when a webhook is configured."""
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        st.warning("Slack delivery skipped: SLACK_WEBHOOK_URL not configured.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        text = " ".join(f.read().split())[:200]

    poster = SlackPoster(webhook_url)
    ok = poster.post_message(
        title=title,
        summary=f"*{title}*\n\n{text}...",
        channel=os.getenv("SLACK_CHANNEL", "#newsletter") or None,
    )
    st.success("Edition published to Slack.") if ok else st.error("Slack delivery failed.")


def distribute_via_email(html_path):
    """Deliver the edition via email when SMTP credentials are available."""
    smtp_host = os.getenv("SMTP_HOST", "")
    username = os.getenv("SMTP_USERNAME", "")
    password = os.getenv("SMTP_PASSWORD", "")
    recipients = [r.strip() for r in os.getenv("SMTP_RECIPIENTS", "").split(",") if r.strip()]

    if not (smtp_host and username and password and recipients):
        st.warning("Email delivery skipped: SMTP credentials are incomplete.")
        return

    with open(html_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    sender = EmailSender(smtp_host, int(os.getenv("SMTP_PORT", 587)), username, password)
    subject = f"Salesforce AAA UVCE Newsletter - {datetime.now().strftime('%B %d, %Y')}"
    ok = sender.send(subject, html_content, recipients)
    st.success("Edition delivered by email.") if ok else st.error("Email delivery failed.")


# --------------------------------------------------------------------------
# Core pipeline
# --------------------------------------------------------------------------

def run_pipeline(client, feeds_config, newsletter_config, controls):
    """Collect, curate, compose and publish the newsletter.

    The whole execution path is wrapped in a professional spinner and relies
    on the same RSS -> filter -> LLM -> render pipeline used by generate.py.
    """
    with st.spinner("Synthesizing current edition..."):
        try:
            # ---- Verify engine connectivity ----
            if not client.is_available():
                st.error("Composer engine unreachable. Verify the LLM backend settings.")
                return

            # ---- Editorial context injected into the config ----
            newsletter = newsletter_config["newsletter"]
            newsletter["tone"] = controls["tone"]
            newsletter["audience"] = controls["audience"]
            newsletter["max_articles_per_section"] = controls["article_count"]

            # ---- 1. Collect from configured RSS sources ----
            collector = RSSCollector(feeds_config)
            articles = collector.collect_all(days_back=7)

            if not articles:
                st.warning("No fresh articles found. Check the RSS feed configuration.")
                return
            st.success(f"Curated {len(articles)} candidate stories from the feeds.")

            # ---- 2. Filter and rank by category ----
            content_filter = ContentFilter(max_per_section=controls["article_count"])
            categorized = content_filter.filter_and_rank(articles)
            st.caption("  |  ".join(f"{cat.capitalize()}: {len(arts)}" for cat, arts in categorized.items()))

            # ---- 3. Compose the edition with the LLM ----
            generator = NewsletterGenerator(client, newsletter_config)
            edition = generator.generate(categorized)

            # ---- 4. Render the static site ----
            html_renderer = HTMLRenderer()
            html_path = html_renderer.render(newsletter_content)

            st.markdown("")
            st.success("Edition synthesized and rendered successfully.")

            # ---- 5. Distribution ----
            if controls["send_slack"]:
                distribute_via_slack(html_path, edition.get("title", "Newsletter"))
            if controls["send_email"]:
                distribute_via_email(html_path)

            # ---- 6. Delivery artifacts ----
            st.markdown(
                '<div class="side-title" style="margin-top:1.6rem;">Delivery</div>',
                unsafe_allow_html=True,
            )

            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.download_button(
                "Download HTML",
                data=html_content,
                file_name="index.html",
                mime="text/html",
                use_container_width=True,
            )

            # ---- 7. Inline proof ----
            with st.expander("Preview Edition", expanded=True):
                st.components.v1.html(html_content, height=620, scrolling=True)

        except Exception as exc:
            st.error(f"Pipeline error: {exc}")


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def main():
    """Boot the dashboard: global design, sidebar controls and bento stage."""
    st.set_page_config(
        page_title="Salesforce AAA UVCE",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    inject_design_system()

    load_dotenv()
    feeds_config, newsletter_config = load_config()
    llm_config = newsletter_config["newsletter"]["llm"]

    # Sidebar control center.
    controls = render_sidebar(llm_config)

    # Resolve the active engine once so the bento cards are accurate.
    client, client_kind, client_meta = create_llm_client(llm_config)

    # Main stage.
    render_dashboard_header()
    render_bento(client_kind, client_meta)

    # Primary action.
    st.markdown("")
    if st.button("Generate Newsletter", key="generate_btn", type="primary"):
        run_pipeline(client, feeds_config, newsletter_config, controls)


if __name__ == "__main__":
    main()