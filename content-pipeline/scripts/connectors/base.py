"""Minimal connector base class for content-pipeline publish stubs."""

from __future__ import annotations

from abc import ABC
from pathlib import Path


class Connector(ABC):
    platform: str = ""
    api_doc_url: str = ""

    def __init__(self, project_root: str | Path | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()

    def validate(self, card: dict) -> list[str]:
        errors: list[str] = []

        asset = card.get("asset")
        if not asset:
            errors.append("missing required field: asset")
        elif not isinstance(asset, str):
            errors.append("asset must be a string path")

        caption = card.get("caption")
        if caption is None or (isinstance(caption, str) and not caption.strip()):
            errors.append("missing required field: caption")

        platforms = card.get("platforms")
        if not isinstance(platforms, list):
            errors.append("platforms must be a list")
        elif self.platform not in platforms:
            errors.append(f"platform {self.platform!r} not listed in card.platforms")

        if asset and isinstance(asset, str):
            asset_path = self._resolve_asset(asset)
            if not asset_path.is_file():
                errors.append(f"asset not found on disk: {asset_path}")

        return errors

    def dry_run(self, card: dict) -> dict:
        errors = self.validate(card)
        if errors:
            raise ValueError("; ".join(errors))

        card_id = card["id"]
        asset_path = self._resolve_asset(card["asset"])
        caption = card.get("caption", "")

        return {
            "platform": self.platform,
            "card_id": card_id,
            "planned_action": self._planned_action(card),
            "api_doc_url": self.api_doc_url,
            "asset": str(asset_path),
            "caption_preview": self._caption_preview(caption),
            "metadata": {
                "status_hint": "publish_dry_run_passed",
            },
        }

    def publish(self, card: dict) -> dict:
        errors = self.validate(card)
        if errors:
            raise ValueError("; ".join(errors))

        card_id = card["id"]
        asset_path = self._resolve_asset(card["asset"])

        return {
            "stub": True,
            "message": "Live API not configured",
            "post_id": f"stub-{self.platform}-{card_id}",
            "platform": self.platform,
            "card_id": card_id,
            "asset": str(asset_path),
            "caption_preview": self._caption_preview(card.get("caption", "")),
            "api_doc_url": self.api_doc_url,
            "note": "Live publishing requires platform credentials.",
        }

    def _resolve_asset(self, asset: str) -> Path:
        path = Path(asset)
        if path.is_absolute():
            return path
        return (self.project_root / path).resolve()

    def _caption_preview(self, caption: str, limit: int = 80) -> str:
        text = caption.strip()
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."

    def _planned_action(self, card: dict) -> str:
        return (
            f"Dry-run publish {card.get('asset_type', 'media')} "
            f"for card {card['id']} to {self.platform}"
        )
