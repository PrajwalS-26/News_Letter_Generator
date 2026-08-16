"""Slack Poster for newsletter distribution."""

import json
import requests
from typing import Optional


class SlackPoster:
    """Posts newsletter to Slack."""

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

    def post_file(self, file_path: str, title: str, initial_comment: str = "",
                  channel: Optional[str] = None) -> bool:
        """Post newsletter file to Slack."""
        try:
            with open(file_path, "rb") as f:
                files = {"file": (title, f, "application/pdf")}
                data = {
                    "title": title,
                    "initial_comment": initial_comment
                }
                if channel:
                    data["channels"] = channel

                response = requests.post(
                    "https://slack.com/api/files.upload",
                    data=data,
                    files=files,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()

                if result.get("ok"):
                    print("File posted to Slack successfully")
                    return True
                else:
                    print(f"Slack API error: {result.get('error')}")
                    return False

        except Exception as e:
            print(f"Failed to post file to Slack: {e}")
            return False
