"""Facebook Page connector stub."""

from __future__ import annotations

from .base import Connector


class FacebookConnector(Connector):
    platform = "facebook"
    api_doc_url = "https://developers.facebook.com/docs/pages-api/posts/"

    def _planned_action(self, card: dict) -> str:
        asset_type = card.get("asset_type", "media")
        if asset_type == "video":
            return (
                f"POST /{{page_id}}/videos with caption for card {card['id']}"
            )
        return (
            f"POST /{{page_id}}/feed or /photos with caption for card {card['id']}"
        )
