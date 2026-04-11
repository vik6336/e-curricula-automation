"""Slide layout and style helpers for PPT generation."""

from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx import Presentation


# Color scheme
COLOR_PRIMARY = RGBColor(0x1B, 0x36, 0x5D)    # Navy
COLOR_ACCENT = RGBColor(0xC8, 0x10, 0x2E)     # SRM Maroon
COLOR_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
COLOR_LIGHT_GRAY = RGBColor(0xF2, 0xF2, 0xF2)
COLOR_DARK_TEXT = RGBColor(0x33, 0x33, 0x33)
COLOR_SUBTITLE = RGBColor(0x66, 0x66, 0x66)

# Dimensions (16:9)
SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)

FONT_FAMILY = "Calibri"


def create_presentation() -> Presentation:
    """Create a new 16:9 presentation."""
    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT
    return prs


def _add_accent_bar(slide, top=False):
    """Add a colored accent bar to the slide."""
    if top:
        shape = slide.shapes.add_shape(
            1,  # Rectangle
            Inches(0), Inches(0),
            SLIDE_WIDTH, Inches(0.15),
        )
    else:
        shape = slide.shapes.add_shape(
            1,
            Inches(0), SLIDE_HEIGHT - Inches(0.15),
            SLIDE_WIDTH, Inches(0.15),
        )
    shape.fill.solid()
    shape.fill.fore_color.rgb = COLOR_ACCENT
    shape.line.fill.background()


def _add_footer(slide, module_num, session_num, slo_num):
    """Add a footer with module/session/SLO info."""
    txBox = slide.shapes.add_textbox(
        Inches(0.5), SLIDE_HEIGHT - Inches(0.6),
        Inches(6), Inches(0.4),
    )
    tf = txBox.text_frame
    p = tf.paragraphs[0]
    p.text = f"Module {module_num} | Session {session_num} | SLO {slo_num}"
    p.font.size = Pt(10)
    p.font.color.rgb = COLOR_SUBTITLE
    p.font.name = FONT_FAMILY


def add_title_slide(prs, title, subtitle, module_num, session_num, slo_num):
    """Add a title slide with course info."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    # Background accent bar at top
    _add_accent_bar(slide, top=True)

    # Title
    txBox = slide.shapes.add_textbox(
        Inches(1), Inches(2),
        Inches(11.333), Inches(1.5),
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(36)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.font.name = FONT_FAMILY
    p.alignment = PP_ALIGN.LEFT

    # Subtitle (SLO description)
    txBox2 = slide.shapes.add_textbox(
        Inches(1), Inches(3.8),
        Inches(11.333), Inches(1),
    )
    tf2 = txBox2.text_frame
    tf2.word_wrap = True
    p2 = tf2.paragraphs[0]
    p2.text = subtitle
    p2.font.size = Pt(20)
    p2.font.color.rgb = COLOR_SUBTITLE
    p2.font.name = FONT_FAMILY
    p2.alignment = PP_ALIGN.LEFT

    # Course info line
    txBox3 = slide.shapes.add_textbox(
        Inches(1), Inches(5.2),
        Inches(11.333), Inches(0.5),
    )
    tf3 = txBox3.text_frame
    p3 = tf3.paragraphs[0]
    p3.text = f"21CSE597T — Containers and Cloud DevOps"
    p3.font.size = Pt(14)
    p3.font.color.rgb = COLOR_ACCENT
    p3.font.name = FONT_FAMILY

    # Module/Session info
    txBox4 = slide.shapes.add_textbox(
        Inches(1), Inches(5.7),
        Inches(11.333), Inches(0.5),
    )
    tf4 = txBox4.text_frame
    p4 = tf4.paragraphs[0]
    p4.text = f"Module {module_num} | Session {session_num} | SLO {slo_num}"
    p4.font.size = Pt(12)
    p4.font.color.rgb = COLOR_SUBTITLE
    p4.font.name = FONT_FAMILY

    _add_accent_bar(slide, top=False)
    return slide


def add_content_slide(prs, title, bullet_points, speaker_notes, module_num, session_num, slo_num):
    """Add a content slide with title and bullet points."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    _add_accent_bar(slide, top=True)

    # Title
    txBox = slide.shapes.add_textbox(
        Inches(0.8), Inches(0.4),
        Inches(11.733), Inches(0.9),
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = title
    p.font.size = Pt(28)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY
    p.font.name = FONT_FAMILY

    # Bullet points
    txBox2 = slide.shapes.add_textbox(
        Inches(1), Inches(1.6),
        Inches(11.333), Inches(5.2),
    )
    tf2 = txBox2.text_frame
    tf2.word_wrap = True

    for i, point in enumerate(bullet_points):
        if i == 0:
            p = tf2.paragraphs[0]
        else:
            p = tf2.add_paragraph()
        p.text = f"• {point}"
        p.font.size = Pt(18)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.font.name = FONT_FAMILY
        p.space_after = Pt(12)
        p.space_before = Pt(4)

    # Speaker notes
    if speaker_notes:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = speaker_notes

    _add_footer(slide, module_num, session_num, slo_num)
    _add_accent_bar(slide, top=False)
    return slide


def add_summary_slide(prs, bullet_points, speaker_notes, module_num, session_num, slo_num):
    """Add a summary/key takeaways slide."""
    slide_layout = prs.slide_layouts[6]  # Blank layout
    slide = prs.slides.add_slide(slide_layout)

    _add_accent_bar(slide, top=True)

    # Title
    txBox = slide.shapes.add_textbox(
        Inches(0.8), Inches(0.4),
        Inches(11.733), Inches(0.9),
    )
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Key Takeaways"
    p.font.size = Pt(32)
    p.font.bold = True
    p.font.color.rgb = COLOR_ACCENT
    p.font.name = FONT_FAMILY

    # Numbered takeaways
    txBox2 = slide.shapes.add_textbox(
        Inches(1), Inches(1.6),
        Inches(11.333), Inches(5.2),
    )
    tf2 = txBox2.text_frame
    tf2.word_wrap = True

    for i, point in enumerate(bullet_points):
        if i == 0:
            p = tf2.paragraphs[0]
        else:
            p = tf2.add_paragraph()
        p.text = f"{i + 1}. {point}"
        p.font.size = Pt(20)
        p.font.color.rgb = COLOR_DARK_TEXT
        p.font.name = FONT_FAMILY
        p.space_after = Pt(16)
        p.space_before = Pt(4)

    if speaker_notes:
        notes_slide = slide.notes_slide
        notes_slide.notes_text_frame.text = speaker_notes

    _add_footer(slide, module_num, session_num, slo_num)
    _add_accent_bar(slide, top=False)
    return slide
