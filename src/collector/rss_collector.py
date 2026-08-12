"""RSS Feed Collector for gathering newsletter content."""

import feedparser
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bs4 import BeautifulSoup


class Article:
    """Represents a collected article."""

    def __init__(self, title: str, link: str, summary: str, published: datetime,
                 source: str, category: str, image_url: Optional[str] = None):
        self.title = title
        self.link = link
        self.summary = summary
        self.published = published
        self.source = source
        self.category = category
        self.image_url = image_url

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "link": self.link,
            "summary": self.summary,
            "published": self.published.isoformat(),
            "source": self.source,
            "category": self.category,
            "image_url": self.image_url
        }


class RSSCollector:
    """Collects articles from RSS feeds."""

    def __init__(self, feeds_config: dict):
        self.feeds_config = feeds_config
        self.headers = {
            "User-Agent": "Mozilla/5.0 (compatible; NewsletterBot/1.0)"
        }

    def collect_all(self, days_back: int = 7) -> List[Article]:
        """Collect articles from all configured feeds."""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        for category, feeds in self.feeds_config.items():
            for feed_config in feeds:
                try:
                    feed_articles = self._collect_feed(feed_config, category, cutoff_date)
                    articles.extend(feed_articles)
                except Exception as e:
                    print(f"Warning: Failed to collect from {feed_config.get('name')}: {e}")

        # Sort by published date (newest first)
        articles.sort(key=lambda x: x.published, reverse=True)
        return articles

    def _collect_feed(self, feed_config: dict, category: str,
                      cutoff_date: datetime) -> List[Article]:
        """Collect articles from a single RSS feed."""
        url = feed_config.get("url", "")
        name = feed_config.get("name", url)

        feed = feedparser.parse(url, request_headers=self.headers)
        articles = []

        for entry in feed.entries:
            try:
                # Parse published date
                published = self._parse_date(entry)
                if published and published < cutoff_date:
                    continue

                # Extract summary
                summary = self._clean_html(
                    entry.get("summary", entry.get("description", ""))
                )

                # Extract image
                image_url = self._extract_image(entry, feed)

                article = Article(
                    title=entry.get("title", "Untitled"),
                    link=entry.get("link", ""),
                    summary=summary[:500],  # Limit summary length
                    published=published or datetime.now(),
                    source=name,
                    category=category,
                    image_url=image_url
                )
                articles.append(article)
            except Exception as e:
                continue

        return articles

    def _parse_date(self, entry) -> Optional[datetime]:
        """Parse date from feed entry."""
        for date_field in ["published_parsed", "updated_parsed"]:
            time_struct = entry.get(date_field)
            if time_struct:
                try:
                    return datetime(*time_struct[:6])
                except Exception:
                    continue
        return None

    def _clean_html(self, html: str) -> str:
        """Remove HTML tags from text."""
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        return soup.get_text(strip=True)

    def _extract_image(self, entry, feed) -> Optional[str]:
        """Extract image URL from entry with multiple fallback methods."""
        # 1. Check media:content
        if hasattr(entry, "media_content") and entry.media_content:
            for media in entry.media_content:
                if media.get("medium") == "image" or "image" in media.get("type", ""):
                    return media.get("url")

        # 2. Check media:thumbnail
        if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
            return entry.media_thumbnail[0].get("url")

        # 3. Check enclosures
        if hasattr(entry, "enclosures") and entry.enclosures:
            for enc in entry.enclosures:
                if "image" in enc.get("type", ""):
                    return enc.get("href") or enc.get("url")

        # 4. Check content:encoded
        if hasattr(entry, "content") and entry.content:
            for content in entry.content:
                if content.get("type", "").startswith("text"):
                    soup = BeautifulSoup(content.get("value", ""), "html.parser")
                    img = soup.find("img")
                    if img and img.get("src"):
                        return img["src"]

        # 5. Check for image in summary/description
        for field in ["summary", "description"]:
            text = entry.get(field, "")
            if text:
                soup = BeautifulSoup(text, "html.parser")
                img = soup.find("img")
                if img and img.get("src"):
                    src = img["src"]
                    if src.startswith("//"):
                        src = "https:" + src
                    elif src.startswith("/"):
                        link = entry.get("link", "")
                        if link:
                            from urllib.parse import urlparse
                            parsed = urlparse(link)
                            src = f"{parsed.scheme}://{parsed.netloc}{src}"
                    return src

        return None
