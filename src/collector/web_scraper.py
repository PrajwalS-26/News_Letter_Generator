"""Web Scraper for additional newsletter content."""

import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict
from urllib.parse import urljoin, urlparse


class WebScraper:
    """Scrapes web pages for additional content."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })

    def scrape_article(self, url: str) -> Optional[Dict]:
        """Scrape full article content from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = ""
            if soup.title:
                title = soup.title.string or ""
            h1 = soup.find("h1")
            if h1:
                title = h1.get_text(strip=True)

            # Extract main content
            content = self._extract_main_content(soup)

            # Extract image
            image_url = self._extract_hero_image(soup, url)

            return {
                "url": url,
                "title": title,
                "content": content[:2000],  # Limit content length
                "image_url": image_url
            }
        except Exception as e:
            print(f"Warning: Failed to scrape {url}: {e}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main article content."""
        # Try common article containers
        for selector in ["article", '[role="main"]', ".article-content",
                         ".post-content", ".entry-content", "main"]:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True, separator=" ")

        # Fallback to body
        if soup.body:
            # Remove script and style elements
            for element in soup.body(["script", "style", "nav", "footer", "header"]):
                element.decompose()
            return soup.body.get_text(strip=True, separator=" ")[:2000]

        return ""

    def _extract_hero_image(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract hero/featured image."""
        # Check meta og:image
        og_image = soup.find("meta", property="og:image")
        if og_image and og_image.get("content"):
            return urljoin(base_url, og_image["content"])

        # Check first large image in article
        for img in soup.find_all("img"):
            src = img.get("src", "")
            if src:
                width = img.get("width", "")
                if not width or (width.isdigit() and int(width) > 200):
                    return urljoin(base_url, src)

        return None

    def fetch_image(self, url: str, save_path: Optional[str] = None) -> Optional[bytes]:
        """Fetch image from URL."""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "")
            if "image" in content_type:
                return response.content
        except Exception:
            pass
        return None
