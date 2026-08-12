"""Email Sender for newsletter distribution."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List


class EmailSender:
    """Sends the newsletter HTML via email."""

    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password

    def send(self, subject: str, html_content: str, recipients: List[str]) -> bool:
        """Send newsletter email with inline HTML content."""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.username
            msg["To"] = ", ".join(recipients)

            # Attach HTML content
            html_part = MIMEText(html_content, "html")
            msg.attach(html_part)

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