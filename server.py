"""FastAPI backend for CurriculAI — production-secure edition."""

import asyncio
import json
import logging
import os
import re
import secrets
import sys
import uuid
import zipfile
from io import BytesIO
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Security, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from fastapi.security import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# ── paths ─────────────────────────────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).parent
OUTPUT_ROOT = PROJECT_ROOT / "output" / "21CSE597T"
INPUT_ROOT = PROJECT_ROOT / "input"
SLO_DOC_DIR = INPUT_ROOT / "slo_documents"

# ── config from environment (fail fast if required vars are missing) ───────────

INTERNAL_API_KEY: str = os.environ.get("INTERNAL_API_KEY", "")
if not INTERNAL_API_KEY:
    # Generate one and warn — operator must set this properly in prod
    INTERNAL_API_KEY = secrets.token_hex(32)
    print(
        f"WARNING: INTERNAL_API_KEY not set. Generated ephemeral key for this process: {INTERNAL_API_KEY}",
        file=sys.stderr,
    )

ALLOWED_ORIGINS: list[str] = [
    o.strip()
    for o in os.environ.get(
        "ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
    if o.strip()
]

PRODUCTION: bool = os.environ.get("PRODUCTION", "false").lower() == "true"

# ── logging + redaction ───────────────────────────────────────────────────────

_SECRET_PATTERN = re.compile(
    r"(password|passwd|api[_\-]?key|token|secret|credential|authorization)[=:\s]+\S+",
    re.IGNORECASE,
)


def _redact(text: str) -> str:
    return _SECRET_PATTERN.sub(r"\1=[REDACTED]", text)


class RedactionFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = _redact(str(record.msg))
        if record.args:
            record.args = tuple(_redact(str(a)) for a in record.args)
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
for handler in logging.root.handlers:
    handler.addFilter(RedactionFilter())

logger = logging.getLogger("curricul-ai")

# ── job registries ────────────────────────────────────────────────────────────
#
# Note: we deliberately do NOT handle eCurricula portal credentials. The upload
# runs a visible browser on the professor's own machine; they type their own
# username/password and solve the captcha there. We never see or store it.

jobs: dict[str, dict] = {}          # generation jobs
upload_jobs: dict[str, dict] = {}   # upload jobs

# ── FastAPI + rate limiter ────────────────────────────────────────────────────

limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="CurriculAI API", docs_url=None, redoc_url=None)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Session-Id"],
    allow_credentials=False,
)


# Explicit CSP. `default-src 'self'` alone silently blocked the app's own
# Google Fonts and inline styles; this states exactly what the UI needs while
# keeping script-src locked to same-origin (no 'unsafe-inline' for scripts).
_CSP = "; ".join([
    "default-src 'self'",
    "script-src 'self'",
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
    "font-src 'self' https://fonts.gstatic.com",
    "img-src 'self' data:",
    "connect-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "frame-ancestors 'none'",
])


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = _CSP
    return response


# ── authentication ────────────────────────────────────────────────────────────

_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def require_api_key(key: str = Security(_api_key_header)) -> None:
    if not secrets.compare_digest(key, INTERNAL_API_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")


# ── file upload helpers ───────────────────────────────────────────────────────

_ALLOWED_EXTENSIONS = {".docx", ".doc", ".pdf"}
_MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

# Magic bytes for allowed MIME types
_MAGIC_SIGNATURES: dict[bytes, str] = {
    b"PK\x03\x04": "docx/xlsx/zip",          # DOCX (Office Open XML is a ZIP)
    b"\xd0\xcf\x11\xe0": "doc",              # Legacy .doc (Compound Document)
    b"%PDF": "pdf",                           # PDF
}


def _validate_file_content(content: bytes, extension: str) -> None:
    header = content[:8]
    matched = any(header.startswith(sig) for sig in _MAGIC_SIGNATURES)
    if not matched:
        raise HTTPException(status_code=400, detail="File content does not match declared type")


# ── endpoints ─────────────────────────────────────────────────────────────────


@app.post("/api/upload/slo", dependencies=[Depends(require_api_key)])
async def upload_slo(file: UploadFile = File(...)):
    """Accept an SLO document, validate it, save with a safe UUID name."""
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Only {_ALLOWED_EXTENSIONS} accepted")

    content = await file.read()
    if len(content) > _MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    _validate_file_content(content, suffix)

    SLO_DOC_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = f"slo_{uuid.uuid4().hex}{suffix}"
    dest = SLO_DOC_DIR / safe_name
    dest.write_bytes(content)
    logger.info("SLO uploaded: %s (%d bytes)", safe_name, len(content))
    return {"stored_as": safe_name, "size": len(content)}


def _resolve_slo_doc(stored_as: str) -> Optional[Path]:
    """Resolve an uploaded SLO filename to a safe path inside SLO_DOC_DIR.

    Guards against path traversal: only a bare filename that actually lives in
    SLO_DOC_DIR is accepted. Returns None if the input is empty.
    """
    stored_as = (stored_as or "").strip()
    if not stored_as:
        return None
    # Reject anything that isn't a plain filename
    if stored_as != Path(stored_as).name:
        raise HTTPException(status_code=400, detail="Invalid slo_doc filename")
    candidate = (SLO_DOC_DIR / stored_as).resolve()
    if candidate.parent != SLO_DOC_DIR.resolve() or not candidate.is_file():
        raise HTTPException(status_code=400, detail="slo_doc not found")
    return candidate


@app.post("/api/generate", dependencies=[Depends(require_api_key)])
@limiter.limit("3/minute")
async def start_generation(
    request: Request,
    modules: str = Form(...),
    slo_doc: str = Form(""),
):
    """Launch the generation pipeline. Returns a job_id for polling.

    `slo_doc` is the `stored_as` filename returned by /api/upload/slo. When
    omitted, the pipeline falls back to the default document in settings.yaml.
    """
    module_list = [m.strip() for m in modules.split(",") if m.strip().isdigit()]
    if not module_list or not all(1 <= int(m) <= 5 for m in module_list):
        raise HTTPException(status_code=400, detail="modules must be 1–5 comma-separated integers")

    slo_path = _resolve_slo_doc(slo_doc)

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "log": [], "returncode": None}
    asyncio.create_task(_run_pipeline(job_id, module_list, slo_path))
    logger.info("Generation job started: %s modules=%s slo=%s", job_id[:8], module_list, bool(slo_path))
    return {"job_id": job_id}


async def _run_job(job_id: str, cmd: list[str]):
    """Generic subprocess job runner streaming stdout into the job log."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,   # separate — never forwarded to browser
    )

    async def _read_stdout():
        async for raw in proc.stdout:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            jobs[job_id]["log"].append(line)

    async def _drain_stderr():
        async for raw in proc.stderr:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            logger.warning("job stderr [%s]: %s", job_id[:8], line)

    await asyncio.gather(_read_stdout(), _drain_stderr())
    await proc.wait()
    jobs[job_id]["returncode"] = proc.returncode
    jobs[job_id]["status"] = "done" if proc.returncode == 0 else "error"
    logger.info("Job %s finished: %s", job_id[:8], jobs[job_id]["status"])


async def _run_pipeline(job_id: str, module_list: list[str], slo_path: Optional[Path] = None):
    cmd = [sys.executable, "-m", "scripts.run_pipeline", "--modules", *module_list]
    if slo_path:
        cmd += ["--slo-doc", str(slo_path)]
    await _run_job(job_id, cmd)


@app.get("/api/job/{job_id}", dependencies=[Depends(require_api_key)])
async def job_status(job_id: str):
    """Plain JSON poll endpoint for n8n."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    job = jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "log_lines": len(job["log"]),
        "last_log": job["log"][-1] if job["log"] else "",
    }


@app.get("/api/status/{job_id}", dependencies=[Depends(require_api_key)])
async def stream_status(job_id: str):
    """SSE stream for the React UI (not used by n8n)."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        sent = 0
        while True:
            job = jobs[job_id]
            log = job["log"]
            while sent < len(log):
                yield f"data: {json.dumps({'type': 'log', 'line': log[sent]})}\n\n"
                sent += 1
            if job["status"] in ("done", "error"):
                yield f"data: {json.dumps({'type': 'status', 'status': job['status']})}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/upload", dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def start_upload(request: Request, body: dict):
    """
    Trigger the eCurricula portal upload. Opens a VISIBLE browser on this
    machine; the professor types their own portal credentials and solves the
    captcha there. We never receive or store any credentials.
    Body: { "modules": [1,2,3,4,5] }
    """
    modules = body.get("modules", list(range(1, 6)))
    if not all(isinstance(m, int) and 1 <= m <= 5 for m in modules):
        raise HTTPException(status_code=400, detail="modules must be integers 1–5")

    upload_job_id = str(uuid.uuid4())
    upload_jobs[upload_job_id] = {"status": "running", "log": [], "returncode": None}
    asyncio.create_task(_run_upload(upload_job_id, modules))
    logger.info("Upload job started: %s modules=%s", upload_job_id[:8], modules)
    return {"upload_job_id": upload_job_id}


async def _run_upload(upload_job_id: str, modules: list[int]):
    # Headful + manual login: the browser opens on the professor's screen so
    # they can enter their own credentials and solve the captcha themselves.
    decision_file = OUTPUT_ROOT.parent / f".upload_decision_{upload_job_id}.json"
    upload_jobs[upload_job_id]["decision_file"] = str(decision_file)

    upload_env = {
        **os.environ,
        "PORTAL_HEADLESS": "0",
        "PORTAL_MANUAL_LOGIN": "1",
        "PORTAL_PRODUCTION": "1" if PRODUCTION else "0",
        # Never silently overwrite the faculty's own uploads: scan first,
        # then pause for their replace/skip decision (relayed via file).
        "PORTAL_ON_CONFLICT": "ask",
        "UPLOAD_DECISION_FILE": str(decision_file),
    }

    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "scripts.upload.portal_upload",
        "--output-dir", str(OUTPUT_ROOT),
        "--modules", *map(str, modules),
        env=upload_env,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _read_out():
        async for raw in proc.stdout:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            upload_jobs[upload_job_id]["log"].append(line)
            # Marker lines from the subprocess drive the conflict handshake
            if "CONFLICTS_JSON:" in line:
                try:
                    payload = json.loads(line.split("CONFLICTS_JSON:", 1)[1].strip())
                    upload_jobs[upload_job_id]["conflicts"] = payload
                    upload_jobs[upload_job_id]["status"] = "awaiting_decision"
                except Exception:
                    logger.warning("Unparseable CONFLICTS_JSON line [%s]", upload_job_id[:8])
            elif "DECISION_RECEIVED:" in line:
                upload_jobs[upload_job_id]["status"] = "running"

    async def _drain_err():
        async for raw in proc.stderr:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            logger.warning("upload stderr [%s]: %s", upload_job_id[:8], line)

    try:
        await asyncio.gather(_read_out(), _drain_err())
        await proc.wait()
        upload_jobs[upload_job_id]["returncode"] = proc.returncode
        upload_jobs[upload_job_id]["status"] = "done" if proc.returncode == 0 else "error"
        logger.info("Upload job %s finished: %s", upload_job_id[:8], upload_jobs[upload_job_id]["status"])
    finally:
        decision_file.unlink(missing_ok=True)


@app.post("/api/upload-decision/{upload_job_id}", dependencies=[Depends(require_api_key)])
async def upload_decision(upload_job_id: str, body: dict):
    """Professor's answer to the replace/skip question for existing uploads."""
    job = upload_jobs.get(upload_job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Upload job not found")
    if job.get("status") != "awaiting_decision":
        raise HTTPException(status_code=409, detail="Job is not awaiting a decision")

    decision = str(body.get("decision", "")).lower()
    if decision not in ("replace", "skip"):
        raise HTTPException(status_code=400, detail="decision must be 'replace' or 'skip'")

    Path(job["decision_file"]).write_text(json.dumps({"decision": decision}))
    job["status"] = "running"
    job["log"].append(f"Professor chose: {decision.upper()} existing uploads")
    logger.info("Upload job %s decision: %s", upload_job_id[:8], decision)
    return {"ok": True, "decision": decision}


@app.get("/api/upload-job/{upload_job_id}", dependencies=[Depends(require_api_key)])
async def upload_job_status(upload_job_id: str):
    """Poll upload job status — used by n8n and the React UI."""
    if upload_job_id not in upload_jobs:
        raise HTTPException(status_code=404, detail="Upload job not found")
    job = upload_jobs[upload_job_id]
    return {
        "upload_job_id": upload_job_id,
        "status": job["status"],
        "log_lines": len(job["log"]),
        "last_log": job["log"][-1] if job["log"] else "",
        "conflicts": job.get("conflicts"),
    }


# ── question bank ─────────────────────────────────────────────────────────────


@app.post("/api/questions/generate", dependencies=[Depends(require_api_key)])
@limiter.limit("3/minute")
async def start_question_generation(request: Request, modules: str = Form(...)):
    """Generate the MCQ/short/long question bank + review PDF per module."""
    module_list = [m.strip() for m in modules.split(",") if m.strip().isdigit()]
    if not module_list or not all(1 <= int(m) <= 5 for m in module_list):
        raise HTTPException(status_code=400, detail="modules must be 1–5 comma-separated integers")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "log": [], "returncode": None}
    cmd = [sys.executable, "-m", "scripts.generate.question_gen", "--modules", *module_list]
    asyncio.create_task(_run_job(job_id, cmd))
    logger.info("Question generation job started: %s modules=%s", job_id[:8], module_list)
    return {"job_id": job_id}


@app.get("/api/questions/info", dependencies=[Depends(require_api_key)])
async def question_info():
    """Which modules have a generated question bank + review PDF."""
    results = []
    for i in range(1, 6):
        qjson = OUTPUT_ROOT / f"unit_{i}" / "questions.json"
        qpdf = OUTPUT_ROOT / f"unit_{i}" / f"unit_{i}_question_bank.pdf"
        entry = {"module": i, "has_questions": qjson.exists(), "has_pdf": qpdf.exists()}
        if qjson.exists():
            try:
                data = json.loads(qjson.read_text())
                entry["sessions"] = len(data.get("sessions", []))
                entry["total_questions"] = sum(
                    len(s.get("mcqs", [])) + len(s.get("short_questions", []))
                    + len(s.get("long_questions", []))
                    for s in data.get("sessions", [])
                )
            except Exception:
                pass
        results.append(entry)
    return results


def _qbank_paths(module_num: int) -> tuple[Path, Path]:
    unit_dir = OUTPUT_ROOT / f"unit_{module_num}"
    return unit_dir / "questions.json", unit_dir / f"unit_{module_num}_question_bank.pdf"


# Portal-enforced minimums per session
_MIN_COUNTS = {"mcqs": 5, "short_questions": 2, "long_questions": 1}


@app.get("/api/questions/bank/{module_num}", dependencies=[Depends(require_api_key)])
async def get_question_bank(module_num: int):
    """Full question bank for the in-app editor."""
    if not 1 <= module_num <= 5:
        raise HTTPException(status_code=400, detail="module_num must be 1–5")
    qjson, _ = _qbank_paths(module_num)
    if not qjson.exists():
        raise HTTPException(status_code=404, detail="No question bank — generate first")
    return json.loads(qjson.read_text())


@app.put("/api/questions/bank/{module_num}", dependencies=[Depends(require_api_key)])
async def save_question_bank(module_num: int, body: dict):
    """Save the faculty-edited bank; re-sanitize and rebuild the review PDF."""
    if not 1 <= module_num <= 5:
        raise HTTPException(status_code=400, detail="module_num must be 1–5")
    qjson, qpdf = _qbank_paths(module_num)
    if not qjson.exists():
        raise HTTPException(status_code=404, detail="No question bank — generate first")

    sessions = body.get("sessions")
    if not isinstance(sessions, list) or not sessions:
        raise HTTPException(status_code=400, detail="sessions list required")

    from scripts.generate.question_gen import _sanitize

    problems = []
    for s in sessions:
        for kind, minimum in _MIN_COUNTS.items():
            if len(s.get(kind, [])) < minimum:
                problems.append(
                    f"Session {s.get('session')}: {kind.replace('_', ' ')} below "
                    f"portal minimum ({minimum})")
        _sanitize(s)  # clamp levels/verbs/POs in place

    if problems:
        raise HTTPException(status_code=422, detail="; ".join(problems))

    existing = json.loads(qjson.read_text())
    existing["sessions"] = sorted(sessions, key=lambda s: s.get("session", 0))
    existing["edited"] = True
    qjson.write_text(json.dumps(existing, indent=2))

    # Rebuild the review PDF so the audit record matches what will be uploaded
    from scripts.build.create_question_pdf import create_question_pdf
    create_question_pdf(existing, str(qpdf))
    logger.info("Question bank saved (edited) for module %d", module_num)
    return {"ok": True, "edited": True}


@app.post("/api/questions/regenerate", dependencies=[Depends(require_api_key)])
@limiter.limit("10/minute")
async def regenerate_question(request: Request, body: dict):
    """Replace ONE question via Gemini, guided by optional faculty feedback."""
    try:
        module_num = int(body.get("module", 0))
        session_num = int(body.get("session", 0))
        index = int(body.get("index", -1))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="module/session/index must be integers")
    kind = str(body.get("kind", ""))
    # Cap feedback length — it is injected into the Gemini prompt.
    feedback = str(body.get("feedback", "")).strip()[:500] or \
        "Improve the quality and clarity of this question."

    if not 1 <= module_num <= 5:
        raise HTTPException(status_code=400, detail="module must be 1–5")
    if kind not in _MIN_COUNTS:
        raise HTTPException(status_code=400, detail=f"kind must be one of {list(_MIN_COUNTS)}")
    qjson, qpdf = _qbank_paths(module_num)
    if not qjson.exists():
        raise HTTPException(status_code=404, detail="No question bank — generate first")

    bank = json.loads(qjson.read_text())
    sess = next((s for s in bank["sessions"] if s.get("session") == session_num), None)
    if not sess or not 0 <= index < len(sess.get(kind, [])):
        raise HTTPException(status_code=404, detail="Question not found")
    existing_q = sess[kind][index]

    def _generate() -> dict:
        from scripts.generate.gemini_content_gen import (
            _call_with_retry, init_gemini, load_settings)
        from scripts.generate.prompt_templates import QUESTION_REGEN_PROMPT
        from scripts.generate.question_gen import _parse_json_response, _sanitize
        import google.generativeai as genai

        settings = load_settings()
        kind_label = {"mcqs": "Multiple Choice (4 options, 1 correct)",
                      "short_questions": "Short answer (with model answer)",
                      "long_questions": "Long answer (with model answer)"}[kind]
        prompt = QUESTION_REGEN_PROMPT.format(
            course_code=settings["course"]["code"],
            course_name=settings["course"]["name"],
            module_num=module_num,
            module_title=bank.get("module_title", ""),
            kind_label=kind_label,
            existing_question=json.dumps(existing_q, indent=2),
            feedback=feedback,
        )
        model = init_gemini()
        cfg = genai.GenerationConfig(temperature=0.4, max_output_tokens=4096,
                                     response_mime_type="application/json")
        response = _call_with_retry(model, prompt, cfg)
        new_q = _parse_json_response(response.text)
        return _sanitize({kind: [new_q]})[kind][0]

    try:
        new_q = await asyncio.to_thread(_generate)
    except Exception as e:
        logger.error("Question regeneration failed: %s", str(e)[:200])
        raise HTTPException(status_code=502, detail="Gemini regeneration failed — try again")

    sess[kind][index] = new_q
    bank["edited"] = True
    qjson.write_text(json.dumps(bank, indent=2))
    from scripts.build.create_question_pdf import create_question_pdf
    create_question_pdf(bank, str(qpdf))
    logger.info("Regenerated %s[%d] for module %d session %d", kind, index,
                module_num, session_num)
    return {"ok": True, "question": new_q}


@app.get("/api/questions/download/{module_num}", dependencies=[Depends(require_api_key)])
async def download_question_pdf(module_num: int):
    if not 1 <= module_num <= 5:
        raise HTTPException(status_code=400, detail="module_num must be 1–5")
    pdf = OUTPUT_ROOT / f"unit_{module_num}" / f"unit_{module_num}_question_bank.pdf"
    if not pdf.exists():
        raise HTTPException(status_code=404, detail="Question bank PDF not found")
    return Response(
        content=pdf.read_bytes(),
        media_type="application/pdf",
        headers={"Content-Disposition":
                 f"attachment; filename=module_{module_num}_question_bank.pdf"},
    )


@app.post("/api/questions/publish", dependencies=[Depends(require_api_key)])
@limiter.limit("5/minute")
async def publish_questions(request: Request, body: dict):
    """Auto-fill the portal's MCQ/Short/Long forms from the approved bank.

    Opens a visible browser (professor logs in + captcha), then the automation
    enters every question with its metadata.
    """
    modules = body.get("modules", list(range(1, 6)))
    if not all(isinstance(m, int) and 1 <= m <= 5 for m in modules):
        raise HTTPException(status_code=400, detail="modules must be integers 1–5")

    missing = [m for m in modules
               if not (OUTPUT_ROOT / f"unit_{m}" / "questions.json").exists()]
    if missing:
        raise HTTPException(status_code=409,
                            detail=f"No question bank for modules {missing} — generate first")

    upload_job_id = str(uuid.uuid4())
    upload_jobs[upload_job_id] = {"status": "running", "log": [], "returncode": None}
    asyncio.create_task(_run_question_publish(upload_job_id, modules))
    logger.info("Question publish job started: %s modules=%s", upload_job_id[:8], modules)
    return {"upload_job_id": upload_job_id}


async def _run_question_publish(upload_job_id: str, modules: list[int]):
    # Same conflict handshake as file uploads: scan the portal's question
    # tables first, pause for the professor's replace/keep decision.
    decision_file = OUTPUT_ROOT.parent / f".upload_decision_{upload_job_id}.json"
    upload_jobs[upload_job_id]["decision_file"] = str(decision_file)

    upload_env = {
        **os.environ,
        "PORTAL_HEADLESS": "0",
        "PORTAL_MANUAL_LOGIN": "1",
        "PORTAL_PRODUCTION": "1" if PRODUCTION else "0",
        "PORTAL_ON_CONFLICT": "ask",
        "UPLOAD_DECISION_FILE": str(decision_file),
    }
    proc = await asyncio.create_subprocess_exec(
        sys.executable, "-m", "scripts.upload.portal_upload",
        "--output-dir", str(OUTPUT_ROOT),
        "--modules", *map(str, modules),
        "--questions",
        env=upload_env,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    async def _read_out():
        async for raw in proc.stdout:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            upload_jobs[upload_job_id]["log"].append(line)
            if "CONFLICTS_JSON:" in line:
                try:
                    payload = json.loads(line.split("CONFLICTS_JSON:", 1)[1].strip())
                    upload_jobs[upload_job_id]["conflicts"] = payload
                    upload_jobs[upload_job_id]["status"] = "awaiting_decision"
                except Exception:
                    logger.warning("Unparseable CONFLICTS_JSON [%s]", upload_job_id[:8])
            elif "DECISION_RECEIVED:" in line:
                upload_jobs[upload_job_id]["status"] = "running"

    async def _drain_err():
        async for raw in proc.stderr:
            line = _redact(raw.decode("utf-8", errors="replace").rstrip())
            logger.warning("qpublish stderr [%s]: %s", upload_job_id[:8], line)

    try:
        await asyncio.gather(_read_out(), _drain_err())
        await proc.wait()
        upload_jobs[upload_job_id]["returncode"] = proc.returncode
        upload_jobs[upload_job_id]["status"] = "done" if proc.returncode == 0 else "error"
        logger.info("Question publish %s finished: %s", upload_job_id[:8],
                    upload_jobs[upload_job_id]["status"])
    finally:
        decision_file.unlink(missing_ok=True)


@app.get("/api/modules", dependencies=[Depends(require_api_key)])
async def list_modules():
    results = []
    for i in range(1, 6):
        ppt_dir = OUTPUT_ROOT / f"unit_{i}" / "ppts"
        pdf_path = OUTPUT_ROOT / f"unit_{i}" / f"unit_{i}_learning_material.pdf"
        ppt_count = len(list(ppt_dir.glob("*.pptx"))) if ppt_dir.exists() else 0
        results.append({"module": i, "ppt_count": ppt_count, "has_pdf": pdf_path.exists()})
    return results


@app.get("/api/download/{module_num}", dependencies=[Depends(require_api_key)])
async def download_module(module_num: int):
    if not 1 <= module_num <= 5:
        raise HTTPException(status_code=400, detail="module_num must be 1–5")
    unit_dir = OUTPUT_ROOT / f"unit_{module_num}"
    if not unit_dir.exists():
        raise HTTPException(status_code=404, detail="Module output not found")

    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        ppt_dir = unit_dir / "ppts"
        if ppt_dir.exists():
            for f in sorted(ppt_dir.glob("*.pptx")):
                zf.write(f, f"module_{module_num}/ppts/{f.name}")
        pdf = unit_dir / f"unit_{module_num}_learning_material.pdf"
        if pdf.exists():
            zf.write(pdf, f"module_{module_num}/{pdf.name}")
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=module_{module_num}.zip"},
    )


@app.get("/api/download", dependencies=[Depends(require_api_key)])
async def download_all():
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for i in range(1, 6):
            unit_dir = OUTPUT_ROOT / f"unit_{i}"
            if not unit_dir.exists():
                continue
            ppt_dir = unit_dir / "ppts"
            if ppt_dir.exists():
                for f in sorted(ppt_dir.glob("*.pptx")):
                    zf.write(f, f"module_{i}/ppts/{f.name}")
            pdf = unit_dir / f"unit_{i}_learning_material.pdf"
            if pdf.exists():
                zf.write(pdf, f"module_{i}/{pdf.name}")
    buf.seek(0)
    return Response(
        content=buf.read(),
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=21CSE597T_all_modules.zip"},
    )


# ── serve the built React UI (same origin as the API) ──────────────────────────
# Mounted last so it doesn't shadow the /api/* routes above. Run `npm run build`
# in ui/ (the launcher does this) to produce ui/dist.

from fastapi.staticfiles import StaticFiles  # noqa: E402

_UI_DIST = PROJECT_ROOT / "ui" / "dist"
if _UI_DIST.exists():
    app.mount("/", StaticFiles(directory=str(_UI_DIST), html=True), name="ui")
else:
    logger.warning("UI build not found at %s — run 'npm run build' in ui/", _UI_DIST)
