"""Prompt templates for Gemini API content generation."""

SLO_CONTENT_PROMPT = """You are an expert DevOps Architect, AI Educator, and Technical Content Designer creating university-level presentations for SRM Institute of Science and Technology.

## Course Context
- **Course Code**: {course_code}
- **Course Name**: {course_name}
- **Module {module_num}**: {module_title}
- **Session {session_num}** of 9  |  **SLO {slo_num}** of 2
- **Student Learning Outcome (SLO)**: {slo_text}
- **Student Result Outcome (SRO)**: {sro_text}
- **Audience**: Undergraduate/Postgraduate Engineering students
- **Difficulty**: Intermediate to Advanced

## Syllabus Context
{syllabus_context}

## Faculty Source Material (use as primary knowledge base)
{source_text}

---

## SLIDE STRUCTURE — PRODUCE EXACTLY 8–10 SLIDES IN THIS ORDER

### Slide 1 — TITLE  (layout: "title_slide")
- title: Topic name derived from the SLO
- subtitle: The full SLO text verbatim
- hook: One punchy, thought-provoking statement that grabs attention (NOT a question)
- speaker_notes: 2–3 sentences for the presenter to introduce the session

### Slide 2 — WHAT  (layout: "two_col")
- Left column: Clear, precise definition (3–4 sentences, no jargon without explanation)
- Right column: Key characteristics (max 4 bullet points, each ≤ 15 words)
- analogy: One relatable real-world analogy (non-technical everyday comparison)
- speaker_notes: Expand on why this definition matters in the DevOps context

### Slide 3 — WHY  (layout: "content")
- problem_statement: The specific pain point this concept solves (1–2 sentences)
- bullet_points: 3–4 industry-relevant reasons this matters (lead with impact, e.g. "Reduces deployment failures by…")
- industry_context: One real company/tool that exemplifies this (e.g. "Netflix uses X to…")
- speaker_notes: Connect to real job roles and career relevance for students

### Slide 4 — HOW  (layout: "two_col")
- Left column: Step-by-step numbered process (4–5 steps, imperative verbs)
- Right column: Tools involved — list each tool with a one-line role description
- speaker_notes: Walk through the steps, highlight any common mistakes

### Slide 5 — DIAGRAM  (layout: "diagram")
- title: Descriptive title for the diagram
- diagram: Structured data for automatic rendering:
  {{
    "nodes": [{{"id": "n1", "label": "Component Name", "shape": "box", "color": "#1B365D", "font_color": "#FFFFFF"}}, ...],
    "edges": [{{"from": "n1", "to": "n2", "label": "action/relationship", "arrow": true}}, ...],
    "layout_direction": "left_to_right",
    "caption": "One-line caption explaining what the diagram shows"
  }}
- Rules: minimum 4 nodes, all nodes connected, labels must be short (≤ 3 words), use color #1B365D for primary nodes and #C8102E for highlight/trigger nodes
- speaker_notes: Narrate the diagram flow step by step

### Slide 6 — CODE  (layout: "code_block") — INCLUDE ONLY IF the SLO involves a tool, command, config, or implementation
- title: What the code demonstrates
- code_snippet: Real, executable code (Docker, Kubernetes YAML, shell, CI/CD config, etc.) — max 20 lines
- language: programming/config language name (e.g. "yaml", "dockerfile", "bash", "python")
- explanation: 3 inline annotations — each as {{"line_ref": "line X–Y", "note": "what it does"}}
- speaker_notes: Walk through the code, explain what to run and what to expect

### Slide 7 — REAL-WORLD USE CASE  (layout: "two_col")
- Left column:
  - company: Real company or project name
  - scenario: 2–3 sentence problem description
  - solution: How the SLO concept was applied
- Right column:
  - outcome: Measurable result (use numbers/percentages where possible)
  - lesson: One transferable insight for students
- speaker_notes: Guide students to connect this to their own projects

### Slide 8 — QUIZ  (layout: "quiz")
- question: One clear MCQ testing conceptual understanding of this SLO (NOT recall)
- options: Exactly 4 options labeled A–D
- correct_answer: The correct letter (A/B/C/D)
- explanation: 2–3 sentences explaining why the answer is correct and why others are wrong
- challenge_task: One hands-on task students can try in 15–20 minutes (specific, tool-based)
- speaker_notes: Deliver as live class activity; reveal answer after 60 seconds of discussion

### Slide 9 — SUMMARY  (layout: "summary")
- bullet_points: Exactly 4 takeaways — one per slide theme (WHAT/WHY/HOW/USE CASE)
- call_to_action: One specific next step (read X, try Y, explore Z)
- preview: One sentence teasing what comes in the next SLO
- speaker_notes: Reinforce the SLO learning outcome, connect to assessment

---

## BRANDING & STYLE RULES
- Primary color: #1B365D (SRM Navy) — use for headers, primary nodes
- Accent color: #C8102E (SRM Maroon) — use for highlights, quiz, call-to-action
- Font: Calibri
- Tone: Technical but accessible — explain acronyms on first use
- Max 5 bullet points per slide
- Bullet points: lead with action verbs or impact metrics, ≤ 15 words each
- No filler phrases ("In conclusion…", "As mentioned…", "It is important to note…")
- Code must be real, syntactically correct, and runnable
- Diagrams must have enough detail to render automatically without human editing

---

## OUTPUT FORMAT — STRICT JSON ONLY

Return ONLY valid JSON. No markdown, no explanation, no code fences.

{{
  "slo_title": "Short title for this SLO (5–8 words)",
  "course_code": "{course_code}",
  "module_num": {module_num},
  "session_num": {session_num},
  "slo_num": {slo_num},
  "slides": [
    {{
      "slide_number": 1,
      "slide_type": "title",
      "layout": "title_slide",
      "title": "",
      "subtitle": "",
      "hook": "",
      "speaker_notes": ""
    }},
    {{
      "slide_number": 2,
      "slide_type": "what",
      "layout": "two_col",
      "title": "",
      "definition": "",
      "key_characteristics": [],
      "analogy": "",
      "speaker_notes": ""
    }},
    {{
      "slide_number": 3,
      "slide_type": "why",
      "layout": "content",
      "title": "",
      "problem_statement": "",
      "bullet_points": [],
      "industry_context": "",
      "speaker_notes": ""
    }},
    {{
      "slide_number": 4,
      "slide_type": "how",
      "layout": "two_col",
      "title": "",
      "steps": [],
      "tools": [{{"name": "", "role": ""}}],
      "speaker_notes": ""
    }},
    {{
      "slide_number": 5,
      "slide_type": "diagram",
      "layout": "diagram",
      "title": "",
      "diagram": {{
        "nodes": [{{"id": "", "label": "", "shape": "box", "color": "", "font_color": ""}}],
        "edges": [{{"from": "", "to": "", "label": "", "arrow": true}}],
        "layout_direction": "left_to_right",
        "caption": ""
      }},
      "speaker_notes": ""
    }},
    {{
      "slide_number": 6,
      "slide_type": "code",
      "layout": "code_block",
      "title": "",
      "code_snippet": "",
      "language": "",
      "explanation": [{{"line_ref": "", "note": ""}}],
      "speaker_notes": ""
    }},
    {{
      "slide_number": 7,
      "slide_type": "use_case",
      "layout": "two_col",
      "title": "",
      "company": "",
      "scenario": "",
      "solution": "",
      "outcome": "",
      "lesson": "",
      "speaker_notes": ""
    }},
    {{
      "slide_number": 8,
      "slide_type": "quiz",
      "layout": "quiz",
      "title": "Knowledge Check",
      "question": "",
      "options": {{"A": "", "B": "", "C": "", "D": ""}},
      "correct_answer": "",
      "explanation": "",
      "challenge_task": "",
      "speaker_notes": ""
    }},
    {{
      "slide_number": 9,
      "slide_type": "summary",
      "layout": "summary",
      "title": "Key Takeaways",
      "bullet_points": [],
      "call_to_action": "",
      "preview": "",
      "speaker_notes": ""
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


QUESTION_GEN_PROMPT = """You are an expert educator creating assessment questions for an Indian university engineering course, following Outcome-Based Education (OBE) standards.

## Course Context
- **Course**: {course_code} — {course_name}
- **Module {module_num}**: {module_title}
- **Session {session_num}**
- **SLO 1**: {slo_1}
- **SLO 2**: {slo_2}

## Task
Create assessment questions for THIS SESSION covering both SLOs:
- **5 multiple choice questions** (4 options each, exactly one correct)
- **2 short-answer questions** (expected answer: 4-6 sentences)
- **1 long-answer question** (expected answer: structured, 250-400 words)

## Rules
1. Questions must be answerable from the session's SLO topics alone.
2. Vary Bloom's levels: include at least one level-1/2 (remember/understand) and at least one level-3+ (apply/analyze) question.
3. `taxonomy_verb` MUST be exactly one word from this list (match the question's cognitive action):
   Choose, Count, Cite, Define, Describe, Distinguish, Draw, Find, Group, Identify, Know, Label, List, Listen, Locate, Match, Memorize, Name, Outline, Quote, Read, Repeat, Recall, Recite, Relate, Review, Recognize, Record, Reproduce, Select, State, Sequence, Show, Sort, Tell, Underline, Write
4. `blooms_level` / `level` is an integer 1-6 (1=Remember, 2=Understand, 3=Apply, 4=Analyze, 5=Evaluate, 6=Create).
5. `program_outcomes` is a list of 1-2 integers from [1, 2, 3] (PO1=Engineering Knowledge, PO2=Problem Analysis, PO3=Design/Development).
6. MCQ distractors must be plausible — no joke options.
7. Answers must be technically accurate and complete.

## Output Format
Return ONLY valid JSON:
{{
  "mcqs": [
    {{
      "question": "Question text?",
      "options": ["Option A text", "Option B text", "Option C text", "Option D text"],
      "correct_option": 1,
      "blooms_level": 2,
      "taxonomy_verb": "Identify",
      "program_outcomes": [1]
    }}
  ],
  "short_questions": [
    {{
      "question": "Question text?",
      "answer": "Model answer, 4-6 sentences.",
      "level": 2,
      "taxonomy_verb": "Describe",
      "program_outcomes": [1, 2]
    }}
  ],
  "long_questions": [
    {{
      "question": "Question text?",
      "answer": "Structured model answer with key points.",
      "level": 4,
      "taxonomy_verb": "Outline",
      "program_outcomes": [2]
    }}
  ]
}}"""


LM_REFERENCES_PROMPT = """You are a university course librarian creating a Learning Material reference sheet for an engineering course module.

## Course Context
- **Course**: {course_code} — {course_name}
- **Module {module_num}**: {module_title}
- **Session topics**:
{session_topics}

## Task
Create a curated reference document for this module: book references and web
resources students should use. This is a REFERENCE SHEET, not a textbook —
keep descriptions short and practical.

## Rules
1. Book references: 4-6 real, well-known textbooks relevant to the module topics.
   Use accurate titles/authors/publishers — standard texts only, no invented books.
2. Web resources: 8-12 links. ONLY stable, well-known URLs: official documentation
   home pages (docs.docker.com, kubernetes.io/docs), official tutorials, and major
   learning platforms. NO deep links to blog posts; NO invented URLs.
3. Per-session pointers: for each session, one line pointing students to the most
   relevant reference(s).
4. Keep the overview to ~100 words.

## Output Format
Return ONLY valid JSON:
{{
  "module_title": "{module_title}",
  "overview": "What this module covers and how to use these references...",
  "book_references": [
    {{"title": "Book Title", "authors": "Author A, Author B", "publisher_year": "Publisher, Year", "relevance": "Which module topics it covers"}}
  ],
  "web_resources": [
    {{"title": "Resource name", "url": "https://...", "type": "Official Docs|Tutorial|Video Course|Tool", "description": "One line on what it offers"}}
  ],
  "session_pointers": [
    {{"session": 1, "topic": "Session topic", "reading": "Chapter/resource pointer"}}
  ]
}}"""


QUESTION_REGEN_PROMPT = """You are revising ONE assessment question for an Indian university engineering course (OBE standards).

## Course Context
- **Course**: {course_code} — {course_name}
- **Module {module_num}**: {module_title}
- **Question type**: {kind_label}

## Existing Question (to be replaced)
{existing_question}

## Faculty Feedback
{feedback}

## Rules
1. Produce ONE replacement question of the same type, addressing the feedback.
2. `taxonomy_verb` MUST be exactly one word from:
   Choose, Count, Cite, Define, Describe, Distinguish, Draw, Find, Group, Identify, Know, Label, List, Listen, Locate, Match, Memorize, Name, Outline, Quote, Read, Repeat, Recall, Recite, Relate, Review, Recognize, Record, Reproduce, Select, State, Sequence, Show, Sort, Tell, Underline, Write
3. Bloom's level / level is an integer 1-6. `program_outcomes` ⊆ [1, 2, 3].
4. MCQs: exactly 4 plausible options, one correct. Short/long: include a model answer.
5. Stay on the same topic as the original unless the feedback says otherwise.

## Output Format
Return ONLY valid JSON — a single question object with EXACTLY the same keys as the existing question shown above."""
