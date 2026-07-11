import { useState, useEffect, useRef } from "react";
import { motion } from "framer-motion";
import Header from "./components/Header";
import Hero from "./components/Hero";
import Stepper from "./components/Stepper";
import UploadZone from "./components/UploadZone";
import ModuleSelector from "./components/ModuleSelector";
import GenerateButton from "./components/GenerateButton";
import ProgressLog from "./components/ProgressLog";
import DownloadPanel from "./components/DownloadPanel";
import StatusBadge from "./components/StatusBadge";
import QuestionBank from "./components/QuestionBank";
import QuestionEditor from "./components/QuestionEditor";
import { API, API_KEY, apiFetch, streamJobStatus } from "./lib/api";

const cardVariants = {
  hidden: { opacity: 0, y: 24 },
  show: (i) => ({
    opacity: 1,
    y: 0,
    transition: { delay: 0.3 + i * 0.12, type: "spring", stiffness: 120, damping: 16 },
  }),
};

function GlassCard({ step, title, children, custom }) {
  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="show"
      custom={custom}
      className="glass rounded-2xl shadow-glass p-6"
    >
      <h2 className="text-base font-bold text-navy mb-4 flex items-center gap-2.5">
        <span className="bg-gradient-to-br from-navy to-navy-light text-white text-xs rounded-full w-6 h-6 flex items-center justify-center shadow-sm">
          {step}
        </span>
        {title}
      </h2>
      {children}
    </motion.div>
  );
}

export default function App() {
  // Hash route: "#/edit/N" opens the full-page question editor (own tab,
  // big-screen editing). Everything else renders the normal app.
  const [hash, setHash] = useState(window.location.hash);
  useEffect(() => {
    const onHash = () => setHash(window.location.hash);
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const editMatch = hash.match(/^#\/edit\/([1-5])$/);
  if (editMatch) {
    return (
      <div className="min-h-screen">
        <div className="mesh-bg" />
        <Header />
        <main className="max-w-6xl mx-auto px-4 py-8">
          <QuestionEditor
            api={API}
            apiKey={API_KEY}
            module={Number(editMatch[1])}
            fullPage
            onClose={() => {
              window.close();
              // if the browser refuses to close a non-scripted tab:
              window.location.hash = "";
            }}
          />
        </main>
      </div>
    );
  }

  return <MainApp />;
}

function MainApp() {
  const [sloFile, setSloFile] = useState(null);
  const [selectedModules, setSelectedModules] = useState([1, 2, 3, 4, 5]);
  const [jobStatus, setJobStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [moduleInfo, setModuleInfo] = useState([]);
  // Human-in-the-loop: professor must confirm they reviewed the content
  const [reviewed, setReviewed] = useState(false);
  // Existing-upload conflicts reported by the automation (awaiting decision)
  const [conflicts, setConflicts] = useState(null);
  const uploadJobIdRef = useRef(null);

  useEffect(() => {
    fetchModuleInfo();
  }, []);

  async function fetchModuleInfo() {
    try {
      const res = await apiFetch("/api/modules");
      if (res.ok) setModuleInfo(await res.json());
    } catch (_) {}
  }

  async function handleGenerate() {
    if (!sloFile || selectedModules.length === 0) return;

    setLogs([]);
    setJobStatus("uploading");

    // 1. Upload SLO file
    const form = new FormData();
    form.append("file", sloFile);
    const uploadRes = await apiFetch("/api/upload/slo", { method: "POST", body: form });
    if (!uploadRes.ok) {
      setJobStatus("error");
      setLogs(["ERROR: Failed to upload SLO document."]);
      return;
    }
    const { stored_as } = await uploadRes.json();

    // 2. Start generation — pass the just-uploaded SLO so it's actually used
    const genForm = new FormData();
    genForm.append("modules", selectedModules.join(","));
    genForm.append("slo_doc", stored_as);
    const genRes = await apiFetch("/api/generate", { method: "POST", body: genForm });
    if (!genRes.ok) {
      setJobStatus("error");
      setLogs(["ERROR: Failed to start generation."]);
      return;
    }
    const { job_id } = await genRes.json();
    setJobStatus("running");

    // 3. Stream generation progress (authenticated fetch-stream — the API key
    // stays in the header, never in the URL). Portal upload is a SEPARATE,
    // professor-initiated step (it opens a browser for them) — not auto-chained.
    streamJobStatus(
      job_id,
      async (data) => {
        if (data.type === "log") {
          setLogs((prev) => [...prev, data.line]);
        } else if (data.type === "status") {
          if (data.status === "done") {
            setJobStatus("done");
            await fetchModuleInfo();
          } else {
            setJobStatus("error");
          }
        }
      },
      (end) => {
        if (end === "error") {
          setJobStatus((prev) => (prev === "running" ? "error" : prev));
        }
      }
    );
  }

  async function startPortalUpload() {
    setJobStatus("uploading_portal");
    setLogs((prev) => [
      ...prev,
      "── Opening eCurricula in a browser window ──",
      "Enter your eCurricula login + captcha in the window that opens.",
    ]);

    const res = await apiFetch("/api/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modules: selectedModules }),
    });
    if (!res.ok) {
      setJobStatus("upload_error");
      setLogs((prev) => [...prev, "ERROR: Failed to start portal upload."]);
      return;
    }
    const { upload_job_id } = await res.json();
    uploadJobIdRef.current = upload_job_id;
    pollUploadStatus(upload_job_id);
  }

  async function pollUploadStatus(upload_job_id) {
    const interval = setInterval(async () => {
      try {
        const res = await apiFetch(`/api/upload-job/${upload_job_id}`);
        if (!res.ok) return;
        const data = await res.json();
        if (data.last_log) {
          setLogs((prev) => {
            const last = prev[prev.length - 1];
            return last === data.last_log ? prev : [...prev, data.last_log];
          });
        }
        if (data.status === "awaiting_decision") {
          setJobStatus("awaiting_decision");
          if (data.conflicts) setConflicts(data.conflicts);
        } else if (data.status === "running") {
          setConflicts(null);
          setJobStatus((prev) => (prev === "awaiting_decision" ? "uploading_portal" : prev));
        } else if (data.status === "done") {
          clearInterval(interval);
          setConflicts(null);
          setJobStatus("upload_done");
          setLogs((prev) => [...prev, "✅ All files uploaded to eCurricula portal!"]);
        } else if (data.status === "error") {
          clearInterval(interval);
          setConflicts(null);
          setJobStatus("upload_error");
          setLogs((prev) => [...prev, "❌ Portal upload failed — check server logs."]);
        }
      } catch (_) {}
    }, 5000);
  }

  async function sendConflictDecision(decision) {
    const id = uploadJobIdRef.current;
    if (!id) return;
    const res = await apiFetch(`/api/upload-decision/${id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    });
    if (res.ok) {
      setConflicts(null);
      setJobStatus("uploading_portal");
      setLogs((prev) => [
        ...prev,
        decision === "replace"
          ? "→ Replacing existing files with AI-generated versions"
          : "→ Keeping existing files, uploading only to empty slots",
      ]);
    }
  }

  const isBusy =
    jobStatus === "uploading" ||
    jobStatus === "running" ||
    jobStatus === "uploading_portal" ||
    jobStatus === "awaiting_decision";

  const canStart = sloFile && selectedModules.length > 0 && !isBusy;

  const hasOutput = moduleInfo.some((m) => m.ppt_count > 0 || m.has_pdf);

  // Generation has finished and there are files to push to the portal.
  const canUploadToPortal =
    (jobStatus === "done" || jobStatus === "upload_error" || jobStatus === "upload_done" ||
      (jobStatus === null && hasOutput)) && hasOutput;

  return (
    <div className="min-h-screen">
      {/* animated background */}
      <div className="mesh-bg" />
      <div className="orb w-96 h-96 bg-navy/20 top-[-80px] left-[-120px] animate-float" />
      <div className="orb w-80 h-80 bg-maroon/15 top-[30%] right-[-100px] animate-float-slow" />
      <div className="orb w-72 h-72 bg-blue-400/20 bottom-[-60px] left-[30%] animate-float" />

      <Header />
      <Hero />

      <div className="max-w-6xl mx-auto px-4 pb-2">
        <Stepper jobStatus={jobStatus} hasFile={!!sloFile} hasOutput={hasOutput} />
      </div>

      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panel */}
        <div className="lg:col-span-1 space-y-4">
          <GlassCard step="1" title="Upload SLO Document" custom={0}>
            <UploadZone file={sloFile} onFileChange={setSloFile} disabled={isBusy} />
          </GlassCard>

          <GlassCard step="2" title="Select Modules" custom={1}>
            <ModuleSelector
              selected={selectedModules}
              onChange={setSelectedModules}
              moduleInfo={moduleInfo}
              disabled={isBusy}
            />
          </GlassCard>

          <motion.div variants={cardVariants} initial="hidden" animate="show" custom={2}>
            <GenerateButton
              onClick={handleGenerate}
              disabled={!canStart}
              isGenerating={isBusy}
            />
          </motion.div>

          {canUploadToPortal && (
            <GlassCard step="3" title="Publish to eCurricula" custom={3}>
              {/* Human-in-the-loop: force a review before anything goes live */}
              <div className="mb-3 rounded-xl bg-amber-50/90 border border-amber-200 px-3 py-2.5">
                <p className="text-xs text-amber-800 font-semibold mb-1">
                  ⚠️ Review before publishing
                </p>
                <p className="text-[11px] text-amber-700 leading-relaxed">
                  Download the generated PPTs and PDF from the panel on the right
                  and review them. AI-generated content must be checked by faculty
                  before it reaches students.
                </p>
              </div>
              <label className="flex items-start gap-2 mb-3 cursor-pointer select-none">
                <input
                  type="checkbox"
                  checked={reviewed}
                  onChange={(e) => setReviewed(e.target.checked)}
                  disabled={isBusy}
                  className="mt-0.5 w-4 h-4 accent-maroon"
                />
                <span className="text-xs text-slate-600 leading-snug">
                  I have downloaded and reviewed the generated content
                </span>
              </label>
              <p className="text-xs text-slate-500 mb-3 leading-relaxed">
                A browser window will open. Sign in to eCurricula and solve the
                captcha yourself — the upload then runs automatically. Your
                credentials never touch this app.
              </p>
              <motion.button
                whileHover={!reviewed || isBusy ? {} : { scale: 1.02 }}
                whileTap={!reviewed || isBusy ? {} : { scale: 0.97 }}
                onClick={startPortalUpload}
                disabled={!reviewed || isBusy}
                className="btn-shine w-full bg-gradient-to-r from-navy to-navy-light text-white rounded-xl py-3 font-bold disabled:opacity-50 shadow-glass"
              >
                {jobStatus === "uploading_portal" || jobStatus === "awaiting_decision"
                  ? "Uploading…"
                  : "🚀 Open eCurricula & Upload"}
              </motion.button>
            </GlassCard>
          )}

          {conflicts && jobStatus === "awaiting_decision" && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 12 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              className="glass rounded-2xl shadow-glass-lg p-5 border-2 border-amber-300"
            >
              <h3 className="text-sm font-bold text-navy mb-2 flex items-center gap-2">
                <span>📌</span> Existing files found on the portal
              </h3>
              <div className="text-xs text-slate-600 mb-3 space-y-1">
                {Object.entries(conflicts).map(([unit, info]) => (
                  <p key={unit}>
                    <span className="font-semibold">Module {unit}:</span>{" "}
                    {[
                      info.pptx?.length ? `${info.pptx.length} PPT slot${info.pptx.length > 1 ? "s" : ""}` : null,
                      info.lm ? "Learning Material" : null,
                    ].filter(Boolean).join(" + ")}
                  </p>
                ))}
              </div>
              <p className="text-[11px] text-slate-500 mb-3">
                These were uploaded previously (possibly by you). What should we do?
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => sendConflictDecision("replace")}
                  className="flex-1 bg-gradient-to-r from-maroon to-maroon-light text-white text-xs font-bold rounded-lg py-2.5"
                >
                  Replace with AI versions
                </button>
                <button
                  onClick={() => sendConflictDecision("skip")}
                  className="flex-1 bg-white/80 border border-slate-300 text-slate-700 text-xs font-bold rounded-lg py-2.5"
                >
                  Keep existing files
                </button>
              </div>
            </motion.div>
          )}

          {jobStatus && <StatusBadge status={jobStatus} />}
        </div>

        {/* Right panel */}
        <div className="lg:col-span-2 space-y-4">
          {(logs.length > 0 || isBusy) && (
            <ProgressLog logs={logs} isRunning={isBusy} />
          )}
          <DownloadPanel moduleInfo={moduleInfo} api={API} apiKey={API_KEY} />
          <QuestionBank
            api={API}
            apiKey={API_KEY}
            selectedModules={selectedModules}
            globalBusy={isBusy}
            appendLog={(line) => setLogs((prev) => [...prev, line])}
          />
        </div>
      </main>

      <footer className="text-center text-[11px] text-slate-400 pb-6">
        CurriculAI · Built for SRM faculty · Gemini-powered generation
      </footer>
    </div>
  );
}
