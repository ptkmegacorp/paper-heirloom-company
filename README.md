# Paper Heirloom Company

Static site and planning docs for Paper Heirloom Company: a bridal shower gift/activity where guests fold printed origami crane sheets, then use the finished cranes as wedding place card holders.

## Published site

- GitHub Pages source: `docs/`
- Custom domain: `paperheirloomcompany.com`
- Etsy CTA: `https://paperheirloomcompany.etsy.com`

## Key docs

- `pricing.md` — pricing strategy and color tiers
- `partnerships-and-outreach.md` — early outreach plan
- `pseo/SPEC.md` — pSEO static page generator plan
- `media-content-pipeline.md` — initial social/media research notes
- `content-pipeline/SPEC.md` — v1 spec for the agent-driven media card pipeline

## Content pipeline

The planned content pipeline will use structured JSON media cards, local review HTML, and a single Python control surface named:

```bash
python content-pipeline/scripts/run-paperheirloom-content-pipeline.py <action>
```

See `content-pipeline/SPEC.md`. This is currently a spec only; implementation is intentionally left for a later build step.
