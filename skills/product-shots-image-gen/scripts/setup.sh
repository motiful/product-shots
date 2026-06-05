#!/usr/bin/env bash
# product-shots-image-gen — dependency installer.
#
# Detects Python 3 + pip, then installs the two runtime dependencies
# (requests, Pillow) if they are not already importable. Idempotent -
# safe to re-run.
#
# Usage:
#   bash scripts/setup.sh

set -euo pipefail

need_pip_install=false

# --- Python 3 ---
if ! command -v python3 > /dev/null 2>&1; then
    echo "ERROR: python3 not found in PATH. Install Python 3.9+ first." >&2
    exit 1
fi
PYV=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[image-gen] python3 found: $PYV"

# --- pip ---
if ! python3 -m pip --version > /dev/null 2>&1; then
    echo "ERROR: pip not available for python3. Try: python3 -m ensurepip --upgrade" >&2
    exit 1
fi

# --- requests ---
if python3 -c 'import requests' 2>/dev/null; then
    REQV=$(python3 -c 'import requests; print(requests.__version__)')
    echo "[image-gen] requests already installed: $REQV"
else
    echo "[image-gen] installing requests..."
    python3 -m pip install --quiet 'requests>=2.28'
    need_pip_install=true
fi

# --- Pillow ---
if python3 -c 'from PIL import Image' 2>/dev/null; then
    PILV=$(python3 -c 'from PIL import Image; print(Image.__version__)')
    echo "[image-gen] Pillow already installed: $PILV"
else
    echo "[image-gen] installing Pillow..."
    python3 -m pip install --quiet 'Pillow>=10.0'
    need_pip_install=true
fi

# --- API key + base URL reminders ---
if [ -z "${OMNIMAAS_API_KEY:-}" ] \
   && [ -z "${PRODUCT_SHOTS_IMAGEGEN_API_KEY:-}" ] \
   && [ -z "${RENDER_API_KEY:-}" ] \
   && [ -z "${CANVASFLOW_IMAGEGEN_API_KEY:-}" ] \
   && [ ! -f "$HOME/.product_shots_imagegen_api_key" ] \
   && [ ! -f "$HOME/.product_shots_render_api_key" ] \
   && [ ! -f "$HOME/.canvasflow_imagegen_api_key" ]; then
    echo ""
    echo "WARNING: No API key found for the image gateway."
    echo "  Preferred:"
    echo "    export OMNIMAAS_API_KEY='your-omnimaas-token'"
    echo "  Generic (any OpenAI-SDK-compatible gateway):"
    echo "    export PRODUCT_SHOTS_IMAGEGEN_API_KEY='your-token'"
    echo "  Or write the key to a chmod-600 file:"
    echo "    echo 'your-token' > ~/.product_shots_imagegen_api_key && chmod 600 ~/.product_shots_imagegen_api_key"
fi

if [ -z "${OMNIMAAS_BASE_URL:-}" ] \
   && [ -z "${PRODUCT_SHOTS_IMAGEGEN_BASE_URL:-}" ] \
   && [ -z "${RENDER_BASE_URL:-}" ] \
   && [ -z "${CANVASFLOW_IMAGEGEN_BASE_URL:-}" ] \
   && [ -z "${OMNIMAAS_API_KEY:-}" ]; then
    echo ""
    echo "WARNING: No base URL configured."
    echo "  When OMNIMAAS_API_KEY is set, the script defaults to https://api.omnimaas.com/v1."
    echo "  Otherwise set one of:"
    echo "    export OMNIMAAS_BASE_URL='https://api.omnimaas.com/v1'"
    echo "    export PRODUCT_SHOTS_IMAGEGEN_BASE_URL='https://your-gateway/v1'"
fi

echo ""
if $need_pip_install; then
    echo "[image-gen] setup complete. Dependencies installed."
else
    echo "[image-gen] setup complete. All dependencies already present."
fi
