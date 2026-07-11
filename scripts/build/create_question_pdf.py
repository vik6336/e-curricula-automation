"""Build the faculty review PDF for a module's generated question bank.

Shows every question with its full OBE metadata (Bloom's level, taxonomy verb,
program outcomes) exactly as it will be entered into the eCurricula portal.
"""

from pathlib import Path
from xml.sax.saxutils import escape as _esc

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


def _e(text) -> str:
    """Escape dynamic content — reportlab Paragraph parses XML-ish markup, so an
    unescaped & or < in a question would break the build or inject markup."""
    return _esc(str(text))

COLOR_PRIMARY = colors.HexColor("#1B365D")
COLOR_ACCENT = colors.HexColor("#C8102E")
COLOR_LIGHT_BG = colors.HexColor("#F0F4FA")

BLOOMS = {1: "Remember", 2: "Understand", 3: "Apply",
          4: "Analyze", 5: "Evaluate", 6: "Create"}


def _styles():
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle("QTitle", parent=base["Title"], fontSize=20,
                                textColor=COLOR_PRIMARY, spaceAfter=6),
        "h2": ParagraphStyle("QH2", parent=base["Heading2"], fontSize=14,
                             textColor=COLOR_PRIMARY, spaceBefore=14, spaceAfter=6),
        "h3": ParagraphStyle("QH3", parent=base["Heading3"], fontSize=11,
                             textColor=COLOR_ACCENT, spaceBefore=10, spaceAfter=4),
        "body": ParagraphStyle("QBody", parent=base["BodyText"], fontSize=9.5,
                               leading=13),
        "meta": ParagraphStyle("QMeta", parent=base["BodyText"], fontSize=8,
                               textColor=colors.HexColor("#555555"), leading=11),
        "opt": ParagraphStyle("QOpt", parent=base["BodyText"], fontSize=9,
                              leftIndent=14, leading=12),
    }


def _meta_line(st, level, verb, pos):
    pos_txt = ", ".join(f"PO{p:02d}" for p in pos)
    return Paragraph(
        f"<b>Bloom's Level:</b> {level} ({BLOOMS.get(level, '?')}) &nbsp;|&nbsp; "
        f"<b>Taxonomy of Learning – Cognitive:</b> {verb} &nbsp;|&nbsp; "
        f"<b>Program Outcomes:</b> {pos_txt}",
        st["meta"],
    )


def create_question_pdf(qbank: dict, output_path: str) -> str:
    st = _styles()
    story = []

    story.append(Paragraph("Question Bank — Faculty Review", st["title"]))
    story.append(Paragraph(
        f"Module {qbank['module_num']}: {qbank['module_title']}", st["h2"]))
    story.append(Paragraph(
        "Review every question below. On approval, CurriculAI will enter these "
        "into the eCurricula portal (MCQ / Short / Long sections) automatically "
        "with the metadata shown.", st["meta"]))
    story.append(Spacer(1, 0.2 * inch))

    for sess in qbank["sessions"]:
        s = sess["session"]
        story.append(Paragraph(f"Session {s}", st["h2"]))

        story.append(Paragraph("Multiple Choice Questions (5)", st["h3"]))
        for i, q in enumerate(sess.get("mcqs", []), 1):
            story.append(Paragraph(f"<b>MCQ {s}.{i}</b> — {_e(q['question'])}", st["body"]))
            for j, opt in enumerate(q["options"], 1):
                marker = " ✓" if j == q["correct_option"] else ""
                story.append(Paragraph(f"({chr(64+j)}) {_e(opt)}{marker}", st["opt"]))
            story.append(_meta_line(st, q["blooms_level"], q["taxonomy_verb"],
                                    q["program_outcomes"]))
            story.append(Spacer(1, 6))

        story.append(Paragraph("Short-Answer Questions (2)", st["h3"]))
        for i, q in enumerate(sess.get("short_questions", []), 1):
            story.append(Paragraph(f"<b>Short {s}.{i}</b> — {_e(q['question'])}", st["body"]))
            story.append(Paragraph(f"<b>Model answer:</b> {_e(q['answer'])}", st["opt"]))
            story.append(_meta_line(st, q["level"], q["taxonomy_verb"],
                                    q["program_outcomes"]))
            story.append(Spacer(1, 6))

        story.append(Paragraph("Long-Answer Question (1)", st["h3"]))
        for i, q in enumerate(sess.get("long_questions", []), 1):
            story.append(Paragraph(f"<b>Long {s}.{i}</b> — {_e(q['question'])}", st["body"]))
            story.append(Paragraph(f"<b>Model answer:</b> {_e(q['answer'])}", st["opt"]))
            story.append(_meta_line(st, q["level"], q["taxonomy_verb"],
                                    q["program_outcomes"]))
            story.append(Spacer(1, 6))

        story.append(PageBreak())

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=0.7 * inch, rightMargin=0.7 * inch,
        topMargin=0.7 * inch, bottomMargin=0.7 * inch,
        title=f"Question Bank — Module {qbank['module_num']}",
    )
    doc.build(story)
    return output_path
