"""Slack Poster for newsletter distribution."""

import requests
from typing import Optional


class SlackPoster:
    """Posts the published newsletter to a Slack channel."""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def post_message(self, title: str, summary: str, link: Optional[str] = None,
                     channel: Optional[str] = None) -> bool:
        """Post newsletter summary to Slack."""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": title,
                        "emoji": True
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": summary
                    }
                }
            ]

            if link:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"<{link}|Read the full newsletter>"
                    }
                })

            payload = {
                "blocks": blocks,
                "text": title
            }

            if channel:
                payload["channel"] = channel

            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=30
            )
            response.raise_for_status()

            print("Posted to Slack successfully")
            return True

        except Exception as e:
            print(f"Failed to post to Slack: {e}")
            return False