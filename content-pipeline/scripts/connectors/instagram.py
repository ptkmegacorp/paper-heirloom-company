"""Instagram connector stub."""

from __future__ import annotations

from .base import Connector


class InstagramConnector(Connector):
    platform = "instagram"
    api_doc_url = (
        "https://developers.facebook.com/docs/instagram-platform/content-publishing"
    )

    def _planned_action(self, card: dict) -> str:
        asset_type = card.get("asset_type", "media")
        return (
            f"Create Instagram media container via Graph API, upload {asset_type}, "
            f"then publish container for card {card['id']}"
        )
