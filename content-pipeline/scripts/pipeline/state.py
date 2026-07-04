"""Media card status definitions and transition helpers."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

DRAFT = "draft"
READY_FOR_HUMAN_REVIEW = "ready_for_human_review"
HUMAN_APPROVED = "human_approved"
PUBLISH_DRY_RUN_PASSED = "publish_dry_run_passed"
PUBLISHED = "published"
PUBLISH_FAILED = "publish_failed"
ARCHIVED = "archived"

ALLOWED_STATUSES: tuple[str, ...] = (
    DRAFT,
    READY_FOR_HUMAN_REVIEW,
    HUMAN_APPROVED,
    PUBLISH_DRY_RUN_PASSED,
    PUBLISHED,
    PUBLISH_FAILED,
    ARCHIVED,
)

_APPROVABLE_STATUSES = frozenset({DRAFT, READY_FOR_HUMAN_REVIEW})
_PUBLISHABLE_STATUSES = frozenset({HUMAN_APPROVED, PUBLISH_DRY_RUN_PASSED})


def is_allowed_status(status: str) -> bool:
    """Return True if *status* is a known pipeline status."""
    return status in ALLOWED_STATUSES


def can_approve(status: str) -> bool:
    """Return True if a card in *status* may be marked human-approved."""
    return status in _APPROVABLE_STATUSES


def can_publish(status: str) -> bool:
    """Return True if a card in *status* may be published or dry-run published."""
    return status in _PUBLISHABLE_STATUSES


def validate_status(status: str) -> str | None:
    """Return an error message if *status* is invalid, else None."""
    if not is_allowed_status(status):
        allowed = ", ".join(ALLOWED_STATUSES)
        return f"invalid status {status!r}; allowed: {allowed}"
    return None


def set_status(card: dict, status: str) -> None:
    """Update a card's status in place after validating it."""
    error = validate_status(status)
    if error:
        raise ValueError(error)
    card["status"] = status


def mark_ready_for_human_review(card: dict) -> None:
    """Move a card to ``ready_for_human_review`` if it is still a draft."""
    if card.get("status") == DRAFT:
        set_status(card, READY_FOR_HUMAN_REVIEW)


def mark_human_approved(card: dict, approved_by: str) -> None:
    """Mark a card human-approved with approval metadata."""
    if not can_approve(card.get("status", "")):
        raise ValueError(
            f"cannot approve card in status {card.get('status')!r}; "
            f"expected one of: {sorted(_APPROVABLE_STATUSES)}"
        )
    approval = card.setdefault("approval", {})
    approval["approved"] = True
    approval["approved_by"] = approved_by
    approval["approved_at"] = datetime.now(timezone.utc).isoformat()
    set_status(card, HUMAN_APPROVED)


def mark_publish_dry_run_passed(card: dict, platform: str | None = None) -> None:
    """Record a successful dry run, optionally for one platform."""
    if not can_publish(card.get("status", "")):
        raise ValueError(
            f"cannot dry-run publish from status {card.get('status')!r}"
        )
    if platform:
        card.setdefault("publish_checks", {})[platform] = {
            "dry_run_passed": True,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }
    set_status(card, PUBLISH_DRY_RUN_PASSED)


def mark_published(card: dict, platform: str | None = None) -> None:
    """Record publish success; set global status only when all platforms are done."""
    if not can_publish(card.get("status", "")):
        raise ValueError(
            f"cannot publish from status {card.get('status')!r}"
        )
    if platform:
        published = card.get("published", {})
        platforms = set(card.get("platforms", []))
        published_platforms = {name for name, value in published.items() if isinstance(value, dict) and not value.get("error")}
        if platforms and platforms.issubset(published_platforms):
            set_status(card, PUBLISHED)
        else:
            set_status(card, PUBLISH_DRY_RUN_PASSED)
        return
    set_status(card, PUBLISHED)


def mark_publish_failed(card: dict) -> None:
    """Set status to ``publish_failed`` when coming from a publishable state."""
    if card.get("status") in _PUBLISHABLE_STATUSES:
        set_status(card, PUBLISH_FAILED)


def mark_archived(card: dict) -> None:
    """Set status to ``archived``."""
    set_status(card, ARCHIVED)


def filter_by_status(cards: Iterable[dict], *statuses: str) -> list[dict]:
    """Return cards whose status is in *statuses*."""
    allowed = set(statuses)
    return [card for card in cards if card.get("status") in allowed]
