"""Parse the SLO/SRO Word document into structured JSON."""

import json
import re
import sys
from pathlib import Path

from docx import Document


def parse_slo_document(docx_path: str) -> dict:
    """Parse SLO/SRO Word document into structured data.

    Expected format (paragraph-based):
        Module N – Title
        Session N
        SLO 1: ...
        SLO 2: ...
        SRO 1: ...
        SRO 2: ...

    Returns dict keyed by module number with sessions list.
    """
    doc = Document(docx_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    modules = {}
    current_module = None
    current_session = None

    for text in paragraphs:
        # Match module header: "Module N – Title" or "Module N - Title"
        module_match = re.match(r"Module\s+(\d+)\s*[–\-]\s*(.+)", text, re.IGNORECASE)
        if module_match:
            module_num = int(module_match.group(1))
            module_title = module_match.group(2).strip()
            current_module = {
                "title": module_title,
                "sessions": [],
            }
            modules[f"module_{module_num}"] = current_module
            current_session = None
            continue

        # Match session header: "Session N"
        session_match = re.match(r"Session\s+(\d+)", text, re.IGNORECASE)
        if session_match and current_module is not None:
            session_num = int(session_match.group(1))
            current_session = {
                "session": session_num,
                "slo_1": "",
                "slo_2": "",
                "sro_1": "",
                "sro_2": "",
            }
            current_module["sessions"].append(current_session)
            continue

        if current_session is None:
            continue

        # Match SLO/SRO entries
        slo1_match = re.match(r"SLO\s*1\s*:\s*(.+)", text, re.IGNORECASE)
        if slo1_match:
            current_session["slo_1"] = slo1_match.group(1).strip()
            continue

        slo2_match = re.match(r"SLO\s*2\s*:\s*(.+)", text, re.IGNORECASE)
        if slo2_match:
            current_session["slo_2"] = slo2_match.group(1).strip()
            continue

        sro1_match = re.match(r"SRO\s*1\s*:\s*(.+)", text, re.IGNORECASE)
        if sro1_match:
            current_session["sro_1"] = sro1_match.group(1).strip()
            continue

        sro2_match = re.match(r"SRO\s*2\s*:\s*(.+)", text, re.IGNORECASE)
        if sro2_match:
            current_session["sro_2"] = sro2_match.group(1).strip()
            continue

    return modules


def validate_parsed_data(modules: dict) -> list[str]:
    """Validate that all expected data was parsed correctly."""
    errors = []
    for i in range(1, 6):
        key = f"module_{i}"
        if key not in modules:
            errors.append(f"Missing {key}")
            continue
        module = modules[key]
        if len(module["sessions"]) != 9:
            errors.append(f"{key}: expected 9 sessions, got {len(module['sessions'])}")
        for session in module["sessions"]:
            for field in ["slo_1", "slo_2", "sro_1", "sro_2"]:
                if not session.get(field):
                    errors.append(f"{key} session {session['session']}: missing {field}")
    return errors


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Default path
        docx_path = Path(__file__).parent.parent.parent / "input" / "SLO_SRO_Containers_Cloud_DevOps.docx"
    else:
        docx_path = sys.argv[1]

    modules = parse_slo_document(str(docx_path))
    errors = validate_parsed_data(modules)

    if errors:
        print("Validation errors:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)

    print(json.dumps(modules, indent=2))
