#!/usr/bin/env bash
#
# CurriculAI — local launcher.
# Runs the whole app on the professor's own machine: builds the React UI,
# then starts FastAPI which serves both the UI and the API on one port.
# The eCurricula upload opens a visible browser so the professor can log in
# and solve the captcha themselves.
#
# Usage:  ./run.sh
#
set -euo pipefail
cd "$(dirname "$0")"

# ── 1. Load config/.env ────────────────────────────────────────────────────────
if [ ! -f config/.env ]; then
  echo "ERROR: config/.env not found." >&2
  echo "       cp config/.env.example config/.env  and set GEMINI_API_KEY." >&2
  exit 1
fi
set -a; . config/.env; set +a

if [ -z "${GEMINI_API_KEY:-}" ] || [ "${GEMINI_API_KEY}" = "your_gemini_api_key_here" ]; then
  echo "ERROR: set a real GEMINI_API_KEY in config/.env" >&2
  exit 1
fi

# ── 2. Sync API keys (UI build key must match the server key) ──────────────────
if [ -z "${INTERNAL_API_KEY:-}" ] || [ "${INTERNAL_API_KEY}" = "change_me_to_a_strong_random_hex_string" ]; then
  INTERNAL_API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
  echo "Generated a local INTERNAL_API_KEY for this run."
fi
export INTERNAL_API_KEY
export VITE_API_KEY="$INTERNAL_API_KEY"

# ── 3. Python deps ─────────────────────────────────────────────────────────────
echo "Checking Python dependencies..."
python3 -m pip install -q -r requirements.txt
python3 -m playwright install chromium >/dev/null 2>&1 || \
  echo "WARN: 'playwright install chromium' failed — portal upload may not work."

# ── 4. Build the UI ────────────────────────────────────────────────────────────
echo "Building UI..."
( cd ui && npm install --no-audit --no-fund --silent && npm run build )

# ── 5. Start the server (serves UI + API on http://localhost:8000) ─────────────
echo ""
echo "──────────────────────────────────────────────────────────"
echo "  CurriculAI is running →  http://localhost:8000"
echo "  Press Ctrl+C to stop."
echo "──────────────────────────────────────────────────────────"
echo ""
exec python3 -m uvicorn server:app --host 127.0.0.1 --port 8000
