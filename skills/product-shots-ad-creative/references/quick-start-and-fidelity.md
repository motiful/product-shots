---
name: quick-start-and-fidelity
description: Section 3 (Target Users — Small Business Owners and Marketers Are the Core), Section 4 (Quick Start — 7 Required Fields Before Generating, with the hub pre-fill rule), and Section 5 (Brand Name & User Copy Fidelity Rule — verbatim preservation of brand_name / slogan / cta / price). The pre-flight gate before the Core Workflow runs.
---

# Quick Start + User Copy Fidelity

The pre-flight gate that runs before the Core Workflow. Section 3 explains who the skill is built for. Section 4 lists the 7 required input fields and the conditional pre-fill rule (route to `product-shots` when fields are missing). Section 5 enforces verbatim preservation of every piece of copy the user supplied.

## Execution Procedure

```
preflight(user_request) → ready_brief | route_to_design_guide

# Section 4 — Quick Start
required_fields = {
    platform, format, ad_objective, industry,
    visual_assets, brand_kit, copy
}
copy = {brand_name, slogan, cta, price_or_offer}

missing = [f for f in required_fields if not provided(f)]
if missing:
    # Verbatim from skill body:
    # "If any of these are missing, use the product-shots router skill first."
    invoke product-shots(state) → fill missing fields
    return route_to_design_guide

# Section 5 — Brand Name & User Copy Fidelity
for phrase in copy.values():
    if phrase is None: continue
    register_protected_phrase(phrase)
    # Every variant produced downstream MUST contain this phrase verbatim
    # No paraphrase, no translation, no character substitution.
return ready_brief
```

## TOC

- [Section 3 — Target Users](#section-3--target-users)
- [Section 4 — Quick Start: 7 Required Fields Before Generating](#section-4--quick-start-7-required-fields-before-generating)
- [Section 5 — Brand Name & User Copy Fidelity Rule](#section-5--brand-name--user-copy-fidelity-rule)

## Section 3 — Target Users

Small business owners and marketers are the core. The skill is designed for users who need professional-grade output but supply amateur-grade input — typically a single product photo plus a vague intent. The skill compensates by encoding platform / industry / objective rules so the user does not need to know what TikTok's safe zone is or that Google Display rejects text overlays.

## Section 4 — Quick Start: 7 Required Fields Before Generating

Before generating any creative, collect these **7 required fields**:

1. **Platform** — Instagram / Facebook / TikTok / LinkedIn / Google (Display or Demand Gen) / YouTube / Pinterest / X (Twitter)
2. **Format** — Feed / Story / Reel / Carousel / Image Ad / Discovery / Shorts / Standard / In-Feed (per platform — see hard-constraints.md §Platform Dimensions)
3. **Ad Objective** — Brand Awareness / Promotion (Conversion) / Lead Generation / App Download / Engagement
4. **Industry** — Beauty/Fashion / Tech/SaaS / Food/Restaurant / Fitness / Wellness / Education / Real Estate / E-commerce/DTC / Home/Furniture (extensible)
5. **Visual Assets** — what the user has: product photo / model photo / logo only / none ("AI generates everything")
6. **Brand Kit** — colors / fonts / logo (optional but, if present, treated as hard constraints overriding industry defaults)
7. **Copy** — brand_name, slogan, cta_text, price_or_offer (whatever the user supplies — preserved verbatim per Section 5)

### Pre-fill Rule

> If any of these are missing, use hub first.

This is **conditional pre-fill, not hand-off**: `product-shots` fills the gaps via clarification questions, then control returns here. The 6-step Core Workflow (Section 6) runs entirely inside this skill.

### Interaction Pattern

When fields are missing, ask one focused question at a time using `<suggestion>` chips. Example:

```
"好的！我需要确认几个信息来生成最适合的创意：

1. 广告目标是什么？
   - 品牌认知（让更多人知道你的品牌）
   - 促销转化（推动立即购买，比如限时折扣）
   - 互动参与（鼓励评论/分享）

2. 你有什么素材？
   - 产品照片
   - 模特穿着 X 的照片
   - 只有 Logo
   - 什么都没有（AI 全部生成）

3. 品牌调性？
   - 专业运动（类似 Nike）
   - 潮流街头（类似 Yeezy）
   - 性价比实用（类似迪卡侬）

请选择，或者我可以用默认值先生成一版给你看看。"
```

Default values for fields the user explicitly defers on are listed in `references/failures-defaults-output.md §Defaults`.

## Section 5 — Brand Name & User Copy Fidelity Rule

Every brand name, slogan, CTA text, and price/offer the user specified MUST appear verbatim in every deliverable variant.

### MUST

- Reproduce `brand_name`, `slogan`, `cta_text`, `price_or_offer` exactly as the user supplied them (including casing, punctuation, full-width characters, emoji, currency symbols, and Chinese / non-Latin scripts).
- Treat user copy as **protected phrases** during prompt sanitation — wrap them in placeholders before applying the banned-words filter, restore them afterward (see `banned-words.md §Exception: User-Specified Content Passthrough`).
- Validate at the Self-Check Gate that every protected phrase is present in the deliverable. Any missing phrase = FAIL → regenerate.

### NEVER

- Never paraphrase, translate, or re-style user-supplied copy ("立即购买" never becomes "Shop Now" unless the user explicitly asks).
- Never substitute "similar" words ("¥899" never becomes "$129" or "899元" — the exact glyphs the user wrote must be preserved).
- Never trim user copy to fit char limits silently — surface the conflict to the user and ask which to truncate or split.
- Never include or invent a brand name the user did not specify. If `brand_name` is missing, leave it absent from the visual; do not hallucinate one.

### Why This Is MUST-level

User-supplied copy is the user's commercial asset. Paraphrasing it changes pricing, legal claims, brand voice, and trademarked phrasing — which is a higher-stakes failure mode than any visual error. Verbatim fidelity is also the defense against the AI image model "improving" the user's wording during prompt interpretation.

The Self-Check Gate (workflow Step 6) re-validates this rule explicitly via the `user_content_preserved` check.
