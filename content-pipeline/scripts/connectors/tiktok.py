"""TikTok connector stub."""

from __future__ import annotations

from .base import Connector


class TikTokConnector(Connector):
    platform = "tiktok"
    api_doc_url = (
        "https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content"
    )

    def validate(self, card: dict) -> list[str]:
        errors = super().validate(card)
        if card.get("asset_type") != "video":
            errors.append("tiktok connector requires asset_type='video' for v1")
        return errors

    def _planned_action(self, card: dict) -> str:
        return (
            f"Init TikTok Content Posting API upload for card {card['id']}, "
            "upload video asset, then publish or save as inbox draft"
        )
