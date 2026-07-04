#!/usr/bin/env python3
"""End-to-end test for the Paper Heirloom content pipeline (no live APIs)."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CLI = ROOT / "content-pipeline/scripts/run-paperheirloom-content-pipeline.py"
FIXTURE = ROOT / "docs/assets/pigeon-flannel-logo.png"
CAMPAIGN = "e2e-test-2026-07"
CARD_ID = "e2e-fold-demo-01"


def run(*args: str, expect_ok: bool = True) -> dict:
    cmd = [sys.executable, str(CLI), *args, "--json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, check=False)
    stdout = proc.stdout.strip()
    stderr = proc.stderr.strip()
    if proc.returncode != 0 and expect_ok:
        raise RuntimeError(
            f"command failed ({proc.returncode}): {' '.join(args)}\n"
            f"stdout: {stdout}\nstderr: {stderr}"
        )
    if not stdout:
        return {"ok": proc.returncode == 0, "stderr": stderr}
    return json.loads(stdout)


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> int:
    if not FIXTURE.is_file():
        print(f"fixture missing: {FIXTURE}", file=sys.stderr)
        return 1

    media = ROOT / "content-pipeline/media"
    campaign_dirs = [
        media / "raw-upload" / CAMPAIGN,
        media / "edited-usable-asset" / CAMPAIGN,
        media / "cards" / CAMPAIGN,
        media / "review" / CAMPAIGN,
    ]

    # Clean prior e2e artifacts
    for d in campaign_dirs:
        if d.exists():
            shutil.rmtree(d)

    print("1. ingest-raw-media")
    ingest = run("ingest-raw-media", "--campaign", CAMPAIGN, "--file", str(FIXTURE))
    assert_true(ingest.get("ok"), "ingest failed")
    raw_dest = Path(ingest["dest"])
    assert_true(raw_dest.is_file(), f"raw file missing: {raw_dest}")

    print("2. prepare edited asset + create-media-card")
    edited_dir = media / "edited-usable-asset" / CAMPAIGN
    edited_dir.mkdir(parents=True, exist_ok=True)
    edited_asset = edited_dir / f"{CARD_ID}.png"
    shutil.copy2(FIXTURE, edited_asset)

    create = run(
        "create-media-card",
        "--campaign",
        CAMPAIGN,
        "--asset",
        str(edited_asset),
        "--id",
        CARD_ID,
    )
    assert_true(create.get("ok"), "create-media-card failed")
    card = create["card"]
    assert_true(card["status"] == "draft", f"expected draft, got {card['status']}")

    print("3. validate-media-cards")
    validate = run("validate-media-cards", "--campaign", CAMPAIGN)
    assert_true(validate.get("ok"), "validation failed")

    print("4. generate-human-review-page")
    review = run("generate-human-review-page", "--campaign", CAMPAIGN)
    review_path = Path(review["review_page"])
    assert_true(review_path.is_file(), f"review page missing: {review_path}")
    html = review_path.read_text(encoding="utf-8")
    assert_true(CARD_ID in html, "card id not in review HTML")
    assert_true("ready_for_human_review" in html, "expected promoted status in review HTML")

    print("5. mark-media-card-approved")
    approved = run(
        "mark-media-card-approved",
        "--card",
        CARD_ID,
        "--approved-by",
        "e2e-tester",
        "--campaign",
        CAMPAIGN,
    )
    assert_true(approved["card"]["status"] == "human_approved", "approval status wrong")
    assert_true(approved["card"]["approval"]["approved"] is True, "approval flag not set")

    print("6. dry-run-publish-media-card (instagram)")
    dry = run(
        "dry-run-publish-media-card",
        "--card",
        CARD_ID,
        "--platform",
        "instagram",
        "--campaign",
        CAMPAIGN,
    )
    assert_true(dry.get("ok"), "dry-run publish failed")
    assert_true(dry["card"]["status"] == "publish_dry_run_passed", "dry-run status wrong")
    assert_true(
        dry["result"]["metadata"]["status_hint"] == "publish_dry_run_passed",
        "connector dry-run hint missing",
    )

    print("7. dry-run + publish-media-card stub (facebook)")
    fb_dry = run(
        "dry-run-publish-media-card",
        "--card",
        CARD_ID,
        "--platform",
        "facebook",
        "--campaign",
        CAMPAIGN,
    )
    assert_true(fb_dry.get("ok"), "facebook dry-run publish failed")
    pub = run(
        "publish-media-card",
        "--card",
        CARD_ID,
        "--platform",
        "facebook",
        "--campaign",
        CAMPAIGN,
    )
    assert_true(pub.get("ok"), "publish failed")
    assert_true(pub["card"]["status"] == "publish_dry_run_passed", "publish status wrong")
    assert_true("facebook" in pub["card"]["published"], "published metadata missing")
    assert_true(pub["result"]["stub"] is True, "expected stub publish response")

    print("8. connector registry spot-check")
    scripts = ROOT / "content-pipeline/scripts"
    sys.path.insert(0, str(scripts))
    from connectors import CONNECTORS, get_connector  # noqa: E402

    assert_true(set(CONNECTORS) == {"facebook", "instagram", "tiktok"}, "connector registry mismatch")
    for name in CONNECTORS:
        connector = get_connector(name, project_root=ROOT)
        errors = connector.validate(pub["card"])
        if name == "tiktok":
            assert_true(errors, "tiktok should reject image assets in v1")
        else:
            assert_true(not errors, f"{name} validate errors: {errors}")

    print("9. open-human-review-page (dry-run only)")
    open_result = run(
        "open-human-review-page",
        "--campaign",
        CAMPAIGN,
        "--dry-run",
    )
    assert_true(open_result.get("ok"), "open review dry-run failed")
    assert_true("would_open" in open_result, "missing would_open in dry-run response")

    print("\n✓ e2e test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
