---
name: paperheirloom-content-pipeline
description: Use when creating, reviewing, approving, or publishing Paper Heirloom Company media cards through the project content pipeline.
---

# Paper Heirloom content pipeline

Use this skill in `/home/bot/paper-heirloom-company` when the user asks about the social/media content pipeline.

Read first:

```text
content-pipeline/SPEC.md
```

Canonical control surface, once implemented:

```bash
python content-pipeline/scripts/run-paperheirloom-content-pipeline.py <action> [options]
```

Important rules:

- Treat JSON media cards as source of truth.
- Generate review HTML before approval.
- Open review HTML for human review.
- Only mark approved after explicit human confirmation.
- Only publish after explicit human publish instruction.
- Prefer dry-run before publish.
- Do not use Playwright/browser automation unless the user explicitly chooses that later.
- Do not store secrets in card JSON.
