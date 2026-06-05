#!/usr/bin/env python3
"""product-shots-image-gen — unified image-generation engine.

Dispatches to OpenAI-compatible image endpoints or Gemini chat-multimodal
endpoints based on the requested model. Returns a single saved file on
success.

Primary entry point: OmniMaaS / Cloubic image gateway
    base URL: https://api.omnimaas.com/v1
    docs:
        - https://docs.cloubic.com/docs/zh-CN/image-generation/image-openai
        - https://docs.cloubic.com/docs/zh-CN/image-generation/image-gemini

The gateway is OpenAI-SDK-compatible and unifies access to GPT image 2
(`gpt-image-2`) and Gemini Nano Banana family
(`gemini-3-pro-image-preview`, etc.) behind one auth token.

Fallback: any other OpenAI-SDK-compatible image gateway (set
PRODUCT_SHOTS_IMAGEGEN_BASE_URL / PRODUCT_SHOTS_IMAGEGEN_API_KEY,
or the shorter RENDER_BASE_URL / RENDER_API_KEY) — also keeps
backward compatibility with the legacy CANVASFLOW_IMAGEGEN_* env vars.

Usage:
    # Text-to-image (Gemini, recommended default — Nano Banana Pro)
    python generate.py --prompt "a red apple on wood" \\
                       --model gemini-3-pro-image-preview

    # With aspect ratio
    python generate.py --prompt "Instagram post hero shot" \\
                       --model gemini-3-pro-image-preview \\
                       --aspect-ratio 1:1

    # Image-to-image (reference image is auto-resized if > 1024px or > 1MB)
    python generate.py --prompt "change background to a beach" \\
                       --model gemini-3-pro-image-preview \\
                       --reference-image ./apple.png

    # OpenAI family (different code path under the hood)
    python generate.py --prompt "a cat" --model gpt-image-2 --aspect-ratio 3:2

Configuration:
    OMNIMAAS_API_KEY                — preferred. Token for the OmniMaaS / Cloubic gateway.
    OMNIMAAS_BASE_URL               — optional. Defaults to https://api.omnimaas.com/v1.

    PRODUCT_SHOTS_IMAGEGEN_API_KEY  — canonical generic. Any OpenAI-SDK-compatible image gateway.
    PRODUCT_SHOTS_IMAGEGEN_BASE_URL — canonical generic. The /v1 base URL of that gateway.

    RENDER_API_KEY                  — alias for PRODUCT_SHOTS_IMAGEGEN_API_KEY (shorter name).
    RENDER_BASE_URL                 — alias for PRODUCT_SHOTS_IMAGEGEN_BASE_URL.

    CANVASFLOW_IMAGEGEN_API_KEY     — legacy fallback (for migrated installs).
    CANVASFLOW_IMAGEGEN_BASE_URL    — legacy fallback.

API keys never reach logs or stdout. They are loaded from environment
variables or from ~/.product_shots_imagegen_api_key (chmod 600) and
passed only via the Authorization header.
"""

import argparse
import base64
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import requests
from PIL import Image

# --- Configuration -----------------------------------------------------------

OMNIMAAS_DEFAULT_BASE_URL = "https://api.omnimaas.com/v1"
API_KEY_PATH = Path.home() / ".product_shots_imagegen_api_key"
COMPAT_API_KEY_PATH = Path.home() / ".product_shots_render_api_key"
LEGACY_API_KEY_PATH = Path.home() / ".canvasflow_imagegen_api_key"

TIMEOUT = 240
REF_MAX_DIM = 1024     # auto-resize ceiling (edge-proxy 524 mitigation)
REF_MAX_BYTES = 1024 * 1024

# Image-to-image retry policy (i2i calls spike 5xx/524 more often).
I2I_TIMEOUT = (30, 180)             # (connect, read) seconds
I2I_MAX_ATTEMPTS = 3
I2I_BACKOFF_SCHEDULE = (1, 4, 16)
I2I_RETRY_STATUSES = {429, 500, 502, 503, 504, 524}


def post_with_i2i_retry(url, *, headers, **kwargs):
    """POST with retry tuned for image-to-image calls.

    Retries on: connection errors, read timeouts, HTTP 5xx, HTTP 429.
    Does NOT retry on: HTTP 4xx (other than 429), incl. 401/403 auth errors.
    """
    kwargs.setdefault("timeout", I2I_TIMEOUT)
    last_exc = None
    for attempt in range(1, I2I_MAX_ATTEMPTS + 1):
        reason = None
        try:
            r = requests.post(url, headers=headers, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as exc:
            last_exc = exc
            reason = f"{type(exc).__name__}: {exc}"
        else:
            if r.status_code not in I2I_RETRY_STATUSES:
                return r
            reason = f"HTTP {r.status_code}"
            last_exc = None

        if attempt < I2I_MAX_ATTEMPTS:
            sleep_s = I2I_BACKOFF_SCHEDULE[attempt - 1]
            print(
                f"[image-gen] i2i retry: attempt {attempt}/{I2I_MAX_ATTEMPTS} "
                f"failed ({reason}); sleeping {sleep_s}s before retry",
                file=sys.stderr,
            )
            time.sleep(sleep_s)
        else:
            print(
                f"[image-gen] i2i retry: attempt {attempt}/{I2I_MAX_ATTEMPTS} "
                f"failed ({reason}); giving up",
                file=sys.stderr,
            )

    if last_exc is not None:
        raise last_exc
    return r


OPENAI_MODELS = {"gpt-image-1", "gpt-image-2", "dall-e-3"}
GEMINI_MODELS = {
    "gemini-3-pro-image-preview",
    "gemini-3.1-flash-image-preview",
    "gemini-2.5-flash-image-preview",
    "gemini-2.5-flash-image",
}

OPENAI_SIZE_BY_RATIO = {
    "1:1": "1024x1024",
    "3:2": "1536x1024", "4:3": "1536x1024", "16:9": "1536x1024",
    "2:3": "1024x1536", "3:4": "1024x1536", "9:16": "1024x1536",
}


def load_api_key() -> tuple[str, str]:
    """Resolve (api_key, source_label). Priority:

    1. OMNIMAAS_API_KEY env var (preferred — OmniMaaS / Cloubic gateway)
    2. PRODUCT_SHOTS_IMAGEGEN_API_KEY env var (canonical generic)
    3. RENDER_API_KEY env var (short alias)
    4. CANVASFLOW_IMAGEGEN_API_KEY env var (legacy)
    5. ~/.product_shots_imagegen_api_key file
    6. ~/.product_shots_render_api_key file (compat with earlier ship)
    7. ~/.canvasflow_imagegen_api_key file (legacy)
    """
    env_order = (
        "OMNIMAAS_API_KEY",
        "PRODUCT_SHOTS_IMAGEGEN_API_KEY",
        "RENDER_API_KEY",
        "CANVASFLOW_IMAGEGEN_API_KEY",
    )
    for env_name in env_order:
        v = os.environ.get(env_name)
        if v:
            return v.strip(), env_name
    for path in (API_KEY_PATH, COMPAT_API_KEY_PATH, LEGACY_API_KEY_PATH):
        if path.exists():
            return path.read_text().strip(), str(path)
    sys.exit(
        "No API key. Set one of:\n"
        "  OMNIMAAS_API_KEY                (preferred — OmniMaaS / Cloubic image gateway)\n"
        "  PRODUCT_SHOTS_IMAGEGEN_API_KEY  (any OpenAI-SDK-compatible image gateway)\n"
        "  RENDER_API_KEY                  (short alias)\n"
        "  CANVASFLOW_IMAGEGEN_API_KEY     (legacy)\n"
        "Or write the key to ~/.product_shots_imagegen_api_key (chmod 600)."
    )


def load_base_url() -> tuple[str, str]:
    """Resolve (base_url, source_label). Priority:

    1. OMNIMAAS_BASE_URL env var
    2. PRODUCT_SHOTS_IMAGEGEN_BASE_URL env var (canonical generic)
    3. RENDER_BASE_URL env var (short alias)
    4. CANVASFLOW_IMAGEGEN_BASE_URL env var (legacy)
    5. OmniMaaS default base URL when only OMNIMAAS_API_KEY is set
    """
    omnimaas_url = os.environ.get("OMNIMAAS_BASE_URL")
    if omnimaas_url:
        return omnimaas_url.rstrip("/"), "OMNIMAAS_BASE_URL"

    ps_url = os.environ.get("PRODUCT_SHOTS_IMAGEGEN_BASE_URL")
    if ps_url:
        return ps_url.rstrip("/"), "PRODUCT_SHOTS_IMAGEGEN_BASE_URL"

    render_url = os.environ.get("RENDER_BASE_URL")
    if render_url:
        return render_url.rstrip("/"), "RENDER_BASE_URL"

    legacy_url = os.environ.get("CANVASFLOW_IMAGEGEN_BASE_URL")
    if legacy_url:
        return legacy_url.rstrip("/"), "CANVASFLOW_IMAGEGEN_BASE_URL"

    # When only OMNIMAAS_API_KEY is set without a base URL, default to OmniMaaS.
    if os.environ.get("OMNIMAAS_API_KEY"):
        return OMNIMAAS_DEFAULT_BASE_URL, "OMNIMAAS_DEFAULT_BASE_URL"

    sys.exit(
        "No image gateway base URL configured. Set one of:\n"
        "  OMNIMAAS_BASE_URL                (defaults to https://api.omnimaas.com/v1 when OMNIMAAS_API_KEY is set)\n"
        "  PRODUCT_SHOTS_IMAGEGEN_BASE_URL  (any OpenAI-SDK-compatible image gateway)\n"
        "  RENDER_BASE_URL                  (short alias)\n"
        "  CANVASFLOW_IMAGEGEN_BASE_URL     (legacy)"
    )


def model_family(model: str) -> str:
    if model in OPENAI_MODELS:
        return "openai"
    if model in GEMINI_MODELS:
        return "gemini"
    sys.exit(
        f"Unknown model: {model}\n"
        f"  OpenAI: {sorted(OPENAI_MODELS)}\n"
        f"  Gemini: {sorted(GEMINI_MODELS)}"
    )


def maybe_resize(path: Path) -> Path:
    """Resize reference image if exceeds REF_MAX_DIM or REF_MAX_BYTES."""
    if path.stat().st_size <= REF_MAX_BYTES:
        with Image.open(path) as im:
            if max(im.size) <= REF_MAX_DIM:
                return path
    with Image.open(path) as im:
        im.thumbnail((REF_MAX_DIM, REF_MAX_DIM), Image.LANCZOS)
        suffix = ".jpg" if im.mode == "RGB" else path.suffix
        tmp = Path(tempfile.mktemp(prefix="ref_", suffix=suffix))
        save_kwargs = {"optimize": True}
        if suffix == ".jpg":
            save_kwargs["quality"] = 88
            im.convert("RGB").save(tmp, "JPEG", **save_kwargs)
        else:
            im.save(tmp, **save_kwargs)
    orig_kb = path.stat().st_size // 1024
    new_kb = tmp.stat().st_size // 1024
    print(f"[image-gen] auto-resized {path.name}: {orig_kb}KB -> {new_kb}KB ({REF_MAX_DIM}px max)")
    return tmp


def encode_data_url(path: Path) -> str:
    ext = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(ext, "png")
    b64 = base64.b64encode(path.read_bytes()).decode()
    return f"data:image/{mime};base64,{b64}"


def compose_prompt(prompt: str, negative: str, aspect: str, family: str) -> str:
    """Build the actual text sent to the model.

    Aspect ratio: for OpenAI it goes into `size` param; for Gemini we embed in
    prompt since the chat-completions API has no size parameter.
    """
    parts = [prompt]
    if aspect and family == "gemini":
        parts.append(f"(aspect ratio: {aspect})")
    if negative:
        parts.append(f"Avoid: {negative}")
    return " ".join(parts)


def generate_openai(prompt, model, size, n, ref_images, api_key, base_url) -> tuple[bytes, dict]:
    headers = {"Authorization": f"Bearer {api_key}"}
    if ref_images:
        url = f"{base_url}/images/edits"
        data = {"model": model, "prompt": prompt, "n": str(n), "size": size}
        files = [
            ("image[]", (p.name, p.read_bytes(), f"image/{p.suffix.lstrip('.') or 'png'}"))
            for p in ref_images
        ]
        r = post_with_i2i_retry(url, headers=headers, data=data, files=files)
    else:
        url = f"{base_url}/images/generations"
        payload = {"model": model, "prompt": prompt, "n": n, "size": size}
        r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)

    if r.status_code != 200:
        sys.exit(f"OpenAI API error {r.status_code}: {r.text[:600]}")

    body = r.json()
    first = body["data"][0]
    if "b64_json" in first:
        return base64.b64decode(first["b64_json"]), body.get("usage", {})
    if "url" in first:
        img = requests.get(first["url"], timeout=TIMEOUT)
        img.raise_for_status()
        return img.content, body.get("usage", {})
    sys.exit(f"OpenAI response missing b64_json/url: {body}")


def generate_gemini(prompt, model, ref_images, api_key, base_url) -> tuple[bytes, dict]:
    content = [{"type": "text", "text": prompt}]
    for img in ref_images:
        content.append(
            {"type": "image_url", "image_url": {"url": encode_data_url(img)}}
        )
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": content}],
    }
    headers = {"Authorization": f"Bearer {api_key}"}
    url = f"{base_url}/chat/completions"
    if ref_images:
        r = post_with_i2i_retry(url, headers=headers, json=payload)
    else:
        r = requests.post(url, headers=headers, json=payload, timeout=TIMEOUT)
    if r.status_code != 200:
        sys.exit(f"Gemini API error {r.status_code}: {r.text[:600]}")

    body = r.json()
    msg = body["choices"][0]["message"]["content"]
    m = re.search(r"data:image/[^;]+;base64,([A-Za-z0-9+/=]+)", msg)
    if not m:
        sys.exit(f"No image data in Gemini response. First 400 chars:\n{msg[:400]}")
    return base64.b64decode(m.group(1)), body.get("usage", {})


def main():
    p = argparse.ArgumentParser(
        description="product-shots-image-gen — unified image generator (OpenAI + Gemini families via OmniMaaS or any compatible gateway)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--prompt", required=True)
    p.add_argument("--model", required=True, help="Model name (see --help for list)")
    p.add_argument(
        "--aspect-ratio",
        choices=sorted(OPENAI_SIZE_BY_RATIO.keys()),
        default=None,
        help="Aspect ratio. OpenAI: maps to size param. Gemini: embedded in prompt.",
    )
    p.add_argument(
        "--size",
        default=None,
        help="OpenAI only. Explicit pixel size (e.g., 1024x1024). Overrides --aspect-ratio.",
    )
    p.add_argument(
        "--negative-prompt",
        default=None,
        help="Concepts to avoid. Appended to prompt as 'Avoid: ...' (no API has true negative_prompt).",
    )
    p.add_argument("--n", type=int, default=1, help="OpenAI only. Number of images (default: 1)")
    p.add_argument(
        "--reference-image",
        action="append",
        default=[],
        metavar="PATH",
        help="Reference image for image-to-image. Auto-resized to <=1024px. Repeatable.",
    )
    p.add_argument(
        "--output",
        default=None,
        help="Output path (default: ./output-<timestamp>.<ext>)",
    )
    args = p.parse_args()

    api_key, key_source  = load_api_key()
    base_url, url_source = load_base_url()
    family               = model_family(args.model)

    # Resolve effective size for OpenAI
    if family == "openai":
        if args.size:
            size = args.size
        elif args.aspect_ratio:
            size = OPENAI_SIZE_BY_RATIO[args.aspect_ratio]
        else:
            size = "1024x1024"
    else:
        size = None

    # Process reference images (auto-resize)
    ref_paths = []
    for raw in args.reference_image:
        p_in = Path(raw).expanduser()
        if not p_in.is_file():
            sys.exit(f"Reference image not found: {p_in}")
        ref_paths.append(maybe_resize(p_in))

    final_prompt = compose_prompt(args.prompt, args.negative_prompt, args.aspect_ratio, family)

    print(
        f"[image-gen] gateway={url_source} key_source={key_source} "
        f"model={args.model} family={family} "
        f"refs={len(ref_paths)} aspect={args.aspect_ratio or 'default'}"
    )
    print(f"[image-gen] prompt='{final_prompt[:120]}'")
    t0 = time.time()

    if family == "openai":
        img_bytes, usage = generate_openai(
            final_prompt, args.model, size, args.n, ref_paths, api_key, base_url
        )
        ext = "png"
    else:
        img_bytes, usage = generate_gemini(
            final_prompt, args.model, ref_paths, api_key, base_url
        )
        ext = "jpeg"

    elapsed = time.time() - t0
    out = Path(args.output).expanduser() if args.output else Path(f"output-{int(time.time())}.{ext}")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(img_bytes)

    tokens = usage.get("total_tokens", "?")
    print(
        f"[image-gen] OK {elapsed:.1f}s | {len(img_bytes):,} bytes | "
        f"tokens={tokens} | {out}"
    )


if __name__ == "__main__":
    main()
