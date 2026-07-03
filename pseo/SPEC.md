# pSEO Page Generator — Spec & Scaffold

**Status:** Waiting on finalized landing page design  
**Project:** Paper Heirloom Company  
**Last updated:** 2026-07-03  

Use this doc when the main landing page (`docs/index.html`) is locked. Until then, do not run a generator against production paths.

---

## Purpose

Build a small **Python script** that reads curated keyword/page data and outputs **static HTML** under `docs/{slug}/index.html` for GitHub Pages.

Goals:

- One design template → many SEO landing pages
- Human-reviewed copy per page (no auto-publish of 100+ thin pages)
- Dry-run and single-slug modes before batch generation
- Align with keyword plan in `../pseo-keywords-v2.txt`

Non-goals (for v1 of the generator):

- PHP or server-side rendering
- CI auto-generation on every push
- AI-written copy without review
- Replacing the canonical main page at `/` (`docs/index.html`)

---

## Prerequisites (check before writing code)

- [ ] **Landing page design finalized** — `docs/index.html` is the visual/copy source of truth
- [ ] **Template extracted** — duplicate into `pseo/template.html` with placeholders
- [ ] **Asset paths stable** — hub uses `assets/`; spokes use `../assets/` or root-absolute `/assets/` once custom domain is live
- [ ] **Etsy URL decided** — replace `#` placeholders in nav/CTA
- [ ] **P1 keyword list curated** — 8–15 rows in JSON, pulled from v2 canonical map
- [ ] **Custom domain** — add `docs/CNAME` when DNS verifies (see GitHub Pages notes)

---

## Directory layout

```text
paper-heirloom-company/
├── docs/                         # GitHub Pages publish root (ONLY this folder is public)
│   ├── index.html                # Main landing (hand-maintained hub)
│   ├── assets/                   # Shared images, site.css later
│   ├── CNAME                     # Add when custom domain DNS is verified
│   └── {slug}/index.html         # Generated pSEO spokes
├── pseo/
│   ├── SPEC.md                   # This file
│   ├── keywords.p1.json          # First batch — hand-curated (create when ready)
│   ├── template.html             # From finalized docs/index.html
│   ├── generate_pages.py         # Writes to docs/{slug}/
│   └── output/                   # Optional staging for dry-run review
├── pricing.md
├── partnerships-and-outreach.md
├── pseo-keywords-v1.txt
└── pseo-keywords-v2.txt
```

**Repo rule:** Everything outside `docs/` is private planning — not published.

---

## Input format — `keywords.p1.json`

```json
[
  {
    "slug": "origami-bridal-shower-gift",
    "primary_keyword": "origami bridal shower gift",
    "cluster": "A",
    "priority": "P1",
    "title": "Origami Bridal Shower Gift — Fold Together, Use at the Wedding | Paper Heirloom Company",
    "meta_description": "A group bridal shower gift: guests fold origami crane sheets at the shower; those same cranes become wedding reception place card holders.",
    "h1": "Origami bridal shower gift your guests fold together",
    "hero_eyebrow": "Bridal shower gift edition",
    "hero_lead": "Short unique intro paragraph for this slug (must differ from other pages).",
    "canonical_path": "/origami-bridal-shower-gift/",
    "related_slugs": ["shower-gift-becomes-place-cards", "black-origami-crane-place-cards"],
    "variant": "default"
  }
]
```

### Asset path rule for generator

| Output file | Asset href |
|-------------|------------|
| `docs/index.html` | `assets/...` |
| `docs/{slug}/index.html` | `../assets/...` |
| Any page (custom domain live) | `/assets/...` (preferred) |

---

## Generator script — `generate_pages.py` (planned)

### CLI

```bash
python pseo/generate_pages.py --dry-run
python pseo/generate_pages.py --slug origami-bridal-shower-gift
python pseo/generate_pages.py --all
python pseo/generate_pages.py --all --output pseo/output/
python pseo/generate_pages.py --all --force
```

### Flags

| Flag | Behavior |
|------|----------|
| `--dry-run` | Print paths; write nothing |
| `--slug SLUG` | Generate one page |
| `--all` | All rows in `keywords.p1.json` |
| `--output DIR` | Staging dir (default: `docs/`) |
| `--force` | Overwrite existing (never hub without explicit flag) |
| `--input FILE` | Default `pseo/keywords.p1.json` |

### Output

```text
docs/{slug}/index.html
```

Optional: `docs/sitemap.xml`, `pseo/generated-manifest.json`

### Protect hub

Generator **must not overwrite** `docs/index.html` unless `--force-hub` is explicitly passed.

---

## Public URL map (after custom domain)

| Repo path | Public URL |
|-----------|------------|
| `docs/index.html` | `https://yourdomain.com/` |
| `docs/{slug}/index.html` | `https://yourdomain.com/{slug}/` |

GitHub Pages (pre-domain): `https://ptkmegacorp.github.io/paper-heirloom-company/` and `.../{slug}/`

See `../pseo-keywords-v2.txt` for full keyword → URL canonical map.

---

## P1 slugs to seed first

| slug | primary_keyword |
|------|-----------------|
| `origami-bridal-shower-gift` | origami bridal shower gift |
| `origami-wedding-shower-gift` | origami wedding shower gift |
| `shower-gift-becomes-place-cards` | shower gift that becomes place cards |
| `fold-together-bridal-shower-gift` | fold together bridal shower gift |
| `interactive-bridal-shower-gift` | interactive bridal shower gift |
| `group-bridal-shower-gift` | group bridal shower gift |
| `black-origami-crane-place-cards` | black origami crane place cards |
| `black-origami-crane-bridal-shower-gift` | black origami crane bridal shower gift |
| `origami-place-card-holders-wedding` | origami place card holders wedding |
| `fold-yourself-wedding-place-cards` | fold yourself wedding place cards |

---

## GitHub Pages

- **Source:** `main` branch, **`/docs`** folder
- **Custom domain (later):** Repo → Settings → Pages → add domain; create `docs/CNAME` with domain name; wait for DNS verify
- **No PHP** — static HTML only
- Root redirect removed — `docs/` is the publish root

---

## Workflow when ready

1. Finalize `docs/index.html`
2. Copy → `pseo/template.html`; add `{{ placeholders }}`
3. Create `pseo/keywords.p1.json`
4. Implement `generate_pages.py` → output to `docs/{slug}/`
5. Dry-run → one slug → review in Firefox → batch → commit → push

---

## Open decisions

| Decision | Choice |
|----------|--------|
| Etsy shop URL | _TBD_ |
| Staging dir vs write direct to `docs/` | _TBD_ |
| Shared CSS in `docs/assets/site.css` | _TBD_ |
| Custom domain | _Waiting on DNS verify_ |

---

## Related files

- `../pseo-keywords-v2.txt` — keyword → URL map (public paths use `/`, not `/website/`)
- `../docs/index.html` — current landing page
