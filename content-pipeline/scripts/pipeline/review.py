"""Generate static human-review HTML pages."""

from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from . import cards, local_model, paths, state


def _render_media_preview(card: dict[str, Any], asset_href: str) -> str:
    asset_type = card.get("asset_type", "")
    if asset_type == "video":
        return (
            f'<video controls preload="metadata" src="{html.escape(asset_href, quote=True)}">'
            f"Your browser does not support video preview."
            f"</video>"
        )
    return (
        f'<img src="{html.escape(asset_href, quote=True)}" '
        f'alt="{html.escape(card.get("id", ""))}">'
    )


def _render_card_section(card: dict[str, Any], root: Path) -> str:
    card_id = card.get("id", "unknown")
    status = card.get("status", "")
    asset_rel = card.get("asset", "")
    asset_abs = paths.resolve_from_root(root, asset_rel)
    asset_href = asset_abs.as_uri()

    approval = card.get("approval") or {}
    approved = approval.get("approved", False)
    approved_by = approval.get("approved_by")
    approved_at = approval.get("approved_at")

    platforms = card.get("platforms") or []
    platform_tags = "".join(
        f'<span class="tag platform">{html.escape(p)}</span>' for p in platforms
    )

    approval_class = "approved" if approved else "pending"
    approval_text = "Approved" if approved else "Pending"
    approval_detail = ""
    if approved:
        detail_parts = []
        if approved_by:
            detail_parts.append(f"by {html.escape(str(approved_by))}")
        if approved_at:
            detail_parts.append(f"at {html.escape(str(approved_at))}")
        if detail_parts:
            approval_detail = f' <span class="muted">({" ".join(detail_parts)})</span>'

    return f"""
    <section class="card" data-status="{html.escape(status)}" data-id="{html.escape(card_id)}">
      <header>
        <h2>{html.escape(card_id)}</h2>
        <span class="tag status">{html.escape(status)}</span>
        <span class="tag {approval_class}">{approval_text}</span>{approval_detail}
      </header>
      <div class="preview">
        {_render_media_preview(card, asset_href)}
      </div>
      <dl class="meta">
        <dt>Campaign</dt><dd>{html.escape(card.get("campaign", ""))}</dd>
        <dt>Asset</dt><dd><code>{html.escape(asset_rel)}</code></dd>
        <dt>Format</dt><dd>{html.escape(card.get("format", ""))}</dd>
        <dt>Asset type</dt><dd>{html.escape(card.get("asset_type", ""))}</dd>
        <dt>Platforms</dt><dd class="tags">{platform_tags or '<span class="muted">none</span>'}</dd>
        <dt>CTA</dt><dd><a href="{html.escape(card.get("cta_url", ""), quote=True)}" target="_blank" rel="noopener">{html.escape(card.get("cta_url", ""))}</a></dd>
      </dl>
      <div class="caption">
        <h3>Caption</h3>
        <p>{html.escape(card.get("caption", ""))}</p>
      </div>
    </section>
    """


def _safe_intro_fragment(fragment: str) -> str:
    if not fragment or "<script" in fragment.lower():
        return ""
    return fragment


def _page_shell(campaign: str, sections: str, intro_fragment: str = "") -> str:
    intro = _safe_intro_fragment(intro_fragment) or "<p>Review each media card. Media appears above its caption; approval happens through the pipeline CLI after human confirmation.</p>"
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paper Heirloom — {html.escape(campaign)} review</title>
  <style>
    :root {{
      color-scheme: light dark;
      --bg: #f7f4ef;
      --surface: #ffffff;
      --text: #1f1a17;
      --muted: #6b625c;
      --border: #ddd4c8;
      --accent: #8b5a3c;
      --approved: #2d6a4f;
      --pending: #b08968;
    }}
    @media (prefers-color-scheme: dark) {{
      :root {{
        --bg: #1a1714;
        --surface: #24201c;
        --text: #f5efe8;
        --muted: #b0a69d;
        --border: #3d3630;
        --accent: #d4a574;
        --approved: #52b788;
        --pending: #ddb892;
      }}
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header.page {{
      padding: 1.5rem 2rem;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }}
    header.page h1 {{
      margin: 0 0 0.25rem;
      font-size: 1.5rem;
    }}
    header.page p {{
      margin: 0;
      color: var(--muted);
    }}
    .toolbar {{
      padding: 1rem 2rem;
      display: flex;
      gap: 0.75rem;
      flex-wrap: wrap;
      align-items: center;
      border-bottom: 1px solid var(--border);
      background: var(--surface);
    }}
    .toolbar label {{
      font-size: 0.9rem;
      color: var(--muted);
    }}
    .toolbar select, .toolbar button {{
      font: inherit;
      padding: 0.35rem 0.6rem;
      border: 1px solid var(--border);
      border-radius: 4px;
      background: var(--bg);
      color: var(--text);
    }}
    main {{
      padding: 1.5rem 2rem 3rem;
      display: grid;
      gap: 1.5rem;
      max-width: 960px;
    }}
    section.card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
    }}
    section.card header {{
      padding: 1rem 1.25rem;
      border-bottom: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
      align-items: center;
    }}
    section.card header h2 {{
      margin: 0;
      flex: 1 1 auto;
      font-size: 1.15rem;
    }}
    .preview {{
      background: #000;
      display: flex;
      justify-content: center;
      align-items: center;
      min-height: 200px;
    }}
    .preview img, .preview video {{
      max-width: 100%;
      max-height: 70vh;
      display: block;
    }}
    .meta {{
      margin: 0;
      padding: 1rem 1.25rem;
      display: grid;
      grid-template-columns: 8rem 1fr;
      gap: 0.35rem 1rem;
      border-bottom: 1px solid var(--border);
      font-size: 0.95rem;
    }}
    .meta dt {{
      margin: 0;
      color: var(--muted);
      font-weight: normal;
    }}
    .meta dd {{
      margin: 0;
    }}
    .meta code {{
      font-size: 0.85rem;
      word-break: break-all;
    }}
    .caption {{
      padding: 1rem 1.25rem 1.25rem;
    }}
    .caption h3 {{
      margin: 0 0 0.5rem;
      font-size: 0.95rem;
      color: var(--muted);
      font-weight: normal;
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}
    .caption p {{
      margin: 0;
      white-space: pre-wrap;
    }}
    .tag {{
      display: inline-block;
      padding: 0.15rem 0.5rem;
      border-radius: 999px;
      font-size: 0.8rem;
      background: var(--border);
    }}
    .tag.status {{ background: var(--accent); color: #fff; }}
    .tag.approved {{ background: var(--approved); color: #fff; }}
    .tag.pending {{ background: var(--pending); color: #fff; }}
    .tag.platform {{ margin-right: 0.35rem; }}
    .muted {{ color: var(--muted); }}
    .hidden {{ display: none !important; }}
  </style>
</head>
<body>
  <header class="page">
    <h1>Paper Heirloom — Human Review</h1>
    <p>Campaign: <strong>{html.escape(campaign)}</strong></p>
    {intro}
  </header>
  <div class="toolbar">
    <label for="status-filter">Filter by status</label>
    <select id="status-filter">
      <option value="">All</option>
      <option value="draft">draft</option>
      <option value="ready_for_human_review">ready_for_human_review</option>
      <option value="human_approved">human_approved</option>
      <option value="publish_dry_run_passed">publish_dry_run_passed</option>
      <option value="published">published</option>
      <option value="publish_failed">publish_failed</option>
      <option value="archived">archived</option>
    </select>
    <button type="button" id="show-all">Show all</button>
  </div>
  <main id="cards">
    {sections}
  </main>
  <script>
    (function () {{
      var filter = document.getElementById("status-filter");
      var cards = document.querySelectorAll("section.card");
      function applyFilter() {{
        var value = filter.value;
        cards.forEach(function (card) {{
          var show = !value || card.dataset.status === value;
          card.classList.toggle("hidden", !show);
        }});
      }}
      filter.addEventListener("change", applyFilter);
      document.getElementById("show-all").addEventListener("click", function () {{
        filter.value = "";
        applyFilter();
      }});
    }})();
  </script>
</body>
</html>
"""


def generate_review_html(
    root: Path | str | None,
    campaign: str,
    *,
    promote_drafts: bool = False,
    use_local_model: bool = False,
) -> Path:
    """Generate a static review page for all cards in *campaign*.

    Writes ``content-pipeline/media/review/{campaign}/index.html``.

    When *promote_drafts* is True, cards still in ``draft`` are updated to
    ``ready_for_human_review`` after the review page is generated. This mirrors
    the optional post-generation transition described in the pipeline spec:
    generating a human review page signals that drafts are ready for review.
    """
    root_path = paths.get_root(root)
    card_paths = cards.list_campaign_card_paths(root_path, campaign)
    if not card_paths:
        raise FileNotFoundError(f"no media cards found for campaign {campaign!r}")

    sections: list[str] = []
    loaded_cards: list[dict[str, Any]] = []
    for card_path in card_paths:
        card = cards.load_card(card_path)
        loaded_cards.append(card)
        if promote_drafts and card.get("status") == state.DRAFT:
            state.mark_ready_for_human_review(card)
            cards.save_card(card, card_path)
        sections.append(_render_card_section(card, root_path))

    intro_fragment = local_model.generate_review_intro(campaign, loaded_cards) if use_local_model else ""
    output_path = paths.review_index_path(root_path, campaign)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(_page_shell(campaign, "\n".join(sections), intro_fragment), encoding="utf-8")
    return output_path
