"""FastAPI backend for E-Curricula Faculty UI."""

import asyncio
import json
import os
import shutil
import subprocess
import sys
import uuid
import zipfile
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

PROJECT_ROOT = Path(__file__).parent
OUTPUT_ROOT = PROJECT_ROOT / "output" / "21CSE597T"
INPUT_ROOT = PROJECT_ROOT / "input"
SLO_DOC_DIR = INPUT_ROOT / "slo_documents"

app = FastAPI(title="E-Curricula Generator API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job registry
jobs: dict[str, dict] = {}


@app.post("/api/upload/slo")
async def upload_slo(file: UploadFile = File(...)):
    """Save the uploaded SLO document to the input directory."""
    SLO_DOC_DIR.mkdir(parents=True, exist_ok=True)
    dest = SLO_DOC_DIR / file.filename
    content = await file.read()
    dest.write_bytes(content)
    return {"filename": file.filename, "size": len(content)}


@app.post("/api/generate")
async def start_generation(
    modules: str = Form(...),  # comma-separated e.g. "1,2,3"
):
    """Launch the pipeline in a background subprocess and return a job ID."""
    module_list = [m.strip() for m in modules.split(",") if m.strip()]
    if not module_list:
        raise HTTPException(status_code=400, detail="No modules specified")

    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "running", "log": [], "returncode": None}

    # Run pipeline in background task
    asyncio.create_task(_run_pipeline(job_id, module_list))

    return {"job_id": job_id}


async def _run_pipeline(job_id: str, module_list: list[str]):
    cmd = [
        sys.executable, "-m", "scripts.run_pipeline",
        "--modules", *module_list,
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=str(PROJECT_ROOT),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    async for raw in proc.stdout:
        line = raw.decode("utf-8", errors="replace").rstrip()
        jobs[job_id]["log"].append(line)
    await proc.wait()
    jobs[job_id]["returncode"] = proc.returncode
    jobs[job_id]["status"] = "done" if proc.returncode == 0 else "error"


@app.get("/api/status/{job_id}")
async def stream_status(job_id: str):
    """Server-Sent Events stream — sends log lines as they arrive."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_generator():
        sent = 0
        while True:
            job = jobs[job_id]
            log = job["log"]
            # Send any new lines
            while sent < len(log):
                line = log[sent]
                yield f"data: {json.dumps({'type': 'log', 'line': line})}\n\n"
                sent += 1
            if job["status"] in ("done", "error"):
                yield f"data: {json.dumps({'type': 'status', 'status': job['status'], 'returncode': job['returncode']})}\n\n"
                break
            await asyncio.sleep(0.3)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/modules")
async def list_modules():
    """Return which modules have generated output."""
    results = []
    for i in range(1, 6):
        ppt_dir = OUTPUT_ROOT / f"unit_{i}" / "ppts"
        pdf_path = OUTPUT_ROOT / f"unit_{i}" / f"unit_{i}_learning_material.pdf"
        ppt_count = len(list(ppt_dir.glob("*.pptx"))) if ppt_dir.exists() else 0
        results.append({
            "module": i,
            "ppt_count": ppt_count,
            "has_pdf": pdf_path.exists(),
        })
    return results


@app.get("/api/download/{module_num}")
async def download_module(module_num: int):
    """Return a zip of all PPTs + PDF for a module."""
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


@app.get("/api/download")
async def download_all():
    """Return a zip of all generated output."""
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
