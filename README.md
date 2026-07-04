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
python3 content-pipeline/scripts/run-paperheirloom-content-pipeline.py <action>
```

See `content-pipeline/SPEC.md`. Phase 1 is implemented: JSON media cards, review HTML, CLI actions, and stub connectors (no live API calls).

Run the end-to-end test (no live APIs):

```bash
python3 content-pipeline/scripts/e2e-test.py
```

### Platform API docs (for connector implementation)

**Instagram (Meta)**

- [Content Publishing](https://developers.facebook.com/docs/instagram-platform/content-publishing)
- [IG User Media](https://developers.facebook.com/docs/instagram-platform/instagram-graph-api/reference/ig-user/media/)
- [Resumable video uploads](https://developers.facebook.com/docs/instagram-platform/content-publishing/resumable-uploads/)

**Facebook Page (Meta)**

- [Pages API overview](https://developers.facebook.com/docs/pages-api/)
- [Getting Started](https://developers.facebook.com/docs/pages-api/getting-started)
- [Posts](https://developers.facebook.com/docs/pages-api/posts/)
- [Page feed reference](https://developers.facebook.com/docs/graph-api/reference/page/feed/)
- [Page photos reference](https://developers.facebook.com/docs/graph-api/reference/page/photos/)
- [Video API publishing](https://developers.facebook.com/docs/video-api/guides/publishing/)

**TikTok**

- [Content Posting API](https://developers.tiktok.com/products/content-posting-api/)
- [Get Started — Direct Post](https://developers.tiktok.com/doc/content-posting-api-get-started)
- [Get Started — Upload (draft)](https://developers.tiktok.com/doc/content-posting-api-get-started-upload-content)
- [Direct Post API reference](https://developers.tiktok.com/doc/content-posting-api-reference-direct-post)
- [API scopes](https://developers.tiktok.com/doc/tiktok-api-scopes)
- [OAuth token management](https://developers.tiktok.com/doc/oauth-user-access-token-management)
