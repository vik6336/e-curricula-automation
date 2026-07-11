"""Quick check: is the GEMINI_API_KEY in config/.env valid and working?

Usage:  python3 test_gemini_key.py
"""
import re
import sys
from pathlib import Path


def main() -> int:
    env_path = Path(__file__).parent / "config" / ".env"
    if not env_path.exists():
        print("❌ config/.env not found")
        return 1

    m = re.search(r"GEMINI_API_KEY\s*=\s*(\S+)", env_path.read_text())
    key = m.group(1).strip() if m else ""
    if not key or key == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY is not set in config/.env")
        return 1

    print(f"Key format: {len(key)} chars, starts with '{key[:4]}' "
          f"({'looks like an AI Studio key' if key.startswith('AIza') else 'does NOT look like an AIza… key'})")

    try:
        import google.generativeai as genai
    except ImportError:
        print("❌ google-generativeai not installed (pip install -r requirements.txt)")
        return 1

    genai.configure(api_key=key)

    # Use the same model the pipeline uses (from settings.yaml).
    import yaml
    settings = yaml.safe_load((Path(__file__).parent / "config" / "settings.yaml").read_text())
    model_name = settings["gemini"]["model"]
    print(f"Testing model: {model_name} …")

    try:
        model = genai.GenerativeModel(model_name)
        resp = model.generate_content("Reply with exactly: OK")
        print(f"✅ WORKING — Gemini replied: {resp.text.strip()!r}")
        return 0
    except Exception as e:
        msg = str(e)
        print(f"❌ FAILED: {type(e).__name__}")
        if "401" in msg or "Unauthenticated" in msg or "API key" in msg:
            print("   → The API key is invalid/wrong type. Get one at https://aistudio.google.com/app/apikey")
        elif "404" in msg or "not found" in msg.lower():
            print(f"   → The model '{model_name}' was not found. Try 'gemini-1.5-flash' in config/settings.yaml.")
        elif "429" in msg or "quota" in msg.lower() or "ResourceExhausted" in msg:
            print("   → Key is valid but rate-limited/over quota. Try again shortly.")
        print(f"   Details: {msg[:300]}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
