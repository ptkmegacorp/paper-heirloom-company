"""Tiny llama-server integration for optional review HTML assistance."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

DEFAULT_LLAMA_SERVER = "http://127.0.0.1:8080"


def generate_review_intro(campaign: str, cards: list[dict], *, timeout: int = 20) -> str:
    """Ask a local OpenAI-compatible llama-server for a short HTML intro.

    Failure is non-fatal: callers should fall back to deterministic HTML.
    """
    base = os.environ.get("PAPERHEIRLOOM_LLAMA_SERVER", DEFAULT_LLAMA_SERVER).rstrip("/")
    prompt = (
        "Return only a small safe HTML fragment, no scripts, for a human review page intro. "
        f"Campaign: {campaign}. Card count: {len(cards)}. "
        "Mention that media appears above caption text and approval happens outside this page."
    )
    payload = {
        "messages": [
            {"role": "system", "content": "You write concise static HTML fragments only."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 160,
    }
    req = urllib.request.Request(
        f"{base}/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except (OSError, KeyError, IndexError, json.JSONDecodeError, urllib.error.URLError):
        return ""
