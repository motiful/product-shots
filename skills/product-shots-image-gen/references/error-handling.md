---
name: error-handling
description: Common failure modes when calling OmniMaaS / Cloubic gateway's image-generation endpoints (HTTP 401 / 429 / 524 / 5xx, malformed responses, content-policy refusals) and the diagnostic exit messages render emits. Documents the image-to-image retry policy (3 attempts with 1s/4s/16s exponential backoff on retryable 429/5xx/524/network errors; auth errors fail fast; text-to-image does not retry). Includes the API-key safety rule (errors never echo the key). Loaded by the parent SKILL.md's Execution Procedure Step 5 on non-200 responses and on response-shape anomalies.
---

# Error Handling

How `scripts/generate.py` reports failures and what the caller should do.

## Execution Procedure

```
handle_http_error(family: str, status_code: int, response_body: str) → exit

status == 401 or status == 403:
    msg = f"{family} API error {status}: bad/missing key. Check ~/.product_shots_imagegen_api_key (or env: OMNIMAAS_API_KEY / PRODUCT_SHOTS_IMAGEGEN_API_KEY)."
status == 429:
    msg = f"{family} API error 429: rate limit. Wait + retry, or check key quota in the upstream image gateway dashboard."
status == 524:
    msg = "Cloudflare 524 (upstream timeout). Reference image likely too large — auto-resize bypassed?"
status >= 500:
    msg = f"Upstream error {status}: {body[:300]}. Retry once after 30s."
else:
    msg = f"{family} API error {status}: {body[:300]}"

print(msg, file=stderr)
exit 1
```

```
classify_response_error(family: str, response_body: dict) → exit

if family == "openai":
    first = response_body["data"][0]
    if "b64_json" not in first and "url" not in first:
        exit 1 with "OpenAI response missing b64_json/url: OmniMaaS / Cloubic gateway format may have changed."

if family == "gemini":
    content = response_body["choices"][0]["message"]["content"]
    if no match for pattern "data:image/[^;]+;base64,([A-Za-z0-9+/=]+)" in content:
        exit 1 with f"No image data in Gemini response. First 400 chars:\n{content[:400]}"
        # likely: content-policy refusal or model degraded
```

## Failure Modes

| HTTP / Error | Cause | Skill behaviour | Recommended caller action |
|---|---|---|---|
| **HTTP 401 / 403** | Missing or invalid API key | exit 1 immediately — **never retried** | Verify `OMNIMAAS_API_KEY` env var (or `PRODUCT_SHOTS_IMAGEGEN_API_KEY` / `RENDER_API_KEY` / `CANVASFLOW_IMAGEGEN_API_KEY` fallbacks, or the file `~/.product_shots_imagegen_api_key`). Regenerate key on the upstream gateway if rotated. |
| **HTTP 429** | Rate limit / quota | image-to-image: retry up to 3 attempts with 1s/4s/16s backoff. Text-to-image: exit 1 with error body. | If still failing after retries, wait longer and check the per-request usage quota on the API key in the upstream gateway dashboard. |
| **HTTP 524** | Edge-proxy upstream timeout (almost always reference-image size) | image-to-image: retry up to 3 attempts with backoff. Text-to-image: exit 1 with raw HTML excerpt. | The skill auto-resizes references to ≤1024px / ≤1MB; a persistent 524 means either auto-resize was bypassed or the upstream is genuinely slow. |
| **HTTP 5xx (other)** | Upstream model error | image-to-image: retry up to 3 attempts with backoff. Text-to-image: exit 1 with response text. | If persistent after retries, log as a model-quality finding and try an alternate model. |
| **`No image data in Gemini response`** | Gemini returned text-only (e.g., content-policy refusal, or model degraded) | exit 1 with first 400 chars of response — **never retried** | Inspect the message — Gemini sometimes refuses prompts (faces, copyrighted entities). Adjust the prompt or use `gpt-image-2` as fallback. |
| **`OpenAI response missing b64_json/url`** | The image gateway returned a non-standard shape | exit 1 with full response dict — **never retried** | The upstream's response format may have changed; file an issue with the gateway provider. |
| **Connection / read timeout** | Network or upstream genuinely hung | image-to-image: retry up to 3 attempts with backoff. Text-to-image: unhandled `requests.Timeout` exception. | If persistent after retries, switch network (proxy?) or model. |

## The 524 → Resize → Retry Pattern

The skill **already auto-resizes** (see `references/reference-image-handling.md`), so this should be rare. If it happens anyway:

1. Check the input reference image size and dimensions.
2. If it bypassed auto-resize (e.g., 800KB but 2000px wide on one side), file an issue against `maybe_resize()` — the `max(im.size) <= 1024` check should have caught it.
3. Manual workaround: pre-resize with `sips -Z 1024 input.png --out resized.png` and pass `resized.png`.

## Retry Policy

Image-to-image calls hit retryable transient errors (network timeouts, 524 edge-proxy timeouts, 5xx, 429) noticeably more often than text-to-image. The skill builds in a bounded retry just for those calls:

- **3 attempts maximum** per call.
- **Exponential backoff** between attempts: 1s after attempt 1, 4s after attempt 2, 16s after attempt 3.
- **Retryable statuses**: HTTP 429, 500, 502, 503, 504, 524, plus connection errors and read timeouts.
- **Never retried**: HTTP 401 / 403 (auth failures fail fast), malformed response shapes, content-policy refusals.

Text-to-image calls do **not** retry — they go through a single attempt. The caller still owns the policy decision of whether to invoke the skill again with a different prompt or model.

After retries are exhausted (or for non-retryable errors), the skill exits with a non-zero status code and a diagnostic message printed to stderr. The caller can then decide whether to swap models, resize references, adjust the prompt, or surface the error to the user.

## API Key Safety

Errors never include the API key value in their output. If you see anything resembling `sk-...` in an error message, that's a bug — the request was logged before sanitisation. Filed under highest priority.
