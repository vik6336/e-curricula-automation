"""Generate Learning Material PDF from consolidated module content."""

import json
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
)

# Colors matching the PPT scheme
COLOR_PRIMARY = colors.HexColor("#1B365D")
COLOR_ACCENT = colors.HexColor("#C8102E")
COLOR_DARK_TEXT = colors.HexColor("#333333")
COLOR_LIGHT_BG = colors.HexColor("#F5F5F5")


def _get_styles():
    """Create custom paragraph styles."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        "CoverTitle",
        parent=styles["Title"],
        fontSize=28,
        textColor=COLOR_PRIMARY,
        spaceAfter=20,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontSize=16,
        textColor=COLOR_ACCENT,
        spaceAfter=12,
        fontName="Helvetica",
    ))

    styles.add(ParagraphStyle(
        "ModuleTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=COLOR_PRIMARY,
        spaceBefore=30,
        spaceAfter=15,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        "SessionTitle",
        parent=styles["Heading2"],
        fontSize=16,
        textColor=COLOR_ACCENT,
        spaceBefore=20,
        spaceAfter=10,
        fontName="Helvetica-Bold",
    ))

    styles.add(ParagraphStyle(
        "SLOTitle",
        parent=styles["Heading3"],
        fontSize=13,
        textColor=COLOR_PRIMARY,
        spaceBefore=12,
        spaceAfter=6,
        fontName="Helvetica-BoldOblique",
    ))

    # Override the built-in BodyText style
    styles["BodyText"].fontSize = 11
    styles["BodyText"].textColor = COLOR_DARK_TEXT
    styles["BodyText"].spaceBefore = 4
    styles["BodyText"].spaceAfter = 8
    styles["BodyText"].fontName = "Helvetica"
    styles["BodyText"].leading = 16

    styles.add(ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
        fontName="Helvetica",
    ))

    return styles


def create_module_pdf(pdf_content: dict, module_num: int, output_path: str) -> str:
    """Create a Learning Material PDF for a module.

    Args:
        pdf_content: Consolidated content from Gemini (generate_pdf_content output)
        module_num: Module number (1-5)
        output_path: Path to save the PDF

    Returns:
        Path to the created file
    """
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=inch,
        rightMargin=inch,
        topMargin=inch,
        bottomMargin=inch,
    )

    styles = _get_styles()
    story = []

    # --- Cover Page ---
    story.append(Spacer(1, 2 * inch))
    story.append(Paragraph("21CSE597T", styles["CoverSubtitle"]))
    story.append(Paragraph("Containers and Cloud DevOps", styles["CoverTitle"]))
    story.append(Spacer(1, 0.5 * inch))

    module_title = pdf_content.get("module_title", f"Module {module_num}")
    story.append(Paragraph(f"Module {module_num}: {module_title}", styles["ModuleTitle"]))
    story.append(Spacer(1, 0.3 * inch))
    story.append(Paragraph("Learning Material", styles["CoverSubtitle"]))
    story.append(Spacer(1, inch))
    story.append(Paragraph(
        "SRM Institute of Science and Technology",
        styles["BodyText"],
    ))
    story.append(PageBreak())

    # --- Table of Contents ---
    story.append(Paragraph("Table of Contents", styles["ModuleTitle"]))
    story.append(Spacer(1, 0.3 * inch))

    sessions = pdf_content.get("sessions", [])
    for session in sessions:
        sn = session.get("session_number", "")
        title = session.get("title", f"Session {sn}")
        story.append(Paragraph(
            f"Session {sn}: {title}",
            styles["BodyText"],
        ))
    story.append(PageBreak())

    # --- Introduction ---
    intro = pdf_content.get("introduction", "")
    if intro:
        story.append(Paragraph("Introduction", styles["ModuleTitle"]))
        story.append(Paragraph(intro, styles["BodyText"]))
        story.append(Spacer(1, 0.3 * inch))

    # --- Session Content ---
    for session in sessions:
        sn = session.get("session_number", "")
        title = session.get("title", f"Session {sn}")
        content = session.get("content", "")
        slo1_title = session.get("slo_1_title", "")
        slo2_title = session.get("slo_2_title", "")

        story.append(Paragraph(f"Session {sn}: {title}", styles["SessionTitle"]))

        if slo1_title:
            story.append(Paragraph(f"SLO 1: {slo1_title}", styles["SLOTitle"]))
        if slo2_title:
            story.append(Paragraph(f"SLO 2: {slo2_title}", styles["SLOTitle"]))

        # Split content into paragraphs
        paragraphs = content.split("\n\n") if content else [content]
        for para in paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), styles["BodyText"]))

        story.append(Spacer(1, 0.2 * inch))

    # --- Conclusion ---
    conclusion = pdf_content.get("conclusion", "")
    if conclusion:
        story.append(Paragraph("Conclusion", styles["ModuleTitle"]))
        story.append(Paragraph(conclusion, styles["BodyText"]))

    doc.build(story)
    return str(output)


if __name__ == "__main__":
    """Usage: python -m scripts.build.create_pdf <pdf_content_json> <module_num> <output_path>"""
    if len(sys.argv) < 4:
        print("Usage: python -m scripts.build.create_pdf <json> <module_num> <output_path>",
              file=sys.stderr)
        sys.exit(1)

    with open(sys.argv[1]) as f:
        pdf_content = json.load(f)

    path = create_module_pdf(pdf_content, int(sys.argv[2]), sys.argv[3])
    print(path)


# ── references-style learning material (faculty request 2026-07-03) ───────────
# "All PDF with links or one document is enough" — a per-unit reference sheet:
# book references + curated web links + per-session reading pointers.

def create_references_pdf(data: dict, module_num: int, output_path: str) -> str:
    from xml.sax.saxutils import escape as _e, quoteattr as _qa

    styles = _get_styles()
    story = []

    story.append(Paragraph(f"Module {module_num}: {_e(str(data.get('module_title', '')))}",
                           styles["ModuleTitle"]))
    story.append(Paragraph("Learning Material — References & Further Reading",
                           styles["SessionTitle"]))
    story.append(Spacer(1, 0.15 * inch))
    if data.get("overview"):
        story.append(Paragraph(_e(str(data["overview"])), styles["BodyText"]))
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph("Book References", styles["SessionTitle"]))
    for i, b in enumerate(data.get("book_references", []), 1):
        story.append(Paragraph(
            f"<b>{i}. {_e(str(b.get('title', '')))}</b> — {_e(str(b.get('authors', '')))} "
            f"({_e(str(b.get('publisher_year', '')))})", styles["BodyText"]))
        if b.get("relevance"):
            story.append(Paragraph(f"<i>{_e(str(b['relevance']))}</i>", styles["BodyText"]))
        story.append(Spacer(1, 4))

    story.append(Spacer(1, 0.15 * inch))
    story.append(Paragraph("Web Resources", styles["SessionTitle"]))
    for r in data.get("web_resources", []):
        url = str(r.get("url", ""))
        story.append(Paragraph(
            f"<b>{_e(str(r.get('title', '')))}</b> [{_e(str(r.get('type', '')))}] — "
            f"<link href={_qa(url)} color='blue'>{_e(url)}</link>",
            styles["BodyText"]))
        if r.get("description"):
            story.append(Paragraph(_e(str(r["description"])), styles["BodyText"]))
        story.append(Spacer(1, 4))

    pointers = data.get("session_pointers", [])
    if pointers:
        story.append(Spacer(1, 0.15 * inch))
        story.append(Paragraph("Session-wise Reading Guide", styles["SessionTitle"]))
        rows = [["Session", "Topic", "Suggested Reading"]] + [
            [str(p.get("session", "")),
             Paragraph(_e(str(p.get("topic", ""))), styles["BodyText"]),
             Paragraph(_e(str(p.get("reading", ""))), styles["BodyText"])]
            for p in pointers
        ]
        table = Table(rows, colWidths=[0.8 * inch, 2.4 * inch, 3.6 * inch])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARY),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_LIGHT_BG]),
        ]))
        story.append(table)

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=f"Module {module_num} Learning Material — References",
    )
    doc.build(story)
    return output_path
