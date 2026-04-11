"""Portal configuration — URLs, selectors, and navigation helpers."""

import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")

# Portal URLs
PORTAL_URL = os.environ.get("PORTAL_URL", "https://dld.srmist.edu.in/etecurricula")
LOGIN_URL = f"{PORTAL_URL}/login" if "/login" not in PORTAL_URL else PORTAL_URL

# Credentials
PORTAL_USERNAME = os.environ.get("PORTAL_USERNAME", "")
PORTAL_PASSWORD = os.environ.get("PORTAL_PASSWORD", "")

# CSS Selectors (these may need to be updated based on actual portal DOM)
# These are initial best-guesses that should be verified against the live portal
SELECTORS = {
    # Login page
    "username_input": 'input[name="username"], input[type="text"]',
    "password_input": 'input[name="password"], input[type="password"]',
    "login_button": 'button[type="submit"], input[type="submit"]',

    # Course navigation
    "course_link": 'a:has-text("{course_code}")',

    # PPTx Source section
    "pptx_section": 'text=PPTx Source',
    "unit_dropdown": 'select:near(:text("Choose Unit"))',

    # Upload elements (per session/SLO row)
    # The portal shows rows like: Session 1 | SLO 1 | CLICK TO UPLOAD | ...
    "upload_button": 'text=CLICK TO UPLOAD',
    "file_input": 'input[type="file"]',

    # Learning Material section
    "learning_material_section": 'text=Learning Material',
}

# Timeouts (ms)
NAVIGATION_TIMEOUT = 30000
UPLOAD_TIMEOUT = 60000
