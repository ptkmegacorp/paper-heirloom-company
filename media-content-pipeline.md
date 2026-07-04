# Paper Heirloom Company — Media Content Pipeline v1

**Status:** Research notes / background  
**Last updated:** 2026-07-03  
**Goal:** Create a repeatable pipeline to make, approve, and distribute product media to Instagram, Facebook, TikTok, and later Pinterest/Etsy.

**Implementation spec:** see `content-pipeline/SPEC.md` for the agent-driven JSON media-card workflow and CLI control surface.

---

## 1. Desired pipeline

```text
Idea / campaign brief
  → source media capture or generation
  → edit / compose platform-ready assets
  → caption + hashtag + link metadata
  → human approval
  → publish or schedule via official APIs/tools
  → log post URLs + metrics
  → reuse winners into pSEO / Etsy / email
```

The pipeline should assume we need both **brand-safe review** and **platform-specific formatting** before anything goes live.

---

## 2. Content inputs

### Product media

- Photos of flat crane sheets
- Photos/video of folding process
- Finished crane place card holders
- Table/reception mockups
- Packaging/unboxing shots
- Color/theme variants: white, lavender, green, black/gold

### Generated or composed media

- Infographics: “fold at shower → display at wedding”
- Text overlays for Reels/TikTok
- Pinterest-style tall graphics
- Carousel frames explaining the concept
- Theme mockups for pSEO and Etsy listings

### Human-shot media to prioritize

For trust, launch content should lean on real product footage first. AI/generated media can help with backgrounds, layout, and concept graphics, but finished product claims should remain accurate.

---

## 3. Edit / compose step

This should become a first-class step, not an afterthought.

Recommended v1 asset types:

| Platform | Format | Notes |
|---|---|---|
| Instagram Feed | 1:1 or 4:5 image/carousel | Product hero, explainer carousel |
| Instagram Reels | 9:16 video | Folding demo, shower-to-table story |
| Facebook Page | Image/video/link post | Similar to IG, less trend-dependent |
| TikTok | 9:16 video | Process, satisfying folds, wedding POV |
| Pinterest later | 2:3 vertical image | SEO/evergreen discovery |

Possible local tools:

- `ffmpeg` for video resize, trim, captions burn-in, thumbnail extraction
- ImageMagick or Python/Pillow for image resizing/composition
- Canva/Figma manually for early templates
- Later: small script that takes `media.json` + assets and exports platform variants

Suggested internal artifact:

```text
media/
  source/
  composed/
  ready/
  published/
  campaigns/
    2026-07-launch/
      brief.md
      posts.json
```

Do **not** publish raw/generated assets directly. Everything should pass through `ready/` and a human approval checklist.

---

## 4. Publishing options

### Option A — Official APIs / SDKs directly

Best long-term if we want control and can handle app setup.

#### Instagram

Official route: **Instagram Platform / Instagram Graph API content publishing**.

Current official docs say it can publish single images, videos, reels, stories, and carousel posts for Instagram professional accounts. Requirements include:

- Instagram professional account
- Connected Meta/Facebook assets depending on login path
- Required permissions such as `instagram_content_publish` or `instagram_business_content_publish`
- Media must be on a publicly accessible URL, or uploaded through supported resumable flows
- Publishing uses a container flow: create media container → check status if needed → publish container
- Rate limit: Instagram accounts are limited to API-published posts in a 24-hour moving window

Important implementation detail: Meta fetches media by URL for many publishing flows, so we need a temporary public media host/CDN or use the supported upload endpoint for video flows.

#### Facebook Page

Official route: **Facebook Pages API**.

Docs show publishing to a Page via Graph API using a Page access token and permissions including:

- `pages_manage_posts`
- `pages_read_engagement` / `pages_manage_read_engagement`
- `pages_show_list`
- `pages_manage_metadata`

Text posts publish through `POST /{page_id}/feed`; photos/videos have related Pages API endpoints.

#### TikTok

Official route: **TikTok Content Posting API**.

TikTok offers:

- Direct Post API — post directly from our app to the TikTok profile
- Upload API — upload as a draft, then finish/edit/post inside TikTok

For v1, Upload-as-draft may be safer because TikTok-native editing/sounds/trends matter and direct posting may require more review/approval.

Pros:

- Most compliant
- Lower account-ban risk
- Can scale into scheduling/logging

Cons:

- App creation, OAuth, permissions, review, and token storage required
- More engineering than using a scheduler
- Media hosting requirement for some Meta flows

---

### Option B — Approved third-party scheduler

Use tools like Buffer, Later, Metricool, Hootsuite, SocialPilot, etc. Validate exact capabilities before choosing.

Pros:

- Fastest operational v1
- Handles token refresh and platform quirks
- Often supports IG/FB/TikTok scheduling from one calendar
- Less maintenance

Cons:

- Monthly cost
- Less custom automation
- API access may still be limited by platform rules
- Need export/logging back into our project

Recommended early path: use a scheduler manually for the first month while we build the asset/caption/approval system locally.

---

### Option C — Playwright/browser automation

Use Playwright to log into social accounts and click through web upload flows.

This should be considered a **last resort** and only for internal assisted workflows, not stealth automation.

Policy risk notes:

- Meta/Instagram terms prohibit unauthorized automated access/collection; Instagram Help also flags automated collection/access as data scraping behavior when done without permission.
- TikTok Terms prohibit scraping/crawling/exporting/extracting data/content using automated systems unless approved in writing.
- Even if our intent is posting our own content, browser automation can trigger anti-bot/account-security systems, CAPTCHA, login challenges, or account restriction.
- Avoid automation for scraping, mass liking/following/commenting, DM automation, follower harvesting, or bypassing platform limitations.

If Playwright is used at all:

- Use it only as a supervised “upload assistant” for our own accounts/content
- No scraping, engagement automation, or evasion/proxy behavior
- Keep rate very low
- Require human confirmation before publish
- Prefer official APIs or approved scheduler whenever available

---

## 5. Recommended v1 architecture

### Phase 1 — Manual publishing, structured pipeline

Create the system before automating distribution:

1. Create campaign briefs
2. Store source media
3. Compose platform-ready assets
4. Write captions/hashtags
5. Human approve
6. Manually post or use a scheduler
7. Record URLs and results

This gives us learning without API complexity.

### Phase 2 — API proof of concept

Build one small internal script for Facebook Page or Instagram first:

- Store post metadata in JSON
- Upload/host media somewhere public if needed
- Publish to one platform
- Log API response and post URL

Do not start with all platforms at once.

### Phase 3 — Unified publisher

A local CLI could eventually look like:

```bash
python scripts/social_publish.py --campaign 2026-07-launch --post fold-demo-01 --platform instagram --dry-run
python scripts/social_publish.py --campaign 2026-07-launch --post fold-demo-01 --platform facebook --publish
python scripts/social_publish.py --campaign 2026-07-launch --post fold-demo-01 --platform tiktok --draft
```

---

## 6. Proposed post metadata shape

```json
{
  "id": "fold-demo-01",
  "status": "draft",
  "campaign": "2026-07-launch",
  "theme": "black-gold",
  "assets": {
    "source": ["media/source/fold-demo.mov"],
    "ready": {
      "instagram_reel": "media/ready/fold-demo-01-ig-reel.mp4",
      "tiktok": "media/ready/fold-demo-01-tiktok.mp4",
      "facebook": "media/ready/fold-demo-01-fb.mp4"
    }
  },
  "caption": "A bridal shower activity that becomes wedding place cards.",
  "hashtags": ["bridalshowerideas", "weddingplacecards", "origamiwedding"],
  "cta_url": "https://paperheirloomcompany.etsy.com",
  "platforms": {
    "instagram": { "type": "reel", "publish_mode": "manual_or_api" },
    "facebook": { "type": "video", "publish_mode": "manual_or_api" },
    "tiktok": { "type": "video", "publish_mode": "draft" }
  },
  "approval": {
    "approved_by": null,
    "approved_at": null
  },
  "published": {}
}
```

---

## 7. Approval checklist

Before publishing:

- [ ] Product shown accurately
- [ ] No misleading AI-generated product details
- [ ] Etsy/shop link correct
- [ ] Caption matches current availability/pricing
- [ ] Music/audio rights acceptable for platform
- [ ] Text overlays legible on mobile
- [ ] Platform aspect ratio correct
- [ ] If AI-generated media used, platform disclosure rules considered
- [ ] No customer/private data visible

---

## 8. Open questions

- Which accounts already exist? IG, FB Page, TikTok, Pinterest?
- Are IG and FB connected in Meta Business Suite?
- Is the Instagram account a professional/business account?
- Do we want direct API publishing or scheduler-first?
- Where should public media be temporarily hosted for Meta API publishing?
- Do we want TikTok direct posting or draft upload only?
- What is the posting cadence for launch? e.g. 3 Reels/week, 2 carousels/week, 3 TikToks/week.
- What tools should be standard for composition: Canva, Figma, local scripts, ffmpeg?
- Are we comfortable using AI-generated backgrounds/mockups, or only real product media?
- Who approves content before publish?

---

## 9. Initial recommendation

For Paper Heirloom Company v1:

1. Build the **media/campaign folder + JSON metadata + approval checklist** first.
2. Use **manual posting or an approved scheduler** for the first launch cycle.
3. Build official API publishing only after we know which formats actually perform.
4. Treat Playwright as a backup for supervised internal upload assistance only, not a primary automation strategy.

