<!-- ============================================================ -->
<!-- TIER 1: ABOVE THE FOLD                                       -->
<!-- ============================================================ -->

<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset=".github/logo-dark.svg">
    <source media="(prefers-color-scheme: light)" srcset=".github/logo-light.svg">
    <img alt="product-shots" src=".github/logo-light.svg" width="320">
  </picture>

  <p><strong>One product photo in. Your full e-commerce visual stack out.</strong></p>
</div>

<div align="center">

[![License: MIT][license-shield]][license-url]
[![Skills: 7][skills-count-shield]][skills-anchor]
[![Agent Skills][skills-shield]][skills-url]
[![Built with Claude Code][cc-shield]][cc-url]
[![Status: alpha][status-shield]][status-anchor]

</div>

<div align="center">
  <a href="#features">Features</a> &middot;
  <a href="#quick-start">Quick Start</a> &middot;
  <a href="#install">Install</a> &middot;
  <a href="#usage">Usage</a> &middot;
  <a href="#skills">Skills</a>
</div>

<br>

> Drop one photo of your SKU into Claude Code. Get back the full visual stack a cross-border listing needs — Amazon-compliant main images, A+ detail-page modules, a 9-angle product shoot, platform-native ads, and social posts. All as open-source [Agent Skills](https://agentskills.io), no SaaS lock-in.

---

<!-- ============================================================ -->
<!-- TIER 2: SCAN QUICKLY                                          -->
<!-- ============================================================ -->

## The Problem

One SKU on a cross-border listing needs **a brutal visual pipeline**: 7 Amazon images at the right ratio and white-background spec, an A+ detail page with module-to-module consistency, a 9-angle shoot for clothing or bags, 4-8 ad-creative variants across TikTok / Meta / Google, and 6 social posts sized for 5 platforms — all rendering the *same* product without drifting into a different SKU.

Sellers either pay a closed SaaS to do it (and hand over their brand assets), hire a studio (slow, expensive, single-channel), or burn weeks tuning Midjourney prompts by hand. None of those compose with the rest of an AI-first workflow.

`product-shots` ships the same pipeline as **open-source Claude Code skills**. It runs in your terminal, lives next to your other skills, never sees your assets outside your machine, and outputs files you fully own.

**If you sell on Amazon, Shopify, TikTok Shop, or an independent storefront — and you want the visual production layer to be code you control, not a subscription — you're the target user.**

## Features

Seven skills, ordered by what carries the most weight in a real listing. The first three are where the wow lives; the rest are platform breadth, then the infrastructure that makes the whole thing portable.

| Skill | What you get |
|---|---|
| [`product-shots-multi-angle`](#skills) | One reference photo → **9 consistent angles** of the same SKU. Fourteen identity anchors (material, stitching, hardware, color cast, proportions, …) lock so the front-3/4 shot and the back shot read as the same product. The killer feature for fashion, bags, and jewelry. |
| [`product-shots-detail-page`](#skills) | A full **A+ Content** detail-page module set — hero band, feature grid, lifestyle scene, size/spec callouts — with cross-image consistency anchors so the SKU doesn't morph between modules. |
| [`product-shots-main-image`](#skills) | Marketplace-compliant **main + secondary images**. Amazon's 9 mandatory rules (pure white, ≥85% frame fill, no text/logos/watermarks, even studio light, apparel exceptions) are encoded as prompt fields — compliance is decided before the model renders, not patched after. Auto-adapts to category-specific norms (electronics vs apparel vs grocery). |
| [`product-shots-ad-creative`](#skills) | Platform-native ad creatives across **8 platforms × 21 formats** — Meta, TikTok, Google Display, Google Demand Gen, YouTube, Pinterest, LinkedIn, X. Per-platform style profiles, banned-words filter, user copy preserved verbatim. |
| [`product-shots-social-post`](#skills) | Feed / Story / Reel / Carousel posts with industry-aware DNA (beauty vs hardware vs apparel each get a different visual language) and a 14-point self-check before render. |
| [`product-shots-image-gen`](#skills) | The shared **image-gen engine**. One API surface across OpenAI `gpt-image-2`, Gemini `gemini-3-pro-image-preview`, and Flux families. OmniMaaS-gateway compatible — endpoint is one env var, no vendor lock-in. Auto-resizes oversize references, retries with sane backoff. |
| [`product-shots`](#skills) | The **intent router** at the front door. Four-stage clarification (≤4 rounds), Visual DNA injection (platform × industry), then dispatch to one of the five business skills above. Stops underspecified prompts from wasting a render. |

> **What product-shots is not:** a generic design tool. It does not write copy, build landing pages, or replace a brand designer. Every skill is sharpened around one job in a cross-border seller's daily workflow.

## Quick Start

Three distinct operations. Pick the one that matches your job:

```text
"Generate Amazon listing photos for this product"            — 7 marketplace-compliant images (main + 6 secondary), white-background spec auto-applied.
"Get a 9-angle shoot of this dress"                          — front / back / side / 3/4 / detail / hanger / lifestyle, 14 identity anchors locked.
"Make cross-platform ad creatives for this product"          — Meta + TikTok + Google + YouTube variants in correct ratios, platform style applied, copy preserved verbatim.
```

Each command lands in `product-shots`, which clarifies what's missing (≤4 rounds), injects platform × industry Visual DNA, and dispatches to the right specialist. The render goes through the shared `product-shots-image-gen` engine.

## Install

```bash
npx skills add motiful/product-shots
```

This registers the seven skills with whichever Agent Skills harness you're running (Claude Code, Codex, Cursor, Windsurf, GitHub Copilot).

**Configure the image backend** — `product-shots-image-gen` reads two env vars. Point them at any OpenAI-SDK-compatible image gateway (an aggregator that exposes `gpt-image-2` + `gemini-3-pro-image-preview`):

```bash
export PRODUCT_SHOTS_IMAGEGEN_BASE_URL='https://your-image-gateway.example.com/v1'
export PRODUCT_SHOTS_IMAGEGEN_API_KEY='sk-...'   # or write to ~/.product_shots_imagegen_api_key (chmod 600)
```

API keys are only ever sent via the `Authorization` header — never logged, never written to stdout.

**Manual registration** (clone + symlink — only if you don't want the `npx skills` route):

```bash
git clone https://github.com/motiful/product-shots ~/skills/product-shots

# Register only in the harness roots you actually use.
ln -sfn ~/skills/product-shots/skills/product-shots          ~/.claude/skills/product-shots
ln -sfn ~/skills/product-shots/skills/product-shots-image-gen       ~/.claude/skills/product-shots-image-gen
ln -sfn ~/skills/product-shots/skills/product-shots-main-image   ~/.claude/skills/product-shots-main-image
ln -sfn ~/skills/product-shots/skills/product-shots-detail-page  ~/.claude/skills/product-shots-detail-page
ln -sfn ~/skills/product-shots/skills/product-shots-multi-angle  ~/.claude/skills/product-shots-multi-angle
ln -sfn ~/skills/product-shots/skills/product-shots-ad-creative  ~/.claude/skills/product-shots-ad-creative
ln -sfn ~/skills/product-shots/skills/product-shots-social-post  ~/.claude/skills/product-shots-social-post
```

## Usage

Two real scenarios, end-to-end. Both start from a single reference photo in your working directory.

### Scenario A — Smart coffee machine, full Amazon listing

```text
> here's the product shot: ./refs/coffee-machine-v2.jpg
> give me the full Amazon listing — main, 6 secondaries, A+ page, and 4 ad creatives
```

What `product-shots` will do, in order:

1. **Clarify** category (small kitchen appliance), market (US Amazon), brand voice in ≤4 questions.
2. **Dispatch** `product-shots-main-image` → 7 compliant images, white-background, ≥85% fill, no overlay text on the main.
3. **Dispatch** `product-shots-detail-page` → A+ hero band + 3 feature modules + 1 lifestyle scene + 1 spec callout. Same SKU across all six modules — no model drift.
4. **Dispatch** `product-shots-ad-creative` → 4 variants targeting Meta feed, Meta story, TikTok feed, YouTube short. Each in correct ratio with platform-native styling.

Output: 18 PNGs, organized by skill, ready to upload.

### Scenario B — Women's dress, 9-angle shoot + social rollout

```text
> reference: ./refs/dress-floral.jpg
> i need a 9-angle shoot + 5 Instagram posts (3 feed, 2 story)
```

What happens:

1. `product-shots` confirms this is apparel (triggers `product-shots-multi-angle`'s 14-anchor fashion profile, not the generic one).
2. `product-shots-multi-angle` locks fabric drape, neckline, sleeve length, pattern repeat, color cast, model proportions, lighting — then renders front / 3/4 front / side / 3/4 back / back / detail (closeup) / on-hanger / lifestyle (indoor) / lifestyle (outdoor).
3. `product-shots-social-post` applies the apparel industry DNA preset (editorial, warm-neutral palette, type hierarchy) and produces 3 feed posts (1:1) + 2 stories (9:16), all derived from the same 9-angle set so the campaign reads as one shoot.

Output: 14 images. The dress is recognizably the *same* dress in every frame — that's the whole point.

## Gallery

Real outputs from `product-shots-*` skills against the OmniMaaS gateway (`gemini-3-pro-image-preview`). Two products, two complete pipelines.

### Smart espresso machine — full Amazon listing flow

<table>
<tr>
<td><img src="assets/gallery/coffee-machine/01-main-image.jpeg" width="220"><br><sub><code>product-shots-main-image</code> · Amazon main</sub></td>
<td><img src="assets/gallery/coffee-machine/02-detail-page-hero.jpeg" width="220"><br><sub><code>product-shots-detail-page</code> · A+ hero band</sub></td>
<td><img src="assets/gallery/coffee-machine/03-detail-page-feature.jpeg" width="220"><br><sub><code>product-shots-detail-page</code> · feature module</sub></td>
</tr>
<tr>
<td><img src="assets/gallery/coffee-machine/04-ad-creative.jpeg" width="220"><br><sub><code>product-shots-ad-creative</code> · TikTok UGC</sub></td>
<td><img src="assets/gallery/coffee-machine/05-social-post.jpeg" width="220"><br><sub><code>product-shots-social-post</code> · IG feed</sub></td>
<td></td>
</tr>
</table>

### Floral midi dress — 9-angle identity-locked shoot

The killer demo for `product-shots-multi-angle`: same model, same dress, nine canonical angles, fourteen identity anchors held constant.

<table>
<tr>
<td><img src="assets/gallery/dress/01-front.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/02-three-quarter-front.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/03-side.jpeg" width="180"></td>
</tr>
<tr>
<td><img src="assets/gallery/dress/04-three-quarter-back.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/05-back.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/06-detail.jpeg" width="180"></td>
</tr>
<tr>
<td><img src="assets/gallery/dress/07-on-hanger.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/08-lifestyle-indoor.jpeg" width="180"></td>
<td><img src="assets/gallery/dress/09-lifestyle-outdoor.jpeg" width="180"></td>
</tr>
</table>

<sub>Every image above is generated end-to-end by <code>product-shots</code> skills via <code>product-shots-image-gen</code> + the OmniMaaS gateway. No manual prompt tuning beyond what the skill emits.</sub>

---

<!-- ============================================================ -->
<!-- TIER 3: SUPPORTING CONTENT                                    -->
<!-- ============================================================ -->

## Skills

Each skill is self-contained — a `SKILL.md` plus its `references/` and `scripts/`. Trigger phrases below are the canonical ones; `product-shots` accepts free-form natural-language variants and routes on intent, not exact wording.

| Skill | Trigger | Primary deliverable |
|---|---|---|
| `product-shots` | (front door for all of the below) | Clarified, DNA-injected dispatch to one specialist |
| `product-shots-multi-angle` | "9-angle shoot of this product" | 9 identity-locked angles of one SKU |
| `product-shots-detail-page` | "build an A+ detail page for this" | Hero + feature + lifestyle + spec modules, consistent SKU |
| `product-shots-main-image` | "Amazon main image for this product" | Marketplace-compliant main + secondary set |
| `product-shots-ad-creative` | "cross-platform ad creatives" | 8-platform × 21-format ad variants |
| `product-shots-social-post` | "Instagram / TikTok posts for this" | Feed / Story / Reel / Carousel with industry DNA |
| `product-shots-image-gen` | (called by the others; or `"just generate: <prompt>"`) | Raw image generation across OpenAI / Gemini / Flux |

## How It Works

`product-shots` pushes the hard work — compliance rules, platform specs, identity anchors, banned-words — **upstream of the model** as prompt fields. Compliance becomes a verifiable intermediate artifact, not a post-hoc check. Model selection is part of the skill, not the user's job: CJK long headlines and photoreal UGC route to `gpt-image-2`; golden-hour lifestyle photoreal routes to `gemini-3-pro-image-preview`. The `product-shots-image-gen` engine handles the actual dispatch, retries oversized references, and falls back across providers when one returns an empty image.

→ [Architecture notes](docs/how-it-works.md)

## What's Inside

```text
skills/
  product-shots/              — intent router (4-stage clarification + Visual DNA injection)
  product-shots-image-gen/    — unified image-gen engine (OpenAI / Gemini / Flux)
  product-shots-main-image/   — Amazon 9 MUST rules + category profiles
  product-shots-detail-page/  — A+ module set with cross-image consistency anchors
  product-shots-multi-angle/  — 14-anchor identity lock, fashion/bags/jewelry profiles
  product-shots-ad-creative/  — 8 platforms × 21 formats, banned-words filter
  product-shots-social-post/  — 7-industry DNA presets, 14-point self-check
.github/          — logo (light/dark), repo metadata
LICENSE           — MIT
```

## Compatibility

Built against the [Agent Skills](https://agentskills.io) protocol — runs in Claude Code, Codex, Cursor, Windsurf, and GitHub Copilot. No MCP server, no custom runtime, no proprietary client. The image backend is endpoint-agnostic: any OpenAI-SDK-compatible gateway works.

## Contributing

Issues and PRs welcome. Each skill is independently reviewable — open a PR scoped to one skill at a time. For new platform support (e.g., a new ad network in `product-shots-ad-creative`), include the platform's spec source and a sample render.

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
  <sub><i>Submitted to UCWS Singapore Hackathon 2026. Built by <a href="https://github.com/motiful">motiful</a>.</i></sub>
</div>

<!-- Reference-style link definitions -->
[license-shield]: https://img.shields.io/badge/License-MIT-green.svg
[license-url]: LICENSE
[skills-count-shield]: https://img.shields.io/badge/skills-7-success.svg
[skills-anchor]: #skills
[skills-shield]: https://img.shields.io/badge/Agent%20Skills-compatible-DA7857?logo=anthropic
[skills-url]: https://agentskills.io
[cc-shield]: https://img.shields.io/badge/Built%20with-Claude%20Code-DA7857?logo=anthropic
[cc-url]: https://claude.ai/code
[status-shield]: https://img.shields.io/badge/status-alpha-orange.svg
[status-anchor]: #the-problem
