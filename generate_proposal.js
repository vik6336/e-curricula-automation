const fs = require("fs");
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        Header, Footer, AlignmentType, LevelFormat,
        HeadingLevel, BorderStyle, WidthType, ShadingType,
        PageNumber, PageBreak, TabStopType, TabStopPosition } = require("docx");

const COLOR_PRIMARY = "1B365D";   // Navy
const COLOR_ACCENT = "C8102E";    // SRM Maroon
const COLOR_LIGHT_BG = "E8EDF2";
const COLOR_WHITE = "FFFFFF";

const border = { style: BorderStyle.SINGLE, size: 1, color: "CCCCCC" };
const borders = { top: border, bottom: border, left: border, right: border };
const noBorders = {
  top: { style: BorderStyle.NONE, size: 0 },
  bottom: { style: BorderStyle.NONE, size: 0 },
  left: { style: BorderStyle.NONE, size: 0 },
  right: { style: BorderStyle.NONE, size: 0 },
};
const cellMargins = { top: 80, bottom: 80, left: 120, right: 120 };

function heading(text, level) {
  return new Paragraph({
    heading: level,
    spacing: { before: level === HeadingLevel.HEADING_1 ? 360 : 240, after: 200 },
    children: [new TextRun({ text, bold: true, font: "Arial", size: level === HeadingLevel.HEADING_1 ? 32 : 26, color: COLOR_PRIMARY })],
  });
}

function body(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 160, line: 320 },
    alignment: opts.align || AlignmentType.JUSTIFIED,
    children: [new TextRun({ text, font: "Arial", size: 22, color: "333333", ...opts })],
  });
}

function boldBody(label, text) {
  return new Paragraph({
    spacing: { after: 160, line: 320 },
    children: [
      new TextRun({ text: label, font: "Arial", size: 22, bold: true, color: COLOR_PRIMARY }),
      new TextRun({ text, font: "Arial", size: 22, color: "333333" }),
    ],
  });
}

function headerCell(text, width) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR },
    margins: cellMargins,
    verticalAlign: "center",
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, bold: true, color: COLOR_WHITE })] })],
  });
}

function dataCell(text, width, shade) {
  return new TableCell({
    borders, width: { size: width, type: WidthType.DXA },
    shading: shade ? { fill: COLOR_LIGHT_BG, type: ShadingType.CLEAR } : undefined,
    margins: cellMargins,
    children: [new Paragraph({ children: [new TextRun({ text, font: "Arial", size: 20, color: "333333" })] })],
  });
}

// ── Cover Page ──
const coverSection = {
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
    },
  },
  children: [
    new Paragraph({ spacing: { before: 2400 }, children: [] }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: "SRM Institute of Science and Technology", font: "Arial", size: 28, color: COLOR_ACCENT, bold: true })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "School of Computing", font: "Arial", size: 24, color: "666666" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "Directorate of Learning and Development", font: "Arial", size: 22, color: "666666" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: COLOR_ACCENT, space: 1 } },
      spacing: { after: 600 },
      children: [],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 300 },
      children: [new TextRun({ text: "PROJECT PROPOSAL", font: "Arial", size: 36, bold: true, color: COLOR_PRIMARY })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 200 },
      children: [new TextRun({ text: "E-Curricula Content Automation System", font: "Arial", size: 32, bold: true, color: COLOR_PRIMARY })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "Using n8n Workflow Automation & Google Gemini LLM", font: "Arial", size: 24, color: COLOR_ACCENT })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 600 },
      children: [new TextRun({ text: "Course: 21CSE597T \u2014 Containers and Cloud DevOps", font: "Arial", size: 22, color: "666666" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      border: { top: { style: BorderStyle.SINGLE, size: 6, color: COLOR_ACCENT, space: 1 } },
      spacing: { before: 200, after: 300 },
      children: [],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "Prepared by: Vikram Khanna", font: "Arial", size: 24, color: "333333" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "Faculty Advisor: [FA Name]", font: "Arial", size: 24, color: "333333" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 100 },
      children: [new TextRun({ text: "Date: April 2026", font: "Arial", size: 22, color: "666666" })],
    }),
  ],
};

// ── Main Content ──
const mainChildren = [];

// ─── 1. Executive Summary ───
mainChildren.push(heading("1. Executive Summary", HeadingLevel.HEADING_1));
mainChildren.push(body(
  "This proposal outlines an automation system for SRM\u2019s e-curricula portal (dld.srmist.edu.in) " +
  "that eliminates the manual effort of creating and uploading course content. The system uses n8n workflow " +
  "automation (running via Docker) connected to Google\u2019s Gemini LLM to automatically generate " +
  "Session Learning Outcome (SLO)-aligned presentations (PPTX) and Learning Material documents (PDF) " +
  "from faculty-provided source materials and the official syllabus. For the pilot course " +
  "21CSE597T \u2014 Containers and Cloud DevOps \u2014 this means automatically producing 90 PPTX files " +
  "and 5 PDF documents across all 5 modules, then uploading them directly to the portal."
));

// ─── 2. Problem Statement ───
mainChildren.push(heading("2. Problem Statement", HeadingLevel.HEADING_1));
mainChildren.push(body(
  "The e-curricula portal requires Course Coordinators to manually create and upload the following " +
  "content for each course:"
));
mainChildren.push(boldBody("Learning Material (PDF): ", "1 faculty-curated PDF document per unit (5 units total), covering all session topics with supplementary references."));
mainChildren.push(boldBody("PPTx Source (ZIP/PPTX): ", "For each unit, 9 sessions \u00d7 2 SLOs = 18 individual presentation files. Across 5 modules, this is 90 presentations."));
mainChildren.push(body(
  "Creating this content manually for a single course requires significant faculty time. " +
  "Each presentation must align with specific SLOs defined by the university, maintain consistent formatting, " +
  "and draw from approved reference materials. Scaling this across multiple courses and semesters " +
  "makes manual creation unsustainable."
));

// ─── 3. Proposed Solution ───
mainChildren.push(heading("3. Proposed Solution", HeadingLevel.HEADING_1));
mainChildren.push(body(
  "An end-to-end automation pipeline that takes faculty-provided source documents (textbooks, " +
  "reference PDFs, lecture notes) and the official SLO/SRO document as inputs, then automatically:"
));
mainChildren.push(boldBody("1. Parses ", "the SLO/SRO document to extract all 90 Session Learning Outcomes across 5 modules."));
mainChildren.push(boldBody("2. Extracts text ", "from source documents (PDF, DOCX, PPTX, web links) for each unit."));
mainChildren.push(boldBody("3. Generates content ", "using Google Gemini LLM, producing structured slide content (8\u201312 slides per SLO) and narrative prose for the PDF."));
mainChildren.push(boldBody("4. Builds PPTX files ", "using python-pptx with professional formatting (16:9, Calibri, SRM colour scheme)."));
mainChildren.push(boldBody("5. Builds PDF documents ", "using ReportLab with cover page, table of contents, and session-by-session narrative."));
mainChildren.push(boldBody("6. Uploads all files ", "to the e-curricula portal via Playwright browser automation."));

// ─── 4. System Architecture ───
mainChildren.push(heading("4. System Architecture", HeadingLevel.HEADING_1));
mainChildren.push(body("The system follows a linear pipeline architecture, orchestrated by n8n:"));
mainChildren.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 200, after: 200 },
  children: [new TextRun({
    text: "[Source Documents] \u2192 [Document Ingestion] \u2192 [Gemini Content Generation] \u2192 [PPT/PDF Build] \u2192 [Portal Upload]",
    font: "Courier New", size: 20, color: COLOR_PRIMARY, bold: true,
  })],
}));

// Architecture table
mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 6960],
  rows: [
    new TableRow({ children: [headerCell("Component", 2400), headerCell("Description", 6960)] }),
    new TableRow({ children: [dataCell("n8n (Docker)", 2400, true), dataCell("Workflow orchestration engine. Runs via Docker container, coordinates all pipeline stages, handles retries and error logging.", 6960, true)] }),
    new TableRow({ children: [dataCell("Gemini 2.0 Flash", 2400), dataCell("Google\u2019s LLM (free tier). Generates structured slide content and PDF narratives from source material, aligned to each SLO.", 6960)] }),
    new TableRow({ children: [dataCell("Python Scripts", 2400, true), dataCell("Document parsing (python-docx, pdfplumber), PPT generation (python-pptx), PDF generation (ReportLab), portal upload (Playwright).", 6960, true)] }),
    new TableRow({ children: [dataCell("Playwright", 2400), dataCell("Browser automation for logging into the e-curricula portal and uploading generated files to the correct slots.", 6960)] }),
  ],
}));

// ─── 5. Technology Stack ───
mainChildren.push(heading("5. Technology Stack", HeadingLevel.HEADING_1));
mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2200, 2200, 4960],
  rows: [
    new TableRow({ children: [headerCell("Technology", 2200), headerCell("Version", 2200), headerCell("Purpose", 4960)] }),
    new TableRow({ children: [dataCell("n8n", 2200, true), dataCell("Latest (Docker)", 2200, true), dataCell("Workflow automation and orchestration", 4960, true)] }),
    new TableRow({ children: [dataCell("Google Gemini", 2200), dataCell("2.0 Flash", 2200), dataCell("LLM for content generation (free tier, upgradeable to Pro)", 4960)] }),
    new TableRow({ children: [dataCell("Python", 2200, true), dataCell("3.12+", 2200, true), dataCell("Core scripting language for all pipeline stages", 4960, true)] }),
    new TableRow({ children: [dataCell("python-pptx", 2200), dataCell("1.0+", 2200), dataCell("PowerPoint PPTX file generation", 4960)] }),
    new TableRow({ children: [dataCell("ReportLab", 2200, true), dataCell("4.1+", 2200, true), dataCell("PDF document generation", 4960, true)] }),
    new TableRow({ children: [dataCell("python-docx", 2200), dataCell("1.1+", 2200), dataCell("Parsing SLO/SRO Word document", 4960)] }),
    new TableRow({ children: [dataCell("pdfplumber", 2200, true), dataCell("0.10+", 2200, true), dataCell("Extracting text from PDF source documents", 4960, true)] }),
    new TableRow({ children: [dataCell("Playwright", 2200), dataCell("1.40+", 2200), dataCell("Browser automation for portal upload", 4960)] }),
    new TableRow({ children: [dataCell("Docker", 2200, true), dataCell("Latest", 2200, true), dataCell("Container runtime for n8n", 4960, true)] }),
  ],
}));

// ─── 6. Scope of Work ───
mainChildren.push(heading("6. Scope of Work", HeadingLevel.HEADING_1));
mainChildren.push(body("The project is divided into three phases. This proposal covers Phase 1 in detail. Phases 2 and 3 will follow after Phase 1 is validated."));

mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [1500, 2800, 2800, 2260],
  rows: [
    new TableRow({ children: [headerCell("Phase", 1500), headerCell("Deliverable", 2800), headerCell("Content Type", 2800), headerCell("Status", 2260)] }),
    new TableRow({ children: [dataCell("Phase 1", 1500, true), dataCell("Course Content", 2800, true), dataCell("Learning Material (PDF) + PPTx Source (PPTX)", 2800, true), dataCell("In Progress", 2260, true)] }),
    new TableRow({ children: [dataCell("Phase 2", 1500), dataCell("Worksheets", 2800), dataCell("Session-aligned worksheet documents", 2800), dataCell("Planned", 2260)] }),
    new TableRow({ children: [dataCell("Phase 3", 1500, true), dataCell("Assessments", 2800, true), dataCell("MCQ, short answer, and long answer assessments", 2800, true), dataCell("Planned", 2260, true)] }),
  ],
}));

// ─── 7. Workflow Details ───
mainChildren.push(heading("7. Detailed Workflow (Phase 1)", HeadingLevel.HEADING_1));

mainChildren.push(heading("Stage 1: Document Ingestion", HeadingLevel.HEADING_2));
mainChildren.push(body("The SLO/SRO Word document is parsed using python-docx to extract all 5 modules, 45 sessions, and 90 SLOs into structured JSON. Faculty-provided source documents (PDFs, DOCX, PPTX, web links) are text-extracted using pdfplumber, python-docx, python-pptx, and BeautifulSoup respectively."));

mainChildren.push(heading("Stage 2: LLM Content Generation", HeadingLevel.HEADING_2));
mainChildren.push(body("For each SLO, the Gemini API receives a carefully engineered prompt containing: the SLO description, SRO context, module syllabus, and extracted source material. Gemini returns structured JSON with 8\u201312 slides per SLO (title, bullet points, speaker notes). A second consolidation pass generates flowing prose narrative for the PDF. Temperature is set to 0.35 for factual, consistent output."));

mainChildren.push(heading("Stage 3: File Generation", HeadingLevel.HEADING_2));
mainChildren.push(body("PPTX files are generated using python-pptx in 16:9 widescreen format with a professional design: Calibri font, navy (#1B365D) primary colour, SRM maroon (#C8102E) accents. Each presentation includes a title slide, 6\u201310 content slides, and a key takeaways slide. PDFs are generated using ReportLab in A4 format with cover page, table of contents, session sections, and conclusion."));

mainChildren.push(heading("Stage 4: Portal Upload", HeadingLevel.HEADING_2));
mainChildren.push(body("Playwright automates the browser to log into dld.srmist.edu.in, navigate to the course, select the correct unit, and upload each file to its designated slot (session/SLO for PPTs, unit for PDFs). The browser runs in visible mode to handle any CAPTCHAs. Screenshots are captured on failure for debugging."));

// ─── 8. Output Specifications ───
mainChildren.push(heading("8. Output Specifications", HeadingLevel.HEADING_1));
mainChildren.push(heading("Per Module Output", HeadingLevel.HEADING_2));

mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [2400, 1600, 5360],
  rows: [
    new TableRow({ children: [headerCell("File Type", 2400), headerCell("Count", 1600), headerCell("Details", 5360)] }),
    new TableRow({ children: [dataCell("PPTX Presentations", 2400, true), dataCell("18", 1600, true), dataCell("9 sessions \u00d7 2 SLOs, each with 8\u201312 slides, 16:9 format", 5360, true)] }),
    new TableRow({ children: [dataCell("Learning Material PDF", 2400), dataCell("1", 1600), dataCell("A4, cover + TOC + 9 session sections + conclusion, ~4000\u20135000 words", 5360)] }),
  ],
}));

mainChildren.push(body(""));
mainChildren.push(boldBody("Total across all 5 modules: ", "90 PPTX files + 5 PDF documents = 95 files generated and uploaded automatically."));

// ─── 9. Course Details ───
mainChildren.push(heading("9. Course Details", HeadingLevel.HEADING_1));
mainChildren.push(boldBody("Course Code: ", "21CSE597T"));
mainChildren.push(boldBody("Course Name: ", "Containers and Cloud DevOps"));
mainChildren.push(boldBody("Category: ", "Professional Elective (Progressive)"));
mainChildren.push(boldBody("Total Modules: ", "5 (9 hours each, 45 total contact hours)"));
mainChildren.push(body(""));

mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [900, 3000, 3460, 1000, 1000],
  rows: [
    new TableRow({ children: [headerCell("Module", 900), headerCell("Title", 3000), headerCell("Key Topics", 3460), headerCell("Sessions", 1000), headerCell("SLOs", 1000)] }),
    new TableRow({ children: [dataCell("1", 900, true), dataCell("Container Fundamentals & DevOps", 3000, true), dataCell("Docker Ecosystem, DevOps Toolchain, Git Essentials", 3460, true), dataCell("9", 1000, true), dataCell("18", 1000, true)] }),
    new TableRow({ children: [dataCell("2", 900), dataCell("AWS & CI/CD", 3000), dataCell("AWS ECR, ECS, CodePipeline, CodeDeploy, Jenkins", 3460), dataCell("9", 1000), dataCell("18", 1000)] }),
    new TableRow({ children: [dataCell("3", 900, true), dataCell("Infrastructure as Code", 3000, true), dataCell("Terraform, Ansible, CloudFormation, Multi-service Deployment", 3460, true), dataCell("9", 1000, true), dataCell("18", 1000, true)] }),
    new TableRow({ children: [dataCell("4", 900), dataCell("Observability & Serverless", 3000), dataCell("IAM, CloudTrail, CloudWatch, Lambda Functions", 3460), dataCell("9", 1000), dataCell("18", 1000)] }),
    new TableRow({ children: [dataCell("5", 900, true), dataCell("Kubernetes & Multi-Cloud", 3000, true), dataCell("EKS, AKS, Container Security, Multi-Cloud Strategy", 3460, true), dataCell("9", 1000, true), dataCell("18", 1000, true)] }),
    new TableRow({ children: [
      new TableCell({ borders, width: { size: 900, type: WidthType.DXA }, shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: "Total", font: "Arial", size: 20, bold: true, color: COLOR_WHITE })] })] }),
      new TableCell({ borders, width: { size: 3000, type: WidthType.DXA }, shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: "", font: "Arial", size: 20, color: COLOR_WHITE })] })] }),
      new TableCell({ borders, width: { size: 3460, type: WidthType.DXA }, shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: "", font: "Arial", size: 20, color: COLOR_WHITE })] })] }),
      new TableCell({ borders, width: { size: 1000, type: WidthType.DXA }, shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: "45", font: "Arial", size: 20, bold: true, color: COLOR_WHITE })] })] }),
      new TableCell({ borders, width: { size: 1000, type: WidthType.DXA }, shading: { fill: COLOR_PRIMARY, type: ShadingType.CLEAR }, margins: cellMargins, children: [new Paragraph({ children: [new TextRun({ text: "90", font: "Arial", size: 20, bold: true, color: COLOR_WHITE })] })] }),
    ] }),
  ],
}));

// ─── 10. Implementation Timeline ───
mainChildren.push(heading("10. Implementation Timeline", HeadingLevel.HEADING_1));

mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [1200, 3300, 2600, 2260],
  rows: [
    new TableRow({ children: [headerCell("Week", 1200), headerCell("Task", 3300), headerCell("Deliverable", 2600), headerCell("Status", 2260)] }),
    new TableRow({ children: [dataCell("Week 1", 1200, true), dataCell("Project setup, SLO parser, document ingestion", 3300, true), dataCell("Working ingestion pipeline", 2600, true), dataCell("Completed", 2260, true)] }),
    new TableRow({ children: [dataCell("Week 2", 1200), dataCell("Gemini integration, prompt engineering", 3300), dataCell("Content generation for 1 module", 2600), dataCell("Completed", 2260)] }),
    new TableRow({ children: [dataCell("Week 3", 1200, true), dataCell("PPT & PDF generation, formatting", 3300, true), dataCell("File builders tested with mock data", 2600, true), dataCell("Completed", 2260, true)] }),
    new TableRow({ children: [dataCell("Week 4", 1200), dataCell("n8n workflow, portal upload automation", 3300), dataCell("End-to-end pipeline", 2600), dataCell("Completed", 2260)] }),
    new TableRow({ children: [dataCell("Week 5", 1200, true), dataCell("End-to-end testing with Module 1, quality review", 3300, true), dataCell("Module 1 content on portal", 2600, true), dataCell("Pending (needs API key)", 2260, true)] }),
    new TableRow({ children: [dataCell("Week 6", 1200), dataCell("Generate all 5 modules, FA review", 3300), dataCell("All content uploaded", 2600), dataCell("Pending", 2260)] }),
    new TableRow({ children: [dataCell("Week 7\u20138", 1200, true), dataCell("Phase 2: Worksheet automation", 3300, true), dataCell("Worksheet generation pipeline", 2600, true), dataCell("Planned", 2260, true)] }),
  ],
}));

// ─── 11. Current Progress ───
mainChildren.push(heading("11. Current Progress", HeadingLevel.HEADING_1));
mainChildren.push(body("The following components have been built and tested:"));

mainChildren.push(boldBody("SLO/SRO Parser: ", "Successfully parses the Word document extracting all 5 modules, 45 sessions, and 90 SLOs with validation. Tested and verified against the actual document."));
mainChildren.push(boldBody("Document Extractor: ", "Supports PDF, DOCX, PPTX, and web URL text extraction. Ready for faculty source materials."));
mainChildren.push(boldBody("Gemini Integration: ", "Prompt templates engineered for SLO-aligned slide generation (8\u201312 slides per SLO) and PDF narrative consolidation. Uses structured JSON output mode for reliability."));
mainChildren.push(boldBody("PPT Generator: ", "Produces professional 16:9 PPTX files with title slides, content slides, and summary slides. Tested with mock data."));
mainChildren.push(boldBody("PDF Generator: ", "Produces A4 Learning Material PDFs with cover, TOC, session sections, and conclusion. Tested with mock data."));
mainChildren.push(boldBody("Portal Uploader: ", "Playwright-based browser automation for logging in and uploading to correct portal slots. Built with CAPTCHA handling."));
mainChildren.push(boldBody("n8n Workflow: ", "Importable JSON workflow that orchestrates all stages end-to-end."));

// ─── 12. Next Steps ───
mainChildren.push(heading("12. Next Steps \u2014 Requires FA Approval", HeadingLevel.HEADING_1));
mainChildren.push(body("To proceed with live testing and full content generation, the following are needed:"));

mainChildren.push(new Table({
  width: { size: 9360, type: WidthType.DXA },
  columnWidths: [600, 3200, 5560],
  rows: [
    new TableRow({ children: [headerCell("#", 600), headerCell("Requirement", 3200), headerCell("Details", 5560)] }),
    new TableRow({ children: [dataCell("1", 600, true), dataCell("Gemini API Key", 3200, true), dataCell("Free tier (Gemini 2.0 Flash) from Google AI Studio. No cost. Required to generate content.", 5560, true)] }),
    new TableRow({ children: [dataCell("2", 600), dataCell("Source Documents per Module", 3200), dataCell("Faculty-approved reference materials (PDFs, textbooks, notes) for each of the 5 modules. These are what the LLM uses to generate accurate content.", 5560)] }),
    new TableRow({ children: [dataCell("3", 600, true), dataCell("Portal Access Credentials", 3200, true), dataCell("Course Coordinator login for dld.srmist.edu.in to test automated upload. Can be deferred until content is reviewed.", 5560, true)] }),
    new TableRow({ children: [dataCell("4", 600), dataCell("FA Review of Module 1 Output", 3200), dataCell("After generating Module 1, FA reviews PPT and PDF quality, SLO alignment, and formatting before generating remaining modules.", 5560)] }),
  ],
}));

mainChildren.push(body(""));
mainChildren.push(body(
  "Once these are provided, Module 1 can be generated within hours and submitted for review. " +
  "After FA approval of Module 1 quality, all 5 modules can be generated in a single automated run."
));

const mainSection = {
  properties: {
    page: {
      size: { width: 12240, height: 15840 },
      margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
    },
  },
  headers: {
    default: new Header({
      children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "E-Curricula Automation \u2014 Project Proposal", font: "Arial", size: 18, color: "999999", italics: true })],
      })],
    }),
  },
  footers: {
    default: new Footer({
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Page ", font: "Arial", size: 18, color: "999999" }),
          new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 18, color: "999999" }),
        ],
      })],
    }),
  },
  children: mainChildren,
};

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 360, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: COLOR_PRIMARY },
        paragraph: { spacing: { before: 240, after: 180 }, outlineLevel: 1 } },
    ],
  },
  sections: [coverSection, mainSection],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync(process.argv[2] || "E-Curricula_Automation_Project_Plan.docx", buffer);
  console.log("Document created successfully.");
});
