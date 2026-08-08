"""Email Sender for newsletter distribution."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional


class EmailSender:
    """Sends newsletter via email."""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send(self, subject: str, html_content: str, recipients: List[str],
             attachment_path: Optional[str] = None) -> bool:
        """Send newsletter email."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = ", ".join(recipients)

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

            # Attach PDF if provided
            if attachment_path and os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    pdf_attachment = MIMEBase("application", "pdf")
                    pdf_payload = f.read()
                    pdf_attachment.set_payload(pdf_payload)
                    encoders.encode_base64(pdf_attachment)
                    filename = os.path.basename(attachment_path)
                    pdf_attachment.add_header(
                        "Content-Disposition",
                        f"attachment; filename={filename}"
                    )
                    msg.attach(pdf_attachment)

            # Send email
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.sendmail(self.username, recipients, msg.as_string())

            print(f"Email sent successfully to {len(recipients)} recipients")
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
