"""Static HTML Renderer for the Salesforce AAA UVCE Official Digest.

Renders the collected, curated content into a single production-grade
``public/index.html`` file suitable for GitHub Pages hosting. The file is
overwritten on every run so the published site always reflects the latest
edition.
"""

import os
from datetime import datetime
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader


class HTMLRenderer:
    """Renders newsletter content into a static HTML page."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Project root is two levels above this module (src/renderer).
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_dir = os.path.join(project_root, "templates")
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, newsletter_content: dict, output_path: str = None) -> str:
        """Render the newsletter and overwrite ``public/index.html``.

        When ``output_path`` is omitted the site is written to
        ``<project>/public/index.html``; the ``public`` directory is created
        on demand so the GitHub Actions deploy step always has fresh content.
        """
        if output_path is None:
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            output_path = os.path.join(project_root, "public", "index.html")

        now = datetime.now()

        render_data = {
            **newsletter_content,
            "articles": self._flatten_articles(newsletter_content),
            "date": now.strftime("%B %d, %Y"),
            "updated_at": now.strftime("%A, %B %d, %Y at %H:%M UTC"),
            "updated_iso": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "year": now.year,
        }

        template = self.env.get_template("newsletter.html")
        html_content = template.render(**render_data)

        # Ensure the public directory exists for GitHub Pages.
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        # Overwrite the single canonical file.
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    @staticmethod
    def _flatten_articles(newsletter_content: dict) -> List[Dict]:
        """Flatten nested section articles into one flat list for the grid.

        The template renders ``{% for article in articles %}`` so the grid
        needs a single top-level iterable rather than nested sections.
        """
        flat = []
        for section in newsletter_content.get("sections", []) or []:
            section_name = section.get("name", "") if isinstance(section, dict) else ""
            for article in section.get("articles", []) or []:
                item = dict(article)
                item.setdefault("category", section_name)
                flat.append(item)
        return flat