"""Ingest raw media into the content pipeline."""

from __future__ import annotations

import shutil
from pathlib import Path

from . import paths


def ingest_raw_media(
    root: Path | str | None,
    campaign: str,
    source_file: Path | str,
    *,
    dry_run: bool = False,
) -> Path:
    """Copy *source_file* into ``raw-upload/{campaign}/`` preserving the filename.

    Returns the destination path. Creates campaign directory as needed.
    Raises ``FileNotFoundError`` if the source does not exist.
    Raises ``FileExistsError`` if the destination already exists (unless dry_run).
    """
    source = Path(source_file).resolve()
    if not source.is_file():
        raise FileNotFoundError(f"source file not found: {source}")

    dest_dir = paths.raw_upload_dir(root, campaign)
    dest = dest_dir / source.name

    if dest.exists() and not dry_run:
        raise FileExistsError(f"destination already exists: {dest}")

    if dry_run:
        return dest

    dest_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)
    return dest
