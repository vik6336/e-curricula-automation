"""Generate PPTX files from Gemini-generated content JSON."""

import json
import sys
from pathlib import Path

from .ppt_styles import (
    add_content_slide,
    add_summary_slide,
    add_title_slide,
    create_presentation,
)


def create_slo_ppt(
    slo_data: dict,
    module_num: int,
    session_num: int,
    slo_num: int,
    output_path: str,
) -> str:
    """Create a PPTX file for a single SLO.

    Args:
        slo_data: Gemini-generated content with "slides" list
        module_num: Module number (1-5)
        session_num: Session number (1-9)
        slo_num: SLO number (1-2)
        output_path: Path to save the PPTX file

    Returns:
        Path to the created file
    """
    prs = create_presentation()
    slides = slo_data.get("slides", [])
    slo_title = slo_data.get("slo_title", f"SLO {slo_num}")

    for slide_data in slides:
        slide_type = slide_data.get("slide_type", "content")
        title = slide_data.get("title", "")
        subtitle = slide_data.get("subtitle", "")
        bullets = slide_data.get("bullet_points", [])
        notes = slide_data.get("speaker_notes", "")

        if slide_type == "title":
            add_title_slide(
                prs, title or slo_title, subtitle or slo_data.get("slo_title", ""),
                module_num, session_num, slo_num,
            )
        elif slide_type == "summary":
            add_summary_slide(
                prs, bullets, notes,
                module_num, session_num, slo_num,
            )
        else:
            add_content_slide(
                prs, title, bullets, notes,
                module_num, session_num, slo_num,
            )

    # Save
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    return str(output)


def create_module_ppts(module_content: dict, output_dir: str) -> list[str]:
    """Create all 18 PPTX files for a module.

    Args:
        module_content: Dict with "slo_contents" list from generate_module_content()
        output_dir: Base output directory

    Returns:
        List of created file paths
    """
    module_num = module_content["module_num"]
    created_files = []

    for slo_item in module_content["slo_contents"]:
        session_num = slo_item["session_num"]
        slo_num = slo_item["slo_num"]
        content = slo_item["content"]

        filename = f"session_{session_num}_slo_{slo_num}.pptx"
        output_path = Path(output_dir) / f"unit_{module_num}" / "ppts" / filename

        path = create_slo_ppt(
            slo_data=content,
            module_num=module_num,
            session_num=session_num,
            slo_num=slo_num,
            output_path=str(output_path),
        )
        created_files.append(path)
        print(f"  Created: {path}", file=sys.stderr)

    return created_files


if __name__ == "__main__":
    """Usage: python -m scripts.build.create_ppt <content_json_path> <output_dir>"""
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.build.create_ppt <content_json> <output_dir>", file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        module_content = json.load(f)

    files = create_module_ppts(module_content, sys.argv[2])
    print(json.dumps(files))
