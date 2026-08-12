"""Newsletter content generator using LLM."""

from typing import List, Dict
from src.llm.ollama_client import OllamaClient
from src.collector.rss_collector import Article
from src.processor.summarizer import Summarizer


class NewsletterGenerator:
    """Generates newsletter content using LLM."""

    def __init__(self, llm_client: OllamaClient, config: dict):
        self.llm = llm_client
        self.config = config
        self.summarizer = Summarizer(llm_client)

    def generate(self, categorized_articles: Dict[str, List[Article]]) -> Dict:
        """Generate complete newsletter content."""
        newsletter_config = self.config.get("newsletter", {})

        # Get all articles flat
        all_articles = []
        for articles in categorized_articles.values():
            all_articles.extend(articles)

        # Generate title
        title = self.summarizer.generate_title(all_articles)

        # Generate introduction
        intro = self._generate_introduction(all_articles)

        # Generate sections
        sections = []
        category_names = {
            "salesforce": "Salesforce Updates",
            "ai": "AI & Machine Learning",
            "tech": "Tech Industry News"
        }

        for category, articles in categorized_articles.items():
            if articles:
                section_name = category_names.get(category, category.title())
                section = self._generate_section(
                    section_name,
                    articles
                )
                sections.append(section)

        # Generate conclusion
        conclusion = self._generate_conclusion(all_articles)

        return {
            "title": title.strip() if title else newsletter_config.get("name", "Weekly Digest"),
            "tagline": newsletter_config.get("tagline", "Your weekly dose of updates"),
            "organization": newsletter_config.get("organization", "Salesforce AAA UVCE"),
            "introduction": intro.strip(),
            "sections": sections,
            "conclusion": conclusion.strip()
        }

    def _generate_introduction(self, articles: List[Article]) -> str:
        """Generate newsletter introduction."""
        headlines = "\n".join(f"- {a.title}" for a in articles[:8])

        prompt = f"""Write a warm, engaging introduction (3-4 sentences) for the Salesforce AAA UVCE weekly newsletter.
This week's top stories include:
{headlines}

Make it professional but friendly. Mention key themes:"""

        try:
            return self.llm.generate(prompt, temperature=0.7, max_tokens=200)
        except Exception:
            return "Welcome to this week's newsletter! Here are the latest updates from Salesforce and the AI world."

    def _generate_section(self, section_name: str, articles: List[Article]) -> Dict:
        """Generate a newsletter section."""
        # Summarize articles
        summarized = []
        for article in articles[:5]:
            summary = self.summarizer.summarize_article(article)
            summarized.append({
                "title": article.title,
                "link": article.link,
                "summary": summary.strip() if summary else article.summary[:200],
                "source": article.source,
                "image_url": article.image_url
            })

        # Generate section intro
        intro = self.summarizer.generate_section_summary(section_name, articles)

        return {
            "name": section_name,
            "introduction": intro.strip() if intro else f"Latest updates in {section_name}",
            "articles": summarized
        }

    def _generate_conclusion(self, articles: List[Article]) -> str:
        """Generate newsletter conclusion."""
        prompt = f"""Write a brief conclusion (2-3 sentences) for the Salesforce AAA UVCE weekly newsletter.
End with a call to action encouraging readers to stay connected and share feedback.
Make it warm and professional:"""

        try:
            return self.llm.generate(prompt, temperature=0.7, max_tokens=150)
        except Exception:
            return "Thanks for reading! Stay connected with Salesforce AAA UVCE for more updates."
