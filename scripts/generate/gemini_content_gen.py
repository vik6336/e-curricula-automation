"""Gemini API integration for generating educational content."""

import json
import os
import re
import sys
import time
from pathlib import Path

import google.generativeai as genai
import yaml
from dotenv import load_dotenv
from google.api_core.exceptions import DeadlineExceeded, ResourceExhausted, ServiceUnavailable

from .prompt_templates import (
    LM_REFERENCES_PROMPT,
    PDF_CONSOLIDATION_PROMPT,
    SLO_CONTENT_PROMPT,
)

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / "config" / ".env")


def load_settings() -> dict:
    settings_path = Path(__file__).parent.parent.parent / "config" / "settings.yaml"
    with open(settings_path) as f:
        return yaml.safe_load(f)


def init_gemini(api_key: str = None) -> genai.GenerativeModel:
    """Initialize the Gemini model."""
    key = api_key or os.environ.get("GEMINI_API_KEY")
    if not key:
        raise ValueError("GEMINI_API_KEY not set. Set it in config/.env or as environment variable.")
    genai.configure(api_key=key)
    settings = load_settings()
    return genai.GenerativeModel(settings["gemini"]["model"])


def _slide_to_text(slide: dict) -> str:
    """Extract meaningful text from any slide type for PDF consolidation."""
    stype = slide.get("slide_type", "content")
    title = slide.get("title", "")
    parts = [f"  [{stype.upper()}] {title}"]

    if stype == "what":
        if slide.get("definition"):
            parts.append(f"    Definition: {slide['definition']}")
        for c in slide.get("key_characteristics", []):
            parts.append(f"    - {c}")
        if slide.get("analogy"):
            parts.append(f"    Analogy: {slide['analogy']}")

    elif stype == "why":
        if slide.get("problem_statement"):
            parts.append(f"    Problem: {slide['problem_statement']}")
        for b in slide.get("bullet_points", []):
            parts.append(f"    - {b}")
        if slide.get("industry_context"):
            parts.append(f"    Industry: {slide['industry_context']}")

    elif stype == "how":
        for i, step in enumerate(slide.get("steps", []), 1):
            parts.append(f"    {i}. {step}")
        for tool in slide.get("tools", []):
            parts.append(f"    Tool: {tool.get('name', '')} — {tool.get('role', '')}")

    elif stype == "diagram":
        diagram = slide.get("diagram", {})
        if diagram.get("caption"):
            parts.append(f"    Diagram: {diagram['caption']}")
        for node in diagram.get("nodes", []):
            parts.append(f"    Component: {node.get('label', '')}")

    elif stype == "code":
        if slide.get("language"):
            parts.append(f"    Language: {slide['language']}")
        for exp in slide.get("explanation", []):
            parts.append(f"    {exp.get('line_ref', '')}: {exp.get('note', '')}")

    elif stype == "use_case":
        for key in ("company", "scenario", "solution", "outcome", "lesson"):
            val = slide.get(key, "")
            if val:
                parts.append(f"    {key.capitalize()}: {val}")

    elif stype == "quiz":
        if slide.get("question"):
            parts.append(f"    Quiz: {slide['question']}")
        if slide.get("challenge_task"):
            parts.append(f"    Challenge: {slide['challenge_task']}")

    elif stype == "summary":
        for b in slide.get("bullet_points", []):
            parts.append(f"    - {b}")
        if slide.get("call_to_action"):
            parts.append(f"    CTA: {slide['call_to_action']}")

    else:
        for b in slide.get("bullet_points", []):
            parts.append(f"    - {b}")

    return "\n".join(parts)


def _call_with_retry(model, prompt, generation_config, max_retries=12):
    """Call Gemini with exponential backoff on rate-limit, timeout, and empty responses."""
    delay = 30
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt, generation_config=generation_config)
            # Treat empty response as retryable
            if not response.text or not response.text.strip():
                raise ValueError("Empty response from Gemini")
            return response
        except (ResourceExhausted, ServiceUnavailable) as e:
            if attempt == max_retries - 1:
                raise
            match = re.search(r'retry in (\d+)', str(e), re.IGNORECASE) or \
                    re.search(r'seconds: (\d+)', str(e))
            wait = min(int(match.group(1)) + 5, 120) if match else delay
            print(f"  Rate limit hit — waiting {wait}s before retry {attempt + 1}/{max_retries}...",
                  file=sys.stderr)
            time.sleep(wait)
            delay = min(delay * 2, 120)
        except DeadlineExceeded:
            if attempt == max_retries - 1:
                raise
            wait = 15 * (attempt + 1)
            print(f"  Timeout (504) — waiting {wait}s before retry {attempt + 1}/{max_retries}...",
                  file=sys.stderr)
            time.sleep(wait)
        except ValueError:
            if attempt == max_retries - 1:
                raise
            wait = 20 * (attempt + 1)
            print(f"  Empty response — waiting {wait}s before retry {attempt + 1}/{max_retries}...",
                  file=sys.stderr)
            time.sleep(wait)


def generate_slo_content(
    model: genai.GenerativeModel,
    module_num: int,
    module_title: str,
    session_num: int,
    slo_num: int,
    slo_text: str,
    sro_text: str,
    source_text: str,
    syllabus_context: str,
) -> dict:
    """Generate presentation content for a single SLO using Gemini."""
    settings = load_settings()

    prompt = SLO_CONTENT_PROMPT.format(
        course_code=settings["course"]["code"],
        course_name=settings["course"]["name"],
        module_num=module_num,
        module_title=module_title,
        session_num=session_num,
        slo_num=slo_num,
        slo_text=slo_text,
        sro_text=sro_text,
        syllabus_context=syllabus_context,
        source_text=source_text[:50000],  # Limit source text to avoid token overflow
    )

    generation_config = genai.GenerationConfig(
        temperature=settings["gemini"]["temperature"],
        max_output_tokens=settings["gemini"]["max_output_tokens"],
        response_mime_type="application/json",
    )
    for parse_attempt in range(4):
        response = _call_with_retry(model, prompt, generation_config)
        try:
            content = json.loads(response.text)
            return content
        except json.JSONDecodeError:
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            try:
                content = json.loads(text)
                return content
            except json.JSONDecodeError:
                if parse_attempt == 3:
                    raise
                print(f"  Malformed JSON — retrying API call (attempt {parse_attempt + 1}/4)...",
                      file=sys.stderr)
                time.sleep(10)


def generate_pdf_content(
    model: genai.GenerativeModel,
    module_num: int,
    module_title: str,
    all_session_content: str,
) -> dict:
    """Generate consolidated PDF content for a module."""
    settings = load_settings()

    prompt = PDF_CONSOLIDATION_PROMPT.format(
        course_code=settings["course"]["code"],
        course_name=settings["course"]["name"],
        module_num=module_num,
        module_title=module_title,
        all_session_content=all_session_content,
    )

    generation_config = genai.GenerationConfig(
        temperature=settings["gemini"]["temperature"],
        max_output_tokens=16384,  # PDF needs more tokens than individual SLO slides
        response_mime_type="application/json",
    )
    for parse_attempt in range(4):
        response = _call_with_retry(model, prompt, generation_config)
        try:
            content = json.loads(response.text)
            return content
        except json.JSONDecodeError:
            text = response.text.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            try:
                content = json.loads(text)
                return content
            except json.JSONDecodeError:
                if parse_attempt == 3:
                    raise
                print(f"  Malformed JSON (PDF) — retrying API call (attempt {parse_attempt + 1}/4)...",
                      file=sys.stderr)
                time.sleep(10)


def generate_lm_references(
    model: genai.GenerativeModel,
    module_num: int,
    module_data: dict,
) -> dict:
    """Generate the references-only Learning Material content for a module.

    Faculty guidance (2026-07-03): the LM PDF should be a reference sheet —
    book references + curated links — not a full narrative document.
    """
    settings = load_settings()
    session_topics = "\n".join(
        f"  - Session {s['session']}: {s['slo_1']}" for s in module_data["sessions"]
    )
    prompt = LM_REFERENCES_PROMPT.format(
        course_code=settings["course"]["code"],
        course_name=settings["course"]["name"],
        module_num=module_num,
        module_title=module_data["title"],
        session_topics=session_topics,
    )
    generation_config = genai.GenerationConfig(
        temperature=0.2,  # low — reference accuracy matters more than creativity
        max_output_tokens=8192,
        response_mime_type="application/json",
    )
    for parse_attempt in range(3):
        response = _call_with_retry(model, prompt, generation_config)
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            if parse_attempt == 2:
                raise
            time.sleep(10)


def generate_module_content(
    model: genai.GenerativeModel,
    module_num: int,
    module_data: dict,
    source_texts: list[dict],
    syllabus_context: str,
    output_dir: str = None,
) -> dict:
    """Generate all content for a module (18 SLO presentations + PDF narrative).

    Args:
        model: Initialized Gemini model
        module_num: Module number (1-5)
        module_data: Parsed SLO/SRO data for this module
        source_texts: List of {"source": filename, "text": content} dicts
        syllabus_context: Relevant syllabus text for this module

    Returns:
        Dict with "slo_contents" (list of dicts) and "pdf_content" (consolidated)
    """
    settings = load_settings()
    delay = settings["gemini"]["rate_limit_delay_seconds"]
    module_title = module_data["title"]

    # Combine all source texts
    combined_source = "\n\n---\n\n".join(
        f"[Source: {s['source']}]\n{s['text']}" for s in source_texts
    ) if source_texts else "No specific source material provided. Use your knowledge of the topic."

    # Load any previously saved SLOs so we can resume after a crash
    checkpoint_path = None
    completed = set()
    slo_contents = []
    if output_dir:
        import os
        checkpoint_path = Path(output_dir) / f"unit_{module_num}" / "slo_checkpoint.json"
        if checkpoint_path.exists():
            with open(checkpoint_path) as f:
                slo_contents = json.load(f)
            completed = {(s["session_num"], s["slo_num"]) for s in slo_contents}
            print(f"  Resuming from checkpoint — {len(completed)} SLOs already done.",
                  file=sys.stderr)

    for session in module_data["sessions"]:
        session_num = session["session"]

        for slo_num in [1, 2]:
            if (session_num, slo_num) in completed:
                print(f"  Skipping Module {module_num}, Session {session_num}, SLO {slo_num} (cached)",
                      file=sys.stderr)
                continue

            slo_text = session[f"slo_{slo_num}"]
            sro_text = session[f"sro_{slo_num}"]

            print(f"  Generating Module {module_num}, Session {session_num}, SLO {slo_num}...",
                  file=sys.stderr)

            content = generate_slo_content(
                model=model,
                module_num=module_num,
                module_title=module_title,
                session_num=session_num,
                slo_num=slo_num,
                slo_text=slo_text,
                sro_text=sro_text,
                source_text=combined_source,
                syllabus_context=syllabus_context,
            )

            slo_contents.append({
                "module_num": module_num,
                "session_num": session_num,
                "slo_num": slo_num,
                "slo_text": slo_text,
                "content": content,
            })

            # Save checkpoint after every SLO so crashes don't lose progress
            if checkpoint_path:
                checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
                with open(checkpoint_path, "w") as f:
                    json.dump(slo_contents, f)

            time.sleep(delay)

    # Generate consolidated PDF content
    print(f"  Generating PDF narrative for Module {module_num}...", file=sys.stderr)
    all_content_text = ""
    for sc in slo_contents:
        # Keep per-SLO summary short to avoid truncation in PDF consolidation
        slo_summary = f"SLO: {sc['slo_text']}\n"
        for s in sc["content"].get("slides", []):
            slo_summary += _slide_to_text(s) + "\n"
        all_content_text += (
            f"\n### Session {sc['session_num']}, SLO {sc['slo_num']}\n{slo_summary}"
        )
    # Cap input to avoid PDF output truncation
    all_content_text = all_content_text[:30000]

    try:
        pdf_content = generate_pdf_content(
            model=model,
            module_num=module_num,
            module_title=module_title,
            all_session_content=all_content_text,
        )
    except Exception as e:
        print(f"  WARNING: PDF generation failed ({e}). Using placeholder.", file=sys.stderr)
        pdf_content = {
            "module_title": module_title,
            "introduction": f"Learning material for Module {module_num}: {module_title}.",
            "sessions": [
                {
                    "session_number": sc["session_num"],
                    "title": f"Session {sc['session_num']}",
                    "slo_1_title": "",
                    "slo_2_title": "",
                    "content": sc["slo_text"],
                }
                for sc in slo_contents[::2]  # one entry per session
            ],
            "conclusion": "Refer to the individual session PPTs for detailed content.",
        }

    return {
        "module_num": module_num,
        "module_title": module_title,
        "slo_contents": slo_contents,
        "pdf_content": pdf_content,
    }
