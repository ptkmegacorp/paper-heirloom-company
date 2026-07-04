# Paper Heirloom Company — Agent-Driven Content Pipeline Spec v1

**Status:** Spec only — not implemented  
**Goal:** Define a basic, file-based media-card workflow that AI agents can operate deterministically.

## Core idea

A human prompts the main AI agent. The agent uses one project CLI as the control surface. Python owns file/state changes. A local model may help generate review HTML or draft text, but it must not approve or publish.

```text
human prompt
  → main agent
  → run-paperheirloom-content-pipeline action
  → deterministic files + review HTML
  → Firefox human review
  → human tells agent approved
  → agent runs approve/publish actions
```

## Keep v1 simple

- Plain files, no database.
- Python standard library where possible.
- Static HTML review page, no external dependencies.
- JSON media cards are the source of truth.
- Publishing connectors can start as dry-run stubs.
- No Playwright in v1 unless official/scheduler options are unavailable later.

## Directory layout

```text
content-pipeline/
  SPEC.md
  media/
    raw-upload/
    edited-usable-asset/
    cards/
    review/
  scripts/
    run-paperheirloom-content-pipeline.py
    connectors/
      base.py
      instagram.py
      facebook.py
      tiktok.py
```

Recommended campaign subfolders:

```text
content-pipeline/media/raw-upload/2026-07-launch/file.mov
content-pipeline/media/edited-usable-asset/2026-07-launch/file-vertical.mp4
content-pipeline/media/cards/2026-07-launch/fold-demo-01.json
content-pipeline/media/review/2026-07-launch/index.html
```

## Media card JSON v1

```json
{
  "id": "fold-demo-01",
  "campaign": "2026-07-launch",
  "status": "draft",
  "asset": "content-pipeline/media/edited-usable-asset/2026-07-launch/fold-demo-01.mp4",
  "asset_type": "video",
  "format": "vertical_video",
  "caption": "A bridal shower activity that becomes wedding place cards.",
  "cta_url": "https://paperheirloomcompany.etsy.com",
  "platforms": ["instagram", "facebook", "tiktok"],
  "approval": {
    "approved": false,
    "approved_by": null,
    "approved_at": null
  },
  "published": {}
}
```

Optional later fields: `hashtags`, `alt_text`, `thumbnail`, `scheduled_at`, `notes`, `ai_disclosure_required`.

## State machine

Allowed statuses:

```text
draft
ready_for_human_review
human_approved
publish_dry_run_passed
published
publish_failed
archived
```

Rules:

- Only the CLI changes status.
- `human_approved` requires explicit human instruction to the main agent.
- Publish commands must reject cards not marked `human_approved` or `publish_dry_run_passed`.
- Connector failures set `publish_failed` and log the error in the card or a sidecar log.

## CLI control surface

Canonical command name:

```bash
python content-pipeline/scripts/run-paperheirloom-content-pipeline.py <action> [options]
```

Required v1 actions:

```bash
# Copy or register raw media under content-pipeline/media/raw-upload/
ingest-raw-media --campaign CAMPAIGN --file PATH

# Create a basic JSON card for an edited/usable asset
create-media-card --campaign CAMPAIGN --asset PATH --id CARD_ID

# Validate card schema, asset paths, status, and platform names
validate-media-cards --campaign CAMPAIGN

# Generate static human review HTML from cards
generate-human-review-page --campaign CAMPAIGN

# Open the generated review page in Firefox
open-human-review-page --campaign CAMPAIGN

# Mark a card approved after explicit human approval
mark-media-card-approved --card CARD_ID --approved-by NAME

# Dry-run a publish connector without posting
dry-run-publish-media-card --card CARD_ID --platform PLATFORM

# Publish an approved card through a connector
publish-media-card --card CARD_ID --platform PLATFORM
```

Helpful global flags:

```text
--dry-run
--json
--verbose
--root PATH
```

## Human review page

The review page is static HTML generated into:

```text
content-pipeline/media/review/{campaign}/index.html
```

V1 layout:

- One card per media card.
- Image/video preview on top.
- Caption and CTA below.
- Platforms, status, asset path, and approval state shown plainly.
- No external CSS/JS.
- Vanilla JS allowed only for filtering/display convenience.

The local model may generate simple HTML fragments, but Python must wrap them in a fixed safe template and write the final file.

## Connector interface

Each connector should expose the same minimal interface:

```python
class Connector:
    platform = "instagram"

    def validate(self, card: dict) -> list[str]:
        """Return validation errors. Empty list means OK."""

    def dry_run(self, card: dict) -> dict:
        """Return planned action without publishing."""

    def publish(self, card: dict) -> dict:
        """Publish and return platform response metadata."""
```

Initial connectors may be stubs that only validate and dry-run.

## Platform guidance

- Instagram/Facebook: prefer official Meta APIs or an approved scheduler.
- TikTok: prefer official Content Posting API; draft upload may be safer than direct post.
- Playwright/browser automation is not part of v1. If considered later, restrict to supervised upload assistance for our own accounts only; no scraping, engagement automation, proxy/evasion, or mass actions.

## Agent safety rules

- Never publish unless the user explicitly asks to publish.
- Never mark approved unless the user explicitly confirms approval.
- Never infer approval from generated review HTML.
- Prefer dry-run before publish.
- Keep all state in media card JSON files.
- Do not store secrets in media card JSON.

## Open questions

- Exact account setup for IG/FB/TikTok.
- Scheduler-first vs direct APIs.
- Where to host public media for API publishing.
- Whether local model is required for HTML, or deterministic Python templates are enough.
- Exact caption/hashtag fields for v1.
- Approval identity format: name, initials, or git user.
