"""Main orchestrator script — runs the full content generation pipeline."""

import json
import sys
import argparse
from pathlib import Path

import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.ingest.parse_slo_document import parse_slo_document, validate_parsed_data
from scripts.ingest.extract_text import extract_all_sources, extract_from_pdf
from scripts.generate.gemini_content_gen import init_gemini, generate_module_content
from scripts.build.create_ppt import create_module_ppts
from scripts.build.create_pdf import create_module_pdf


def load_settings():
    settings_path = Path(__file__).parent.parent / "config" / "settings.yaml"
    with open(settings_path) as f:
        return yaml.safe_load(f)


def run_pipeline(
    modules_to_process: list[int] = None,
    skip_upload: bool = True,
    slo_doc: str = None,
):
    """Run the full content generation pipeline.

    Args:
        modules_to_process: List of module numbers (1-5) to process. Default: all.
        skip_upload: If True, skip the portal upload step.
        slo_doc: Path to the SLO/SRO document to use. Default: the path in
            settings.yaml. Used by the server to inject a freshly uploaded file.
    """
    settings = load_settings()
    project_root = Path(__file__).parent.parent

    if modules_to_process is None:
        modules_to_process = list(range(1, settings["course"]["num_modules"] + 1))

    # --- Step 1: Parse SLO/SRO document ---
    print("=" * 60)
    print("Step 1: Parsing SLO/SRO document...")
    print("=" * 60)

    if slo_doc:
        slo_path = Path(slo_doc)
        if not slo_path.is_absolute():
            slo_path = project_root / slo_path
    else:
        slo_path = project_root / settings["paths"]["slo_document"]

    if not slo_path.exists():
        print(f"SLO document not found: {slo_path}")
        sys.exit(1)
    print(f"  Using SLO document: {slo_path}")
    slo_data = parse_slo_document(str(slo_path))
    errors = validate_parsed_data(slo_data)

    if errors:
        print("Validation errors in SLO document:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    print(f"  Parsed {len(slo_data)} modules successfully.")

    # --- Step 2: Extract source documents ---
    print("\n" + "=" * 60)
    print("Step 2: Extracting source documents...")
    print("=" * 60)

    source_dir = project_root / settings["paths"]["input_dir"] / "source_docs"
    source_texts = extract_all_sources(str(source_dir))

    for unit, texts in source_texts.items():
        total_chars = sum(len(t["text"]) for t in texts)
        print(f"  {unit}: {len(texts)} sources, {total_chars:,} chars")

    # Extract syllabus for context
    syllabus_path = project_root / settings["paths"]["syllabus"]
    syllabus_text = extract_from_pdf(str(syllabus_path))
    print(f"  Syllabus: {len(syllabus_text):,} chars")

    # --- Step 3: Generate content with Gemini ---
    print("\n" + "=" * 60)
    print("Step 3: Generating content with Gemini API...")
    print("=" * 60)

    model = init_gemini()
    output_dir = project_root / settings["paths"]["output_dir"] / settings["course"]["code"]

    for module_num in modules_to_process:
        module_key = f"module_{module_num}"
        if module_key not in slo_data:
            print(f"  Skipping module {module_num}: not found in SLO data")
            continue

        print(f"\n--- Module {module_num}: {slo_data[module_key]['title']} ---")

        # Get source texts for this unit
        unit_sources = source_texts.get(f"unit_{module_num}", [])

        # Generate all content (18 SLO presentations + PDF narrative)
        module_content = generate_module_content(
            model=model,
            module_num=module_num,
            module_data=slo_data[module_key],
            source_texts=unit_sources,
            syllabus_context=syllabus_text,
            output_dir=str(output_dir),
        )

        # Save raw content JSON
        content_json_path = output_dir / f"unit_{module_num}" / "content.json"
        content_json_path.parent.mkdir(parents=True, exist_ok=True)
        with open(content_json_path, "w") as f:
            json.dump(module_content, f, indent=2)
        print(f"  Saved content JSON: {content_json_path}")

        # --- Step 4: Generate PPT files (before PDF so they're always saved) ---
        print(f"\n  Generating PPT files for Module {module_num}...")
        ppt_files = create_module_ppts(module_content, str(output_dir))
        print(f"  Created {len(ppt_files)} PPT files")

        # Remove checkpoint now that PPTs are saved
        checkpoint = output_dir / f"unit_{module_num}" / "slo_checkpoint.json"
        if checkpoint.exists():
            checkpoint.unlink()

        # --- Step 5: Generate Learning Material PDF ---
        # Faculty guidance: LM should be a references sheet (books + links),
        # not a narrative document. Falls back to the narrative PDF on failure.
        print(f"\n  Generating Learning Material (references) for Module {module_num}...")
        pdf_path = output_dir / f"unit_{module_num}" / f"unit_{module_num}_learning_material.pdf"
        try:
            from scripts.build.create_pdf import create_references_pdf
            from scripts.generate.gemini_content_gen import generate_lm_references
            refs = generate_lm_references(model, module_num, slo_data[module_key])
            create_references_pdf(refs, module_num, str(pdf_path))
            print(f"  Created references PDF: {pdf_path}")
        except Exception as e:
            print(f"  WARNING: references PDF failed ({e}) — using narrative fallback.",
                  file=sys.stderr)
            try:
                create_module_pdf(module_content["pdf_content"], module_num, str(pdf_path))
                print(f"  Created PDF (narrative fallback): {pdf_path}")
            except Exception as e2:
                print(f"  WARNING: PDF creation failed ({e2}). PPTs are saved.", file=sys.stderr)

    # --- Step 6: Upload (optional) ---
    if not skip_upload:
        print("\n" + "=" * 60)
        print("Step 6: Uploading to e-curricula portal...")
        print("=" * 60)

        from scripts.upload.portal_upload import upload_all
        results = upload_all(str(output_dir), modules_to_process)
        print(json.dumps(results, indent=2))
    else:
        print("\n" + "=" * 60)
        print("Upload skipped. Run with --upload to upload to portal.")
        print("=" * 60)

    print("\nPipeline complete!")
    print(f"Output directory: {output_dir}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="E-Curricula Content Generation Pipeline")
    parser.add_argument(
        "--modules", "-m",
        type=int, nargs="+",
        help="Module numbers to process (default: all 1-5)",
    )
    parser.add_argument(
        "--upload",
        action="store_true",
        help="Upload generated files to the e-curricula portal",
    )
    parser.add_argument(
        "--slo-doc",
        help="Path to the SLO/SRO document (default: the one in settings.yaml)",
    )
    args = parser.parse_args()

    run_pipeline(
        modules_to_process=args.modules,
        skip_upload=not args.upload,
        slo_doc=args.slo_doc,
    )
