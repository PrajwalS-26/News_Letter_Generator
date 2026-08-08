"""HTML Renderer for newsletter generation."""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader


class HTMLRenderer:
    """Renders newsletter content to HTML."""

    def __init__(self, template_dir: str = None):
        if template_dir is None:
            # Go up from src/renderer to project root, then into templates
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            template_dir = os.path.join(project_root, "templates")
        self.template_dir = template_dir
        self.env = Environment(loader=FileSystemLoader(template_dir))

    def render(self, newsletter_content: dict, output_path: str) -> str:
        """Render newsletter to HTML file."""
        template = self.env.get_template("newsletter.html")

        # Add date and year
        now = datetime.now()
        render_data = {
            **newsletter_content,
            "date": now.strftime("%B %d, %Y"),
            "year": now.year
        }

        html_content = template.render(**render_data)

        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        # Write HTML file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
