"""Generate MCQ / short / long question banks per session using Gemini.

Produces output/<course>/unit_N/questions.json plus a formatted review PDF
(unit_N_question_bank.pdf) for faculty approval before portal auto-fill.

Usage: python -m scripts.generate.question_gen --modules 1 2
"""

import argparse
import json
import sys
import time
from pathlib import Path

from scripts.ingest.parse_slo_document import parse_slo_document
from scripts.generate.gemini_content_gen import (
    _call_with_retry,
    init_gemini,
    load_settings,
)
from scripts.generate.prompt_templates import QUESTION_GEN_PROMPT

import google.generativeai as genai

PROJECT_ROOT = Path(__file__).parent.parent.parent

ALLOWED_VERBS = {
    "Choose", "Count", "Cite", "Define", "Describe", "Distinguish", "Draw",
    "Find", "Group", "Identify", "Know", "Label", "List", "Listen", "Locate",
    "Match", "Memorize", "Name", "Outline", "Quote", "Read", "Repeat",
    "Recall", "Recite", "Relate", "Review", "Recognize", "Record",
    "Reproduce", "Select", "State", "Sequence", "Show", "Sort", "Tell",
    "Underline", "Write",
}


def _parse_json_response(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)


def _sanitize(qset: dict) -> dict:
    """Clamp fields to what the portal form accepts."""
    for q in qset.get("mcqs", []):
        q["correct_option"] = min(max(int(q.get("correct_option", 1)), 1), 4)
        q["blooms_level"] = min(max(int(q.get("blooms_level", 1)), 1), 6)
        if q.get("taxonomy_verb") not in ALLOWED_VERBS:
            q["taxonomy_verb"] = "Identify"
        q["program_outcomes"] = [p for p in q.get("program_outcomes", [1]) if p in (1, 2, 3)] or [1]
        q["options"] = (q.get("options", []) + ["", "", "", ""])[:4]
    for kind in ("short_questions", "long_questions"):
        for q in qset.get(kind, []):
            q["level"] = min(max(int(q.get("level", 1)), 1), 6)
            if q.get("taxonomy_verb") not in ALLOWED_VERBS:
                q["taxonomy_verb"] = "Describe"
            q["program_outcomes"] = [p for p in q.get("program_outcomes", [1]) if p in (1, 2, 3)] or [1]
    return qset


def generate_module_questions(model, module_num: int, module_data: dict,
                              output_dir: Path) -> dict:
    settings = load_settings()
    delay = settings["gemini"]["rate_limit_delay_seconds"]

    unit_dir = output_dir / f"unit_{module_num}"
    unit_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = unit_dir / "questions_checkpoint.json"

    sessions_out = []
    done_sessions = set()
    if checkpoint_path.exists():
        sessions_out = json.loads(checkpoint_path.read_text())
        done_sessions = {s["session"] for s in sessions_out}
        print(f"  Resuming questions from checkpoint — {len(done_sessions)} sessions done",
              file=sys.stderr)

    generation_config = genai.GenerationConfig(
        temperature=settings["gemini"]["temperature"],
        max_output_tokens=8192,
        response_mime_type="application/json",
    )

    for session in module_data["sessions"]:
        s_num = session["session"]
        if s_num in done_sessions:
            continue
        print(f"  Generating questions — Module {module_num}, Session {s_num}...")

        prompt = QUESTION_GEN_PROMPT.format(
            course_code=settings["course"]["code"],
            course_name=settings["course"]["name"],
            module_num=module_num,
            module_title=module_data["title"],
            session_num=s_num,
            slo_1=session["slo_1"],
            slo_2=session["slo_2"],
        )

        for attempt in range(3):
            response = _call_with_retry(model, prompt, generation_config)
            try:
                qset = _sanitize(_parse_json_response(response.text))
                break
            except (json.JSONDecodeError, ValueError, KeyError):
                if attempt == 2:
                    raise
                print(f"  Malformed question JSON — retrying ({attempt + 1}/3)...",
                      file=sys.stderr)
                time.sleep(10)

        sessions_out.append({"session": s_num, **qset})
        checkpoint_path.write_text(json.dumps(sessions_out))
        time.sleep(delay)

    result = {
        "module_num": module_num,
        "module_title": module_data["title"],
        "sessions": sorted(sessions_out, key=lambda s: s["session"]),
    }
    out_path = unit_dir / "questions.json"
    out_path.write_text(json.dumps(result, indent=2))
    checkpoint_path.unlink(missing_ok=True)
    print(f"  Saved question bank: {out_path}")
    return result


def main():
    parser = argparse.ArgumentParser(description="Question bank generator")
    parser.add_argument("--modules", "-m", type=int, nargs="+",
                        help="Module numbers (default: all)")
    args = parser.parse_args()

    settings = load_settings()
    modules = args.modules or list(range(1, settings["course"]["num_modules"] + 1))

    slo_path = PROJECT_ROOT / settings["paths"]["slo_document"]
    slo_data = parse_slo_document(str(slo_path))
    output_dir = PROJECT_ROOT / settings["paths"]["output_dir"] / settings["course"]["code"]

    model = init_gemini()

    for module_num in modules:
        key = f"module_{module_num}"
        if key not in slo_data:
            print(f"  Skipping module {module_num}: not in SLO data")
            continue
        print(f"\n=== Question bank: Module {module_num} — {slo_data[key]['title']} ===")
        result = generate_module_questions(model, module_num, slo_data[key], output_dir)

        # Build the faculty review PDF
        from scripts.build.create_question_pdf import create_question_pdf
        pdf_path = output_dir / f"unit_{module_num}" / f"unit_{module_num}_question_bank.pdf"
        create_question_pdf(result, str(pdf_path))
        print(f"  Review PDF: {pdf_path}")

    print("\nQuestion generation complete!")


if __name__ == "__main__":
    main()
