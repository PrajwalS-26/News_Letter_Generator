"""LLM-based content summarization for newsletter."""

from typing import List, Dict
from src.llm.ollama_client import OllamaClient
from src.collector.rss_collector import Article


class Summarizer:
    """Summarizes articles using LLM."""

    def __init__(self, llm_client: OllamaClient):
        self.llm = llm_client

    def summarize_article(self, article: Article) -> str:
        """Summarize a single article."""
        prompt = f"""Summarize the following article in 2-3 sentences for a newsletter.
Keep it concise, informative, and engaging.

Title: {article.title}
Source: {article.source}
Content: {article.summary}

Summary:"""

        try:
            return self.llm.generate(prompt, temperature=0.5, max_tokens=200)
        except Exception:
            return article.summary[:300]

    def generate_section_summary(self, section_name: str, articles: List[Article]) -> str:
        """Generate a summary for a newsletter section."""
        articles_text = "\n".join(
            f"- {a.title}: {a.summary[:150]}" for a in articles[:5]
        )

        prompt = f"""Write a brief 2-3 sentence introduction for a newsletter section called "{section_name}".
The section contains these articles:
{articles_text}

Write an engaging introduction that highlights the key themes:"""

        try:
            return self.llm.generate(prompt, temperature=0.7, max_tokens=150)
        except Exception:
            return f"Latest updates in {section_name}"

    def generate_title(self, articles: List[Article]) -> str:
        """Generate a catchy newsletter title."""
        headlines = "\n".join(f"- {a.title}" for a in articles[:10])

        prompt = f"""Generate a catchy, professional newsletter title for this week's
Salesforce AAA UVCE newsletter. These are the top stories:
{headlines}

Title:"""

        try:
            return self.llm.generate(prompt, temperature=0.8, max_tokens=50)
        except Exception:
            return "Weekly Digest"
