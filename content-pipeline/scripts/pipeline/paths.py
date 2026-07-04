"""Path resolution for the Paper Heirloom content pipeline."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Mapping

CONTENT_PIPELINE_DIR = "content-pipeline"
MEDIA_DIR = "media"
RAW_UPLOAD_DIR = "raw-upload"
EDITED_USABLE_ASSET_DIR = "edited-usable-asset"
CARDS_DIR = "cards"
REVIEW_DIR = "review"

_root_override: Path | None = None


def set_root_override(path: Path | str | None) -> None:
    """Set a global project-root override (e.g. from ``--root``)."""
    global _root_override
    if path is None:
        _root_override = None
    else:
        _root_override = Path(path).resolve()


def default_root() -> Path:
    """Return the project root inferred from this package location."""
    # pipeline/ -> scripts/ -> content-pipeline/ -> project root
    return Path(__file__).resolve().parents[3]


def get_root(override: Path | str | None = None) -> Path:
    """Resolve the project root, honoring override then global override then default."""
    if override is not None:
        return Path(override).resolve()
    if _root_override is not None:
        return _root_override
    return default_root()


def content_pipeline_dir(root: Path | str | None = None) -> Path:
    """Return ``content-pipeline/`` under the project root."""
    return get_root(root) / CONTENT_PIPELINE_DIR


def media_dir(root: Path | str | None = None) -> Path:
    """Return ``content-pipeline/media/``."""
    return content_pipeline_dir(root) / MEDIA_DIR


def raw_upload_dir(root: Path | str | None = None, campaign: str | None = None) -> Path:
    """Return raw-upload dir, optionally scoped to a campaign."""
    base = media_dir(root) / RAW_UPLOAD_DIR
    return base / campaign if campaign else base


def edited_usable_asset_dir(root: Path | str | None = None, campaign: str | None = None) -> Path:
    """Return edited-usable-asset dir, optionally scoped to a campaign."""
    base = media_dir(root) / EDITED_USABLE_ASSET_DIR
    return base / campaign if campaign else base


def cards_dir(root: Path | str | None = None, campaign: str | None = None) -> Path:
    """Return cards dir, optionally scoped to a campaign."""
    base = media_dir(root) / CARDS_DIR
    return base / campaign if campaign else base


def review_dir(root: Path | str | None = None, campaign: str | None = None) -> Path:
    """Return review dir, optionally scoped to a campaign."""
    base = media_dir(root) / REVIEW_DIR
    return base / campaign if campaign else base


def campaign_dirs(root: Path | str | None, campaign: str) -> Mapping[str, Path]:
    """Return all campaign-scoped media directories."""
    return {
        "raw_upload": raw_upload_dir(root, campaign),
        "edited_usable_asset": edited_usable_asset_dir(root, campaign),
        "cards": cards_dir(root, campaign),
        "review": review_dir(root, campaign),
    }


def card_path(root: Path | str | None, campaign: str, card_id: str) -> Path:
    """Return the filesystem path for a media card JSON file."""
    return cards_dir(root, campaign) / f"{card_id}.json"


def review_index_path(root: Path | str | None, campaign: str) -> Path:
    """Return the path for a campaign's human review HTML page."""
    return review_dir(root, campaign) / "index.html"


def relative_to_root(root: Path | str, path: Path | str) -> str:
    """Return *path* as a forward-slash string relative to *root*."""
    root_path = get_root(root)
    resolved = Path(path).resolve()
    try:
        rel = resolved.relative_to(root_path)
    except ValueError:
        rel = Path(path)
    return rel.as_posix()


def resolve_from_root(root: Path | str | None, relative_path: str) -> Path:
    """Resolve a project-relative path to an absolute path."""
    return get_root(root) / relative_path


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    """Register the standard ``--root`` CLI flag."""
    parser.add_argument(
        "--root",
        metavar="PATH",
        help="Project root directory (default: auto-detected)",
    )


def apply_root_from_args(args: argparse.Namespace) -> Path:
    """Apply ``--root`` from parsed args and return the resolved root."""
    root = get_root(getattr(args, "root", None))
    if getattr(args, "root", None) is not None:
        set_root_override(root)
    return root
