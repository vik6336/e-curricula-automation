"""Shared configuration loading with active-course override.

settings.yaml holds the fixed structure (5 modules, 9 sessions, 2 SLOs each) and
defaults. The *active course* — its portal code and display name — is chosen by
the professor at runtime and stored in config/active_course.json, which
overrides settings["course"]["code"] / ["name"] for every reader.
"""

import json
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
SETTINGS_PATH = CONFIG_DIR / "settings.yaml"
ACTIVE_COURSE_PATH = CONFIG_DIR / "active_course.json"


def get_active_course() -> dict | None:
    """The course the professor is currently working on, or None if unset."""
    if ACTIVE_COURSE_PATH.exists():
        try:
            data = json.loads(ACTIVE_COURSE_PATH.read_text())
            if data.get("code") and data.get("name"):
                return {"code": str(data["code"]), "name": str(data["name"])}
        except Exception:
            pass
    return None


def set_active_course(code: str, name: str) -> dict:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    course = {"code": code.strip(), "name": name.strip()}
    ACTIVE_COURSE_PATH.write_text(json.dumps(course, indent=2))
    return course


def load_settings() -> dict:
    """settings.yaml, with course code/name overridden by the active course."""
    with open(SETTINGS_PATH) as f:
        settings = yaml.safe_load(f)
    active = get_active_course()
    if active:
        settings["course"]["code"] = active["code"]
        settings["course"]["name"] = active["name"]
    return settings


def course_code() -> str:
    return load_settings()["course"]["code"]
