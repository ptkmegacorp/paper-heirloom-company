"""Shared action logic for the content pipeline CLI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from . import cards, ingest, paths, review, state


class ActionError(Exception):
    """Raised when a pipeline action cannot complete."""


def create_media_card(
    root: Path | str | None,
    campaign: str,
    asset: Path | str,
    card_id: str,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Create a draft media card for an edited/usable asset.

    The asset path is stored relative to the project root. The card JSON is
    written to ``content-pipeline/media/cards/{campaign}/{card_id}.json``.
    """
    root_path = paths.get_root(root)
    asset_path = Path(asset).resolve()

    if not asset_path.is_file():
        raise ActionError(f"asset file not found: {asset_path}")

    asset_relative = paths.relative_to_root(root_path, asset_path)
    card = cards.new_card(card_id, campaign, asset_relative)
    card_file = paths.card_path(root_path, campaign, card_id)

    if card_file.exists() and not dry_run:
        raise ActionError(f"media card already exists: {card_file}")

    if dry_run:
        return card

    cards.save_card(card, card_file)
    return card


def validate_media_cards(
    root: Path | str | None,
    campaign: str,
) -> dict[str, list[str]]:
    """Validate all cards in a campaign. Returns card_id -> errors mapping."""
    root_path = paths.get_root(root)
    results: dict[str, list[str]] = {}

    card_paths = cards.list_campaign_card_paths(root_path, campaign)
    if not card_paths:
        raise ActionError(f"no media cards found for campaign {campaign!r}")

    for card_path in card_paths:
        card = cards.load_card(card_path)
        card_key = card.get("id", card_path.stem)
        errors = cards.validate_card(card, root_path)
        if errors:
            results[card_key] = errors

    return results


def validate_single_card(
    root: Path | str | None,
    card_id: str,
    campaign: str | None = None,
) -> tuple[dict[str, Any], Path, list[str]]:
    """Load and validate one card. Returns (card, path, errors)."""
    found = cards.find_card(root, card_id, campaign)
    if found is None:
        scope = f" in campaign {campaign!r}" if campaign else ""
        raise ActionError(f"media card not found: {card_id!r}{scope}")

    card, card_path = found
    errors = cards.validate_card(card, root)
    return card, card_path, errors


def mark_media_card_approved(
    root: Path | str | None,
    card_id: str,
    approved_by: str,
    *,
    campaign: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Mark a card human-approved after explicit human confirmation."""
    card, card_path, errors = validate_single_card(root, card_id, campaign)
    if errors:
        raise ActionError(f"card {card_id!r} failed validation: {'; '.join(errors)}")

    if not state.can_approve(card.get("status", "")):
        raise ActionError(
            f"cannot approve card {card_id!r} in status {card.get('status')!r}"
        )

    if dry_run:
        preview = dict(card)
        state.mark_human_approved(preview, approved_by)
        return preview

    state.mark_human_approved(card, approved_by)
    cards.save_card(card, card_path)
    return card


def generate_human_review_page(
    root: Path | str | None,
    campaign: str,
    *,
    promote_drafts: bool = True,
    dry_run: bool = False,
    use_local_model: bool = False,
) -> Path:
    """Generate the static human review HTML page for a campaign.

    By default (*promote_drafts=True*), cards still in ``draft`` are moved to
    ``ready_for_human_review`` after the page is written. Set
    *promote_drafts=False* to leave draft statuses unchanged.
    """
    if dry_run:
        return paths.review_index_path(root, campaign)

    return review.generate_review_html(
        root,
        campaign,
        promote_drafts=promote_drafts,
        use_local_model=use_local_model,
    )


def ingest_raw_media_action(
    root: Path | str | None,
    campaign: str,
    source_file: Path | str,
    *,
    dry_run: bool = False,
) -> Path:
    """CLI helper wrapping :func:`ingest.ingest_raw_media`."""
    return ingest.ingest_raw_media(root, campaign, source_file, dry_run=dry_run)


def ensure_publishable(card: dict[str, Any], platform: str | None = None, *, require_platform_dry_run: bool = False) -> None:
    """Raise :class:`ActionError` if the card is not publishable."""
    if not state.can_publish(card.get("status", "")):
        raise ActionError(
            f"card {card.get('id')!r} is not publishable "
            f"(status={card.get('status')!r}); "
            f"expected human_approved or publish_dry_run_passed"
        )
    if require_platform_dry_run and platform:
        check = card.get("publish_checks", {}).get(platform, {})
        if not check.get("dry_run_passed"):
            raise ActionError(
                f"card {card.get('id')!r} has not passed dry-run for platform {platform!r}"
            )


def load_card_for_action(
    root: Path | str | None,
    card_id: str,
    campaign: str | None = None,
) -> tuple[dict[str, Any], Path]:
    """Load a card or raise :class:`ActionError` if missing."""
    found = cards.find_card(root, card_id, campaign)
    if found is None:
        scope = f" in campaign {campaign!r}" if campaign else ""
        raise ActionError(f"media card not found: {card_id!r}{scope}")
    return found
