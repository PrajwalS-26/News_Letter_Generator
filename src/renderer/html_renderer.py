"""Static HTML Renderer for the Salesforce AAA UVCE Official Digest.

Renders the collected, curated content into a single production-grade
``public/index.html`` file suitable for GitHub Pages hosting. The file is
overwritten on every run so the published site always reflects the latest
edition. Branded assets referenced by the template (e.g. the header logo)
are copied into the public folder so they resolve on the live site.
"""

import os
import shutil
from datetime import datetime
from typing import List, Dict
from jinja2 import Environment, FileSystemLoader

# Local branded assets the template references with a relative path. They are
# copied next to index.html on every build so the deployed site serves them.
LOCAL_ASSETS = [
    "club-logo.jpeg",
]

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))


class HTMLRenderer:
    """Renders newsletter content into a static HTML page."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            template_dir = os.path.join(PROJECT_ROOT, "templates")
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, newsletter_content: dict, output_path: str = None) -> str:
        """Render the newsletter and overwrite ``public/index.html``.

        When ``output_path`` is omitted the site is written to
        ``<project>/public/index.html``; the ``public`` directory is created
        on demand so the GitHub Actions deploy step always has fresh content.
        """
        if output_path is None:
            output_path = os.path.join(PROJECT_ROOT, "public", "index.html")

        output_dir = os.path.dirname(output_path) or "."
        # Ensure the public directory exists for GitHub Pages.
        os.makedirs(output_dir, exist_ok=True)

        # Copy branded assets (e.g. header logo) next to index.html so the
        # deployed site can serve them via relative paths.
        self._copy_local_assets(output_dir)

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

        # Overwrite the single canonical file.
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path

    @staticmethod
    def _copy_local_assets(output_dir: str) -> None:
        """Copy committed brand assets from the repo root into the output dir."""
        for asset in LOCAL_ASSETS:
            src = os.path.join(PROJECT_ROOT, asset)
            if os.path.exists(src):
                try:
                    shutil.copy2(src, os.path.join(output_dir, asset))
                except OSError:
                    pass

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