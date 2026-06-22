"""Generate PPTX files from Gemini-generated content JSON."""

import json
import sys
from pathlib import Path

from .ppt_styles import (
    add_title_slide,
    add_what_slide,
    add_why_slide,
    add_how_slide,
    add_diagram_slide,
    add_code_slide,
    add_use_case_slide,
    add_quiz_slide,
    add_summary_slide,
    add_content_slide,
    create_presentation,
)

_SLIDE_BUILDERS = {
    "title":    add_title_slide,
    "what":     add_what_slide,
    "why":      add_why_slide,
    "how":      add_how_slide,
    "diagram":  add_diagram_slide,
    "code":     add_code_slide,
    "use_case": add_use_case_slide,
    "quiz":     add_quiz_slide,
    "summary":  add_summary_slide,
}


def create_slo_ppt(slo_data, module_num, session_num, slo_num, output_path):
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

    for slide_data in slo_data.get("slides", []):
        slide_type = slide_data.get("slide_type", "content")
        builder = _SLIDE_BUILDERS.get(slide_type, add_content_slide)
        builder(prs, slide_data, module_num, session_num, slo_num)

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output))
    return str(output)


def create_module_ppts(module_content, output_dir):
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
        slo_num     = slo_item["slo_num"]
        content     = slo_item["content"]

        filename    = f"session_{session_num}_slo_{slo_num}.pptx"
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
    if len(sys.argv) < 3:
        print("Usage: python -m scripts.build.create_ppt <content_json> <output_dir>",
              file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        module_content = json.load(f)

    files = create_module_ppts(module_content, sys.argv[2])
    print(json.dumps(files))
