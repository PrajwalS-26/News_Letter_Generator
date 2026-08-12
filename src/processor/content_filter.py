"""Content Filter for ranking and filtering articles."""

from typing import List, Dict
from src.collector.rss_collector import Article


# Section order - Salesforce first
SECTION_ORDER = ["salesforce", "ai", "tech"]


class ContentFilter:
    """Filters and ranks articles for the newsletter."""

    def __init__(self, max_per_section: int = 5):
        self.max_per_section = max_per_section

    def filter_and_rank(self, articles: List[Article]) -> Dict[str, List[Article]]:
        """Filter and rank articles by category in defined order."""
        categorized = {}
        for article in articles:
            cat = article.category
            if cat not in categorized:
                categorized[cat] = []
            categorized[cat].append(article)

        # Rank and limit each category, in defined order
        result = {}
        for category in SECTION_ORDER:
            if category in categorized:
                ranked = self._rank_articles(categorized[category])
                result[category] = ranked[:self.max_per_section]

        # Add any remaining categories not in SECTION_ORDER
        for category, cat_articles in categorized.items():
            if category not in result:
                ranked = self._rank_articles(cat_articles)
                result[category] = ranked[:self.max_per_section]

        return result

    def _rank_articles(self, articles: List[Article]) -> List[Article]:
        """Rank articles by relevance (summary length as proxy for quality)."""
        return sorted(
            articles,
            key=lambda a: len(a.summary),
            reverse=True
        )

    def get_top_articles(self, articles: List[Article], limit: int = 10) -> List[Article]:
        """Get top articles across all categories."""
        ranked = self._rank_articles(articles)
        return ranked[:limit]
