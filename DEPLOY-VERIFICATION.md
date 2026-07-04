# Pages deploy — verification proof package

Use this after any change to `docs/` or `.github/workflows/deploy-pages.yml` to confirm the deploy pipeline is clean.

## Quick run (automated)

```bash
cd paper-heirloom-company
chmod +x scripts/verify-pages-deploy.sh
./scripts/verify-pages-deploy.sh
```

**Pass criteria:** script exits `0`, all lines show `✓`, no `✗`.

## Manual spot-check (do once together)

### A. Trigger a fresh deploy

```bash
gh workflow run "Deploy static content to Pages" --repo ptkmegacorp/paper-heirloom-company
gh run watch --repo ptkmegacorp/paper-heirloom-company
```

Or: **Actions → Deploy static content to Pages → Run workflow**.

### B. Confirm in GitHub UI

| Check | Where | Expected |
|-------|--------|----------|
| Workflow green | Actions → latest run | All steps ✓, conclusion **Success** |
| No red X annotations | Same run → Annotations | Empty (Node deprecation notice is OK) |
| Pages built | Settings → Pages | **Your site is live at…** |
| Source | Settings → Pages | **GitHub Actions** |
| Custom domain | Settings → Pages | `paperheirloomcompany.com` |

### C. Confirm live content

Open: https://ptkmegacorp.github.io/paper-heirloom-company/

You should see:

- [ ] Hero with “Paper Heirloom Company”
- [ ] Flannel pigeon logo above **Purchase on Etsy →**
- [ ] Hero infographic image loads
- [ ] No GitHub 404 page

### D. What we fixed in the workflow

Per [GitHub’s custom Pages workflow docs](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages):

| Requirement | Our workflow |
|-------------|--------------|
| `permissions: pages: write, id-token: write` | ✓ |
| `actions/configure-pages@v5` | ✓ |
| `actions/upload-pages-artifact@v4` + `path: docs` | ✓ |
| `include-hidden-files: true` (for `.nojekyll`) | ✓ (v4 only) |
| `actions/deploy-pages@v5` | ✓ |
| `environment: github-pages` | ✓ |

## Expected workflow run (reference)

```
deploy
  ✓ Checkout
  ✓ Setup Pages
  ✓ Upload artifact
  ✓ Deploy to GitHub Pages
```

## If something fails

| Symptom | Likely fix |
|---------|------------|
| Deploy step: “try again later” | Re-run workflow; check [GitHub Status](https://www.githubstatus.com/) |
| `include-hidden-files` warning | Ensure `upload-pages-artifact@v4` (not v3) |
| github.io 404 | Pages status not `built` — check Actions log |
| Custom domain shows Namecheap | Disable URL Forward in Namecheap; wait for DNS |
| HTTPS not available | Enable **Enforce HTTPS** in Pages settings after first successful deploy |

## Proof artifact

After a clean run, save the run URL for your records:

```bash
gh run list --repo ptkmegacorp/paper-heirloom-company --workflow "Deploy static content to Pages" --limit 1
```
