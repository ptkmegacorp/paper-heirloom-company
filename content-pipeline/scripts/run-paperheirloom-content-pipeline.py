#!/usr/bin/env python3
"""Paper Heirloom Company content pipeline CLI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

from connectors import get_connector  # noqa: E402
from pipeline import (  # noqa: E402
    ActionError,
    ALLOWED_PLATFORMS,
    add_root_argument,
    apply_root_from_args,
    cards,
    create_media_card,
    ensure_publishable,
    browser,
    generate_human_review_page,
    ingest_raw_media_action,
    mark_media_card_approved,
    mark_publish_dry_run_passed,
    mark_published,
    mark_publish_failed,
    review_index_path,
    validate_media_cards,
    load_card_for_action,
)

def _emit(result: object, *, as_json: bool, verbose: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, default=str))
        return
    if isinstance(result, dict):
        for key, value in result.items():
            print(f"{key}: {value}")
    elif isinstance(result, Path):
        print(result)
    elif isinstance(result, list):
        for item in result:
            print(item)
    else:
        print(result)
    if verbose and not as_json:
        pass


def _cmd_ingest_raw_media(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    dest = ingest_raw_media_action(
        root,
        args.campaign,
        args.file,
        dry_run=args.dry_run,
    )
    _emit({"ok": True, "dest": str(dest)}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_create_media_card(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    card = create_media_card(
        root,
        args.campaign,
        args.asset,
        args.id,
        dry_run=args.dry_run,
    )
    _emit({"ok": True, "card": card}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_validate_media_cards(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    errors = validate_media_cards(root, args.campaign)
    if errors:
        _emit({"ok": False, "errors": errors}, as_json=args.json, verbose=args.verbose)
        return 1
    _emit({"ok": True, "campaign": args.campaign, "message": "all cards valid"}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_generate_human_review_page(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    out = generate_human_review_page(
        root,
        args.campaign,
        promote_drafts=not args.no_promote,
        dry_run=args.dry_run,
        use_local_model=args.use_local_model,
    )
    _emit({"ok": True, "review_page": str(out)}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_open_human_review_page(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    review_path = review_index_path(root, args.campaign)
    if not review_path.is_file():
        raise ActionError(
            f"review page not found: {review_path}; "
            f"run generate-human-review-page --campaign {args.campaign} first"
        )
    if args.dry_run:
        _emit({"ok": True, "would_open": review_path.as_uri(), "firefox_status": browser.firefox_status()}, as_json=args.json, verbose=args.verbose)
        return 0
    result = browser.open_file(review_path)
    _emit({"ok": True, "opened": review_path.as_uri(), "firefox": result}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_mark_media_card_approved(args: argparse.Namespace) -> int:
    root = apply_root_from_args(args)
    card = mark_media_card_approved(
        root,
        args.card,
        args.approved_by,
        campaign=args.campaign,
        dry_run=args.dry_run,
    )
    _emit({"ok": True, "card": card}, as_json=args.json, verbose=args.verbose)
    return 0


def _publish_action(args: argparse.Namespace, *, live: bool) -> int:
    root = apply_root_from_args(args)
    card, card_path = load_card_for_action(root, args.card, args.campaign)
    ensure_publishable(card, args.platform, require_platform_dry_run=live)

    connector = get_connector(args.platform, project_root=root)
    connector_errors = connector.validate(card)
    if connector_errors:
        raise ActionError(f"connector validation failed: {'; '.join(connector_errors)}")

    if args.dry_run:
        preview = connector.dry_run(card)
        _emit({"ok": True, "dry_run": True, "result": preview}, as_json=args.json, verbose=args.verbose)
        return 0

    try:
        if live:
            result = connector.publish(card)
            published = card.setdefault("published", {})
            published[args.platform] = {
                **result,
                "published_at": datetime.now(timezone.utc).isoformat(),
            }
            mark_published(card, args.platform)
        else:
            result = connector.dry_run(card)
            mark_publish_dry_run_passed(card, args.platform)
        cards.save_card(card, card_path)
    except Exception as exc:
        published = card.setdefault("published", {})
        published[args.platform] = {
            "error": str(exc),
            "failed_at": datetime.now(timezone.utc).isoformat(),
            "platform": args.platform,
        }
        mark_publish_failed(card)
        cards.save_card(card, card_path)
        raise ActionError(f"publish action failed: {exc}") from exc

    _emit({"ok": True, "card": card, "result": result}, as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_dry_run_publish_media_card(args: argparse.Namespace) -> int:
    return _publish_action(args, live=False)


def _cmd_publish_media_card(args: argparse.Namespace) -> int:
    return _publish_action(args, live=True)


def _cmd_firefox_status(args: argparse.Namespace) -> int:
    _emit(browser.firefox_status(), as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_refresh_human_review_page(args: argparse.Namespace) -> int:
    if args.dry_run:
        _emit({"ok": True, "would_refresh": True, "firefox_status": browser.firefox_status()}, as_json=args.json, verbose=args.verbose)
        return 0
    _emit(browser.refresh(), as_json=args.json, verbose=args.verbose)
    return 0


def _cmd_close_human_review_page(args: argparse.Namespace) -> int:
    if args.dry_run:
        _emit({"ok": True, "would_close": True, "firefox_status": browser.firefox_status()}, as_json=args.json, verbose=args.verbose)
        return 0
    _emit(browser.close(), as_json=args.json, verbose=args.verbose)
    return 0


def build_parser() -> argparse.ArgumentParser:
    global_parser = argparse.ArgumentParser(add_help=False)
    add_root_argument(global_parser)
    global_parser.add_argument("--dry-run", action="store_true", help="simulate without writing")
    global_parser.add_argument("--json", action="store_true", help="emit JSON output")
    global_parser.add_argument("--verbose", action="store_true", help="verbose output")

    parser = argparse.ArgumentParser(
        description="Paper Heirloom Company content pipeline",
    )
    sub = parser.add_subparsers(dest="action", required=True)

    p = sub.add_parser("ingest-raw-media", parents=[global_parser], help="copy raw media into campaign folder")
    p.add_argument("--campaign", required=True)
    p.add_argument("--file", required=True, type=Path)

    p = sub.add_parser("create-media-card", parents=[global_parser], help="create a JSON media card")
    p.add_argument("--campaign", required=True)
    p.add_argument("--asset", required=True, type=Path)
    p.add_argument("--id", required=True, dest="id")

    p = sub.add_parser("validate-media-cards", parents=[global_parser], help="validate cards in a campaign")
    p.add_argument("--campaign", required=True)

    p = sub.add_parser("generate-human-review-page", parents=[global_parser], help="generate review HTML")
    p.add_argument("--campaign", required=True)
    p.add_argument(
        "--no-promote",
        action="store_true",
        help="do not promote draft cards to ready_for_human_review",
    )
    p.add_argument(
        "--use-local-model",
        action="store_true",
        help="ask local llama-server for a small safe review-page intro fragment",
    )

    p = sub.add_parser("open-human-review-page", parents=[global_parser], help="open review HTML in Firefox")
    p.add_argument("--campaign", required=True)

    p = sub.add_parser("mark-media-card-approved", parents=[global_parser], help="mark card human-approved")
    p.add_argument("--card", required=True)
    p.add_argument("--approved-by", required=True)
    p.add_argument("--campaign", default=None)

    p = sub.add_parser("dry-run-publish-media-card", parents=[global_parser], help="dry-run publish via connector")
    p.add_argument("--card", required=True)
    p.add_argument("--platform", required=True, choices=sorted(ALLOWED_PLATFORMS))
    p.add_argument("--campaign", default=None)

    p = sub.add_parser("publish-media-card", parents=[global_parser], help="publish via connector stub")
    p.add_argument("--card", required=True)
    p.add_argument("--platform", required=True, choices=sorted(ALLOWED_PLATFORMS))
    p.add_argument("--campaign", default=None)

    sub.add_parser("firefox-status", parents=[global_parser], help="show Firefox/window-manager status")
    sub.add_parser("refresh-human-review-page", parents=[global_parser], help="refresh focused/open Firefox review window")
    sub.add_parser("close-human-review-page", parents=[global_parser], help="close Firefox review windows")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    handlers = {
        "ingest-raw-media": _cmd_ingest_raw_media,
        "create-media-card": _cmd_create_media_card,
        "validate-media-cards": _cmd_validate_media_cards,
        "generate-human-review-page": _cmd_generate_human_review_page,
        "open-human-review-page": _cmd_open_human_review_page,
        "mark-media-card-approved": _cmd_mark_media_card_approved,
        "dry-run-publish-media-card": _cmd_dry_run_publish_media_card,
        "publish-media-card": _cmd_publish_media_card,
        "firefox-status": _cmd_firefox_status,
        "refresh-human-review-page": _cmd_refresh_human_review_page,
        "close-human-review-page": _cmd_close_human_review_page,
    }

    try:
        return handlers[args.action](args)
    except ActionError as exc:
        if args.json:
            print(json.dumps({"ok": False, "error": str(exc)}))
        else:
            print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
