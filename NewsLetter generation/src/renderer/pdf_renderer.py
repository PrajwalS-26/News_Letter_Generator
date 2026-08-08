"""PDF Renderer for newsletter generation using xhtml2pdf."""

import os
import requests
from xhtml2pdf import pisa
from io import BytesIO


class PDFRenderer:
    """Renders newsletter content to PDF with image support."""

    def render(self, html_path: str, output_path: str) -> str:
        """Convert HTML newsletter to PDF."""
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        # Read HTML file
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        # Convert HTML to PDF
        with open(output_path, "wb") as output_file:
            pisa_status = pisa.CreatePDF(
                html_content,
                dest=output_file,
                encoding='utf-8'
            )

        if pisa_status.err:
            print(f"PDF warning: {pisa_status.err} non-critical errors")

        return output_path

    def _download_image(self, url: str) -> str:
        """Download image and return local path or empty string."""
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                if 'image' in content_type:
                    # Save to temp file
                    import tempfile
                    suffix = '.jpg' if 'jpeg' in content_type or 'jpg' in content_type else '.png'
                    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                        tmp.write(response.content)
                        return tmp.name
        except Exception:
            pass
        return ""
