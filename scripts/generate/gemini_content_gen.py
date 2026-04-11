"""Gemini API integration for generating educational content."""

import json
import os
import sys
import time
from pathlib import Path

import google.generativeai as genai
import yaml
from dotenv import load_dotenv

from .prompt_templates import PDF_CONSOLIDATION_PROMPT, SLO_CONTENT_PROMPT

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

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=settings["gemini"]["temperature"],
            max_output_tokens=settings["gemini"]["max_output_tokens"],
            response_mime_type="application/json",
        ),
    )

    try:
        content = json.loads(response.text)
    except json.JSONDecodeError:
        # Try to extract JSON from the response
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        content = json.loads(text)

    return content


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

    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            temperature=settings["gemini"]["temperature"],
            max_output_tokens=settings["gemini"]["max_output_tokens"],
            response_mime_type="application/json",
        ),
    )

    try:
        content = json.loads(response.text)
    except json.JSONDecodeError:
        text = response.text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
        content = json.loads(text)

    return content


def generate_module_content(
    model: genai.GenerativeModel,
    module_num: int,
    module_data: dict,
    source_texts: list[dict],
    syllabus_context: str,
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

    slo_contents = []

    for session in module_data["sessions"]:
        session_num = session["session"]

        for slo_num in [1, 2]:
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

            time.sleep(delay)

    # Generate consolidated PDF content
    print(f"  Generating PDF narrative for Module {module_num}...", file=sys.stderr)
    all_content_text = ""
    for sc in slo_contents:
        slides_text = "\n".join(
            f"  - {s.get('title', '')}: {'; '.join(s.get('bullet_points', []))}"
            for s in sc["content"].get("slides", [])
        )
        all_content_text += (
            f"\n### Session {sc['session_num']}, SLO {sc['slo_num']}: {sc['slo_text']}\n"
            f"{slides_text}\n"
        )

    pdf_content = generate_pdf_content(
        model=model,
        module_num=module_num,
        module_title=module_title,
        all_session_content=all_content_text,
    )

    return {
        "module_num": module_num,
        "module_title": module_title,
        "slo_contents": slo_contents,
        "pdf_content": pdf_content,
    }
