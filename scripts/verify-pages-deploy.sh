#!/usr/bin/env bash
# Verify GitHub Pages deploy workflow and live site.
# Usage: ./scripts/verify-pages-deploy.sh
set -euo pipefail

REPO="ptkmegacorp/paper-heirloom-company"
GITHUB_IO="https://ptkmegacorp.github.io/paper-heirloom-company/"
CUSTOM_DOMAIN="paperheirloomcompany.com"
GITHUB_A="185.199.108.153"

pass=0
fail=0

ok()   { echo "  ✓ $1"; pass=$((pass + 1)); }
bad()  { echo "  ✗ $1"; fail=$((fail + 1)); }
section() { echo ""; echo "== $1 =="; }

section "1. GitHub Pages config"
pages_json="$(gh api "repos/${REPO}/pages" 2>/dev/null || true)"
if [[ -z "$pages_json" ]]; then
  bad "Could not read Pages config (is gh authenticated?)"
else
  build_type="$(echo "$pages_json" | jq -r '.build_type')"
  status="$(echo "$pages_json" | jq -r '.status')"
  cname="$(echo "$pages_json" | jq -r '.cname // empty')"
  source="$(echo "$pages_json" | jq -r '.source.branch + " / " + .source.path')"

  [[ "$build_type" == "workflow" ]] && ok "build_type is workflow" || bad "build_type is '$build_type' (expected workflow)"
  [[ "$status" == "built" ]] && ok "Pages status is built" || bad "Pages status is '$status' (expected built)"
  [[ "$cname" == "$CUSTOM_DOMAIN" ]] && ok "Custom domain CNAME is $CUSTOM_DOMAIN" || bad "Custom domain is '$cname'"
  ok "Legacy branch source (unused): $source"
fi

section "2. Latest deploy workflow run"
run_json="$(gh run list --repo "$REPO" --workflow "Deploy static content to Pages" --limit 1 --json databaseId,conclusion,status,displayTitle,url 2>/dev/null || echo '[]')"
if [[ "$(echo "$run_json" | jq 'length')" -eq 0 ]]; then
  bad "No 'Deploy static content to Pages' runs found"
else
  run_id="$(echo "$run_json" | jq -r '.[0].databaseId')"
  conclusion="$(echo "$run_json" | jq -r '.[0].conclusion')"
  run_status="$(echo "$run_json" | jq -r '.[0].status')"
  run_url="$(echo "$run_json" | jq -r '.[0].url')"

  [[ "$run_status" == "completed" ]] && ok "Run completed (id $run_id)" || bad "Run status is '$run_status'"
  [[ "$conclusion" == "success" ]] && ok "Run conclusion is success" || bad "Run conclusion is '$conclusion'"
  echo "    $run_url"

  section "2b. Workflow job steps"
  jobs_json="$(gh api "repos/${REPO}/actions/runs/${run_id}/jobs" --jq '.jobs[] | select(.name=="deploy") | .steps[] | {name, conclusion}' 2>/dev/null || echo '')"
  if [[ -z "$jobs_json" ]]; then
    bad "Could not read deploy job steps"
  else
    while IFS= read -r step; do
      name="$(echo "$step" | jq -r '.name')"
      conc="$(echo "$step" | jq -r '.conclusion')"
      if [[ "$conc" == "success" || "$conc" == "skipped" ]]; then
        ok "Step: $name ($conc)"
      else
        bad "Step: $name ($conc)"
      fi
    done < <(echo "$jobs_json" | jq -c '.')
  fi

  section "2c. Workflow annotations (errors only)"
  ann="$(gh api "repos/${REPO}/check-runs/${run_id}/annotations" 2>/dev/null || true)"
  # Fallback: parse run view for error annotations
  errors="$(gh run view "$run_id" --repo "$REPO" 2>/dev/null | grep -E '^X |##\[error\]' || true)"
  if [[ -n "$errors" ]]; then
    bad "Run has error annotations:"
    echo "$errors" | sed 's/^/    /'
  else
    ok "No error-level annotations on latest run"
  fi
fi

section "3. Live site — github.io"
http_code="$(curl -sS -o /tmp/phc-verify-body.html -w '%{http_code}' --max-time 20 "$GITHUB_IO")"
if [[ "$http_code" == "200" ]]; then
  ok "GET $GITHUB_IO → HTTP $http_code"
else
  bad "GET $GITHUB_IO → HTTP $http_code (expected 200)"
fi

if grep -q "Paper Heirloom Company" /tmp/phc-verify-body.html 2>/dev/null; then
  ok "Page body contains 'Paper Heirloom Company'"
else
  bad "Page body missing expected title text"
fi

if grep -q "pigeon-flannel-logo.png" /tmp/phc-verify-body.html 2>/dev/null; then
  ok "Page references flannel logo asset"
else
  bad "Page missing flannel logo reference"
fi

if grep -q "Purchase on Etsy" /tmp/phc-verify-body.html 2>/dev/null; then
  ok "Page contains Etsy CTA"
else
  bad "Page missing Etsy CTA"
fi

section "4. Live site — custom domain (via GitHub IP)"
custom_code="$(curl -sS -o /tmp/phc-verify-custom.html -w '%{http_code}' --max-time 20 \
  --resolve "${CUSTOM_DOMAIN}:443:${GITHUB_A}" "https://${CUSTOM_DOMAIN}/" 2>/dev/null || echo "000")"
if [[ "$custom_code" == "200" ]]; then
  ok "GET https://${CUSTOM_DOMAIN}/ (forced to GitHub IP) → HTTP $custom_code"
elif [[ "$custom_code" == "301" || "$custom_code" == "302" ]]; then
  ok "GET https://${CUSTOM_DOMAIN}/ → HTTP $custom_code (redirect; cert may still be provisioning)"
else
  bad "GET https://${CUSTOM_DOMAIN}/ (GitHub IP) → HTTP $custom_code"
  echo "    Tip: disable Namecheap URL Forward if you still see parking locally"
fi

section "5. DNS (public resolver 8.8.8.8)"
apex_ips="$(dig +short "$CUSTOM_DOMAIN" A @8.8.8.8 | sort)"
if echo "$apex_ips" | grep -q "185.199.108.153"; then
  ok "Apex A records include GitHub Pages IPs"
  echo "$apex_ips" | sed 's/^/    /'
else
  bad "Apex A records do not look like GitHub Pages yet"
  echo "$apex_ips" | sed 's/^/    /'
fi

www_cname="$(dig +short "www.${CUSTOM_DOMAIN}" CNAME @8.8.8.8 | head -1)"
if echo "$www_cname" | grep -qi "ptkmegacorp.github.io"; then
  ok "www CNAME → $www_cname"
else
  bad "www CNAME is '$www_cname' (expected ptkmegacorp.github.io)"
fi

section "Summary"
echo "  Passed: $pass"
echo "  Failed: $fail"
if [[ "$fail" -eq 0 ]]; then
  echo ""
  echo "All checks passed. Deploy workflow and site look healthy."
  exit 0
else
  echo ""
  echo "Some checks failed — review items marked ✗ above."
  exit 1
fi
