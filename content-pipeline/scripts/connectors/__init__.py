"""Platform connector registry for the content pipeline."""

from __future__ import annotations

from pathlib import Path

from .base import Connector
from .facebook import FacebookConnector
from .instagram import InstagramConnector
from .tiktok import TikTokConnector

CONNECTORS: dict[str, type[Connector]] = {
    "instagram": InstagramConnector,
    "facebook": FacebookConnector,
    "tiktok": TikTokConnector,
}


def get_connector(platform: str, project_root: str | Path | None = None) -> Connector:
    cls = CONNECTORS.get(platform)
    if cls is None:
        available = ", ".join(sorted(CONNECTORS))
        raise ValueError(f"Unknown platform: {platform!r}. Available: {available}")
    return cls(project_root=project_root)


__all__ = [
    "CONNECTORS",
    "Connector",
    "FacebookConnector",
    "InstagramConnector",
    "TikTokConnector",
    "get_connector",
]
