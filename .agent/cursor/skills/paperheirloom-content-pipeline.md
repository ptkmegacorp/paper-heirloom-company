# Paper Heirloom content pipeline skill

Use for the Paper Heirloom Company agent-driven media pipeline.

Project spec:

- `content-pipeline/SPEC.md`

Canonical CLI, once implemented:

```bash
python content-pipeline/scripts/run-paperheirloom-content-pipeline.py <action> [options]
```

Agent rules:

- Keep v1 file-based and simple.
- JSON media cards are the source of truth.
- Python CLI owns state transitions.
- Human review happens through generated static HTML.
- Do not approve or publish without explicit human instruction.
- Prefer official APIs or approved schedulers; Playwright is last-resort only.
