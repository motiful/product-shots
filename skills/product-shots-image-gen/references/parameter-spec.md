---
name: parameter-spec
description: Single source of truth for every CLI flag and Python keyword argument exposed by render — name, type, default, applicability per family, valid range. Includes the aspect-ratio → OpenAI pixel-size lookup table and the per-caller recommendation table. Loaded by the parent SKILL.md's Execution Procedure Step 0 (argument validation) and Step 3 (effective prompt composition).
---

# Parameter Spec

Every flag of `scripts/generate.py`. The validation function below is the authority — if argparse and this spec disagree, this spec wins.

## Execution Procedure

```
validate_args(args) → effective_args | exit

require args.prompt is non-empty AND len(args.prompt) ≤ 4000
require args.model is in OPENAI_MODELS ∪ GEMINI_MODELS
    # delegate to model_family() in references/model-selection.md

if args.aspect_ratio:
    assert args.aspect_ratio in {"1:1", "16:9", "9:16", "4:3", "3:4", "3:2", "2:3"}

family = model_family(args.model)

if family == "openai":
    args.size = args.size OR OPENAI_SIZE_BY_RATIO[args.aspect_ratio] OR "1024x1024"
    assert args.n >= 1
elif family == "gemini":
    if args.n != 1:
        warn "Gemini ignores --n; loop in caller for multiples. Forcing n=1."
        args.n = 1
    if args.size:
        warn "Gemini ignores --size; aspect ratio is embedded in prompt."

for path in args.reference_image:
    assert path.exists() AND path.is_file()

return args
```

```
lookup_caller_defaults(caller_skill: str, surface: str) → flag_dict

# Recommended invocation flags per skills caller / surface combination.
# Returns a dict of flag → value that can be passed straight to generate.py.
# See "Family-Specific Defaults" table below.
```

## CLI Flags

| Flag | Required | Type | Default | Applicability | Notes |
|---|---|---|---|---|---|
| `--prompt` | **yes** | string | — | both families | The text instruction. ≤4000 chars practical limit. |
| `--model` | **yes** | enum | — | both families | One of the supported model names; see `references/model-selection.md`. Family is auto-derived. |
| `--aspect-ratio` | no | enum | none | both families | `1:1` / `16:9` / `9:16` / `4:3` / `3:4` / `3:2` / `2:3`. OpenAI: mapped to `size`. Gemini: appended to prompt. |
| `--size` | no | string `WxH` | `1024x1024` | **openai only** | Explicit pixel dimensions. Overrides `--aspect-ratio`. Ignored for Gemini. |
| `--negative-prompt` | no | string | none | both families | Concepts to avoid. Appended to prompt as `Avoid: …`. No API has a true `negative_prompt` field. |
| `--n` | no | int ≥1 | 1 | **openai only** | Number of variations per call. Gemini = always 1; loop in caller for multiples. |
| `--reference-image` | no | path (repeatable) | [] | both families | File path(s). Auto-resized to ≤1024px / ≤1MB. Up to 9 for Gemini per their docs; OpenAI accepts multiple `image[]` entries for `/v1/images/edits`. |
| `--output` | no | path | `./output-<ts>.<ext>` | both families | Where to save. Extension auto-determined (PNG for OpenAI, JPEG for Gemini) when default is used. Parent dirs are created. |

## Aspect Ratio → OpenAI Size Mapping

```
1:1                 → 1024x1024
3:2 / 4:3 / 16:9    → 1536x1024   (landscape)
2:3 / 3:4 / 9:16    → 1024x1536   (portrait)
```

This mapping is intentionally coarse — gpt-image-2 only supports a small set of pixel sizes. For exact pixel dimensions, use `--size` directly.

## Family-Specific Defaults

When called by other product-shots specialists:

| Caller / use case | Recommended flags |
|---|---|
| `product-shots-main-image` (Amazon main image, single SKU) | `--model gpt-image-2 --aspect-ratio 1:1` |
| `product-shots-main-image` (secondary image with reference) | `--model gemini-3-pro-image-preview --aspect-ratio 1:1 --reference-image <main.jpg>` |
| `product-shots-detail-page` (A+ Hero Banner 21:9) | `--model gemini-3-pro-image-preview --aspect-ratio 16:9 --reference-image <main.jpg>` |
| `product-shots-detail-page` (A+ standard module 3:2) | `--model gemini-3-pro-image-preview --aspect-ratio 3:2 --reference-image <main.jpg>` |
| `product-shots-multi-angle` (9-angle model series) | `--model gemini-3-pro-image-preview --reference-image <model.jpg>` |
| `product-shots-ad-creative` photoreal | `--model gpt-image-2 --aspect-ratio <platform-specific>` |
| `product-shots-social-post` (Carousel slide) | `--model gemini-3-pro-image-preview --aspect-ratio 4:5` |

## API Key + Base URL

Resolved at runtime in this priority order:

**API key:**
1. `OMNIMAAS_API_KEY` env var (preferred — OmniMaaS / Cloubic gateway)
2. `PRODUCT_SHOTS_IMAGEGEN_API_KEY` env var (canonical generic, any OpenAI-SDK-compatible gateway)
3. `RENDER_API_KEY` env var (short alias)
4. `CANVASFLOW_IMAGEGEN_API_KEY` env var (legacy fallback)
5. `~/.product_shots_imagegen_api_key` file (chmod 600 recommended)
6. `~/.product_shots_render_api_key` file (compat with earlier ship)
7. `~/.canvasflow_imagegen_api_key` file (legacy fallback)

**Base URL:**
1. `OMNIMAAS_BASE_URL` env var
2. `PRODUCT_SHOTS_IMAGEGEN_BASE_URL` env var (canonical generic)
3. `RENDER_BASE_URL` env var (short alias)
4. `CANVASFLOW_IMAGEGEN_BASE_URL` env var (legacy fallback)
5. Default `https://api.omnimaas.com/v1` when `OMNIMAAS_API_KEY` is set without an explicit base URL

Both API key and base URL are **never echoed**, never written to logs. The skill exits with a clear message if either is missing.
