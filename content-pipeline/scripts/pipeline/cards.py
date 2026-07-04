"""Load, save, and validate media card JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

from . import paths, state

ALLOWED_PLATFORMS = frozenset({"instagram", "facebook", "tiktok"})

IMAGE_EXTENSIONS = frozenset({".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".tif", ".tiff"})
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v", ".mpeg", ".mpg"})

REQUIRED_FIELDS = (
    "id",
    "campaign",
    "status",
    "asset",
    "asset_type",
    "format",
    "caption",
    "cta_url",
    "platforms",
    "approval",
    "published",
)

REQUIRED_APPROVAL_FIELDS = ("approved", "approved_by", "approved_at")

DEFAULT_CTA_URL = "https://paperheirloomcompany.etsy.com"
DEFAULT_CAPTION = "Caption pending review."
DEFAULT_PLATFORMS = ["instagram", "facebook", "tiktok"]


def detect_asset_type(path: Path | str) -> str:
    """Return ``image`` or ``video`` based on file extension."""
    suffix = Path(path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return "image"
    if suffix in VIDEO_EXTENSIONS:
        return "video"
    raise ValueError(f"cannot detect asset_type from extension {suffix!r}")


def default_format_for_asset_type(asset_type: str) -> str:
    """Return a sensible default format value for *asset_type*."""
    if asset_type == "video":
        return "vertical_video"
    return "image"


def new_card(
    card_id: str,
    campaign: str,
    asset_relative_path: str,
    *,
    asset_type: str | None = None,
    format_value: str | None = None,
    caption: str = DEFAULT_CAPTION,
    cta_url: str = DEFAULT_CTA_URL,
    platforms: list[str] | None = None,
) -> dict[str, Any]:
    """Build a new media card dict with draft status and defaults."""
    resolved_asset_type = asset_type or detect_asset_type(asset_relative_path)
    return {
        "id": card_id,
        "campaign": campaign,
        "status": state.DRAFT,
        "asset": asset_relative_path,
        "asset_type": resolved_asset_type,
        "format": format_value or default_format_for_asset_type(resolved_asset_type),
        "caption": caption,
        "cta_url": cta_url,
        "platforms": list(platforms if platforms is not None else DEFAULT_PLATFORMS),
        "approval": {
            "approved": False,
            "approved_by": None,
            "approved_at": None,
        },
        "published": {},
    }


def load_card(path: Path | str) -> dict[str, Any]:
    """Load a media card JSON file."""
    card_path = Path(path)
    with card_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_card(card: dict[str, Any], path: Path | str) -> Path:
    """Write a media card JSON file, creating parent dirs as needed."""
    card_path = Path(path)
    card_path.parent.mkdir(parents=True, exist_ok=True)
    with card_path.open("w", encoding="utf-8") as handle:
        json.dump(card, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return card_path


def validate_platform_names(platforms: Iterable[str]) -> list[str]:
    """Return validation errors for platform names."""
    errors: list[str] = []
    if not platforms:
        errors.append("platforms must be a non-empty list")
        return errors
    for platform in platforms:
        if platform not in ALLOWED_PLATFORMS:
            allowed = ", ".join(sorted(ALLOWED_PLATFORMS))
            errors.append(f"invalid platform {platform!r}; allowed: {allowed}")
    return errors


def validate_schema(card: dict[str, Any]) -> list[str]:
    """Return schema validation errors for a media card dict."""
    errors: list[str] = []

    for field in REQUIRED_FIELDS:
        if field not in card:
            errors.append(f"missing required field: {field}")

    if "status" in card:
        status_error = state.validate_status(card["status"])
        if status_error:
            errors.append(status_error)

    if "platforms" in card:
        if not isinstance(card["platforms"], list):
            errors.append("platforms must be a list")
        else:
            errors.extend(validate_platform_names(card["platforms"]))

    if "approval" in card:
        if not isinstance(card["approval"], dict):
            errors.append("approval must be an object")
        else:
            for field in REQUIRED_APPROVAL_FIELDS:
                if field not in card["approval"]:
                    errors.append(f"missing required approval field: {field}")

    if "published" in card and not isinstance(card["published"], dict):
        errors.append("published must be an object")

    if "asset_type" in card and card["asset_type"] not in {"image", "video"}:
        errors.append(f"invalid asset_type {card['asset_type']!r}; expected image or video")

    return errors


def validate_card(card: dict[str, Any], root: Path | str | None = None) -> list[str]:
    """Validate schema, asset existence, status, and platforms."""
    errors = validate_schema(card)
    if errors:
        return errors

    asset_path = paths.resolve_from_root(root, card["asset"])
    if not asset_path.is_file():
        errors.append(f"asset file not found: {card['asset']}")

    try:
        detected = detect_asset_type(asset_path)
        if detected != card["asset_type"]:
            errors.append(
                f"asset_type {card['asset_type']!r} does not match file extension "
                f"(expected {detected!r})"
            )
    except ValueError as exc:
        errors.append(str(exc))

    return errors


def list_campaign_card_paths(root: Path | str | None, campaign: str) -> list[Path]:
    """Return sorted JSON paths for all cards in a campaign."""
    campaign_path = paths.cards_dir(root, campaign)
    if not campaign_path.is_dir():
        return []
    return sorted(campaign_path.glob("*.json"))


def list_all_card_paths(root: Path | str | None) -> list[Path]:
    """Return sorted JSON paths for all cards across campaigns."""
    cards_root = paths.cards_dir(root)
    if not cards_root.is_dir():
        return []
    return sorted(cards_root.glob("*/*.json"))


def load_campaign_cards(root: Path | str | None, campaign: str) -> list[dict[str, Any]]:
    """Load all cards for a campaign."""
    return [load_card(path) for path in list_campaign_card_paths(root, campaign)]


def find_card_path(
    root: Path | str | None,
    card_id: str,
    campaign: str | None = None,
) -> Path | None:
    """Find a card JSON path by id, optionally within a single campaign."""
    if campaign is not None:
        candidate = paths.card_path(root, campaign, card_id)
        return candidate if candidate.is_file() else None

    for path in list_all_card_paths(root):
        if path.stem == card_id:
            return path
    return None


def find_card(
    root: Path | str | None,
    card_id: str,
    campaign: str | None = None,
) -> tuple[dict[str, Any], Path] | None:
    """Find and load a card by id. Returns (card, path) or None."""
    card_file = find_card_path(root, card_id, campaign)
    if card_file is None:
        return None
    return load_card(card_file), card_file
