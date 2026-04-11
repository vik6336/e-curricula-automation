"""Prompt templates for Gemini API content generation."""

SLO_CONTENT_PROMPT = """You are an expert educational content creator for university-level courses at SRM Institute of Science and Technology.

## Task
Generate presentation content for a specific Student Learning Outcome (SLO).

## Course Details
- **Course Code**: {course_code}
- **Course Name**: {course_name}
- **Module {module_num}**: {module_title}
- **Session {session_num}** of 9
- **SLO {slo_num}** of 2: {slo_text}
- **SRO**: {sro_text}

## Syllabus Context for This Module
{syllabus_context}

## Source Material (Faculty-Provided References)
{source_text}

## Requirements
Generate educational presentation content that:
1. Contains 8-12 slides
2. Each slide has: a title (concise), 3-5 bullet points (30-60 words each), and speaker notes (2-3 sentences expanding on the bullets)
3. Directly addresses the SLO: "{slo_text}"
4. Uses the source material as the primary knowledge base
5. Maintains academic rigor appropriate for undergraduate/postgraduate level
6. Includes at least one example or case study slide
7. Ends with a summary/key takeaways slide
8. First slide should be a title slide with the SLO as subtitle

## Output Format
Return ONLY valid JSON in this exact structure:
{{
  "slo_title": "Short descriptive title for this SLO",
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "title",
      "title": "Slide Title",
      "subtitle": "SLO description",
      "bullet_points": [],
      "speaker_notes": "Introduction notes..."
    }},
    {{
      "slide_number": 2,
      "slide_type": "content",
      "title": "Slide Title",
      "subtitle": "",
      "bullet_points": ["Point 1...", "Point 2...", "Point 3..."],
      "speaker_notes": "Detailed explanation..."
    }},
    {{
      "slide_number": 8,
      "slide_type": "summary",
      "title": "Key Takeaways",
      "subtitle": "",
      "bullet_points": ["Takeaway 1...", "Takeaway 2...", "Takeaway 3..."],
      "speaker_notes": "Summary notes..."
    }}
  ]
}}"""

PDF_CONSOLIDATION_PROMPT = """You are an expert educational content writer creating learning material for a university course at SRM Institute of Science and Technology.

## Task
Consolidate the following presentation content into a flowing, coherent learning document for students. This will be the "Learning Material" PDF for the module.

## Course Details
- **Course Code**: {course_code}
- **Course Name**: {course_name}
- **Module {module_num}**: {module_title}

## Content to Consolidate
{all_session_content}

## Requirements
1. Organize content by session (Session 1 through Session 9)
2. For each session, combine both SLO contents into flowing prose paragraphs (NOT bullet points)
3. Add smooth transitions between sessions
4. Maintain technical accuracy and academic rigor
5. Include relevant examples from the source material
6. Each session section should be 400-600 words
7. Add a brief module introduction (150 words) and conclusion (100 words)

## Output Format
Return ONLY valid JSON:
{{
  "module_title": "{module_title}",
  "introduction": "Module introduction text...",
  "sessions": [
    {{
      "session_number": 1,
      "title": "Session title",
      "slo_1_title": "SLO 1 title",
      "slo_2_title": "SLO 2 title",
      "content": "Flowing prose combining both SLOs..."
    }}
  ],
  "conclusion": "Module conclusion text..."
}}"""
