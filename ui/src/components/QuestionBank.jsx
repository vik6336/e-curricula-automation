import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { streamJobStatus } from "../lib/api";

async function downloadWithKey(url, apiKey, filename) {
  const res = await fetch(url, { headers: { "X-API-Key": apiKey } });
  if (!res.ok) return;
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  URL.revokeObjectURL(a.href);
}

/**
 * AI Question Bank — generate (Gemini) → faculty review PDF → approve →
 * auto-fill the eCurricula MCQ/Short/Long forms.
 */
export default function QuestionBank({ api, apiKey, selectedModules, globalBusy, appendLog }) {
  const [info, setInfo] = useState([]);
  const [phase, setPhase] = useState("idle"); // idle | generating | publishing
  const [reviewed, setReviewed] = useState(false);
  const [statusLine, setStatusLine] = useState("");
  // Existing portal questions found by the pre-fill scan (awaiting decision)
  const [conflicts, setConflicts] = useState(null);
  const [pubJobId, setPubJobId] = useState(null);

  function apiFetch(path, opts = {}) {
    return fetch(`${api}${path}`, {
      ...opts,
      headers: { "X-API-Key": apiKey, ...(opts.headers || {}) },
    });
  }

  async function fetchInfo() {
    try {
      const res = await apiFetch("/api/questions/info");
      if (res.ok) setInfo(await res.json());
    } catch (_) {}
  }

  useEffect(() => {
    fetchInfo();
    // Editing happens in a separate tab — refresh counts when coming back
    const onFocus = () => fetchInfo();
    window.addEventListener("focus", onFocus);
    return () => window.removeEventListener("focus", onFocus);
  }, []);

  async function handleGenerate() {
    if (selectedModules.length === 0) return;
    setPhase("generating");
    setStatusLine("Generating questions with Gemini…");
    appendLog("── Generating AI question bank ──");

    const form = new FormData();
    form.append("modules", selectedModules.join(","));
    const res = await apiFetch("/api/questions/generate", { method: "POST", body: form });
    if (!res.ok) {
      setPhase("idle");
      setStatusLine("Failed to start generation.");
      return;
    }
    const { job_id } = await res.json();

    // Authenticated fetch-stream — key stays in the header, not the URL
    streamJobStatus(
      job_id,
      async (data) => {
        if (data.type === "log") {
          appendLog(data.line);
          setStatusLine(data.line.slice(0, 80));
        } else if (data.type === "status") {
          setPhase("idle");
          setStatusLine(data.status === "done"
            ? "Question bank ready — download & review."
            : "Generation failed.");
          await fetchInfo();
        }
      },
      (end) => {
        if (end === "error") {
          setPhase("idle");
          setStatusLine("Connection lost — check server.");
        }
      }
    );
  }

  async function handlePublish() {
    const ready = info.filter((m) => m.has_questions && selectedModules.includes(m.module))
                      .map((m) => m.module);
    if (ready.length === 0) return;
    setPhase("publishing");
    setStatusLine("Opening eCurricula — log in + captcha in the browser window…");
    appendLog("── Auto-filling eCurricula question forms ──");
    appendLog("Enter your eCurricula login + captcha in the window that opens.");

    const res = await apiFetch("/api/questions/publish", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ modules: ready }),
    });
    if (!res.ok) {
      setPhase("idle");
      setStatusLine("Failed to start question publish.");
      return;
    }
    const { upload_job_id } = await res.json();
    setPubJobId(upload_job_id);

    const interval = setInterval(async () => {
      try {
        const r = await apiFetch(`/api/upload-job/${upload_job_id}`);
        if (!r.ok) return;
        const data = await r.json();
        if (data.last_log) {
          appendLog(data.last_log);
          setStatusLine(data.last_log.slice(0, 80));
        }
        if (data.status === "awaiting_decision") {
          if (data.conflicts) setConflicts(data.conflicts);
          setStatusLine("Existing questions found — choose replace or keep below.");
        } else if (data.status === "running") {
          setConflicts(null);
        } else if (data.status === "done") {
          clearInterval(interval);
          setConflicts(null);
          setPhase("idle");
          setStatusLine("✅ All questions entered into eCurricula!");
          appendLog("✅ Question forms filled successfully!");
        } else if (data.status === "error") {
          clearInterval(interval);
          setConflicts(null);
          setPhase("idle");
          setStatusLine("❌ Some questions failed — check logs.");
        }
      } catch (_) {}
    }, 5000);
  }

  async function sendConflictDecision(decision) {
    if (!pubJobId) return;
    const res = await apiFetch(`/api/upload-decision/${pubJobId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision }),
    });
    if (res.ok) {
      setConflicts(null);
      appendLog(
        decision === "replace"
          ? "→ Deleting existing questions, then entering the AI bank"
          : "→ Keeping existing questions, filling only empty sessions"
      );
    }
  }

  const readyModules = info.filter((m) => m.has_questions);
  const busy = phase !== "idle" || globalBusy;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="glass rounded-2xl shadow-glass p-6"
    >
      <div className="flex items-center justify-between mb-2">
        <h2 className="text-base font-bold text-navy flex items-center gap-2">
          <span className="text-lg">📝</span> AI Question Bank
        </h2>
        <span className="text-[10px] font-bold uppercase tracking-wide bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
          MCQ · Short · Long
        </span>
      </div>
      <p className="text-xs text-slate-500 mb-4 leading-relaxed">
        Generates 5 MCQs + 2 short + 1 long question per session — each with
        Bloom's Level, Taxonomy of Learning verb, and Program Outcome mapping.
        You review the PDF before anything is entered into the portal.
      </p>

      <motion.button
        whileHover={busy ? {} : { scale: 1.02 }}
        whileTap={busy ? {} : { scale: 0.97 }}
        onClick={handleGenerate}
        disabled={busy || selectedModules.length === 0}
        className="w-full bg-gradient-to-r from-purple-600 to-purple-500 text-white rounded-xl py-2.5 text-sm font-bold disabled:opacity-50 shadow-glass mb-3"
      >
        {phase === "generating" ? (
          <span className="flex items-center justify-center gap-2">
            <span className="inline-block w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin" />
            Generating…
          </span>
        ) : (
          `⚡ Generate Question Bank (Module${selectedModules.length > 1 ? "s" : ""} ${selectedModules.join(", ")})`
        )}
      </motion.button>

      {readyModules.length > 0 && (
        <div className="space-y-2 mb-3">
          {readyModules.map((m) => (
            <div
              key={m.module}
              className="flex items-center justify-between py-2 px-3 rounded-xl bg-white/60 border border-white/70"
            >
              <div>
                <p className="text-xs font-semibold text-slate-800">Module {m.module}</p>
                <p className="text-[10px] text-slate-500">
                  {m.total_questions ?? "?"} questions · {m.sessions ?? "?"} sessions
                </p>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={() => window.open(`#/edit/${m.module}`, "_blank")}
                  disabled={busy}
                  title="Opens the full-page editor in a new tab"
                  className="text-[11px] bg-white border border-navy/30 text-navy px-3 py-1.5 rounded-lg font-semibold disabled:opacity-50"
                >
                  ✏️ Edit
                </button>
                {m.has_pdf && (
                  <button
                    onClick={() =>
                      downloadWithKey(
                        `${api}/api/questions/download/${m.module}`,
                        apiKey,
                        `module_${m.module}_question_bank.pdf`
                      )
                    }
                    className="text-[11px] bg-gradient-to-r from-navy to-navy-light text-white px-3 py-1.5 rounded-lg font-semibold"
                  >
                    ⬇ Review PDF
                  </button>
                )}
              </div>
            </div>
          ))}

          <label className="flex items-start gap-2 pt-1 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={reviewed}
              onChange={(e) => setReviewed(e.target.checked)}
              disabled={busy}
              className="mt-0.5 w-4 h-4 accent-maroon"
            />
            <span className="text-xs text-slate-600 leading-snug">
              I have reviewed the question bank PDF{readyModules.length > 1 ? "s" : ""}
            </span>
          </label>

          <motion.button
            whileHover={!reviewed || busy ? {} : { scale: 1.02 }}
            whileTap={!reviewed || busy ? {} : { scale: 0.97 }}
            onClick={handlePublish}
            disabled={!reviewed || busy}
            className="btn-shine w-full bg-gradient-to-r from-maroon to-maroon-light text-white rounded-xl py-2.5 text-sm font-bold disabled:opacity-50 shadow-glass"
          >
            {phase === "publishing" ? "Filling forms…" : "🤖 Auto-fill eCurricula Forms"}
          </motion.button>
        </div>
      )}

      {conflicts && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          className="rounded-xl border-2 border-amber-300 bg-amber-50/80 p-4 mb-3"
        >
          <h3 className="text-xs font-bold text-navy mb-1.5 flex items-center gap-1.5">
            <span>📌</span> These sessions already have questions on the portal
          </h3>
          <div className="text-[11px] text-slate-600 mb-2 space-y-0.5">
            {Object.entries(conflicts).map(([unit, kinds]) => (
              <p key={unit}>
                <span className="font-semibold">Module {unit}:</span>{" "}
                {Object.entries(kinds)
                  .map(([kind, sessions]) => `${kind} (S${sessions.join(", S")})`)
                  .join(" · ")}
              </p>
            ))}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => sendConflictDecision("replace")}
              className="flex-1 bg-gradient-to-r from-maroon to-maroon-light text-white text-[11px] font-bold rounded-lg py-2"
            >
              Replace (delete & re-enter)
            </button>
            <button
              onClick={() => sendConflictDecision("skip")}
              className="flex-1 bg-white border border-slate-300 text-slate-700 text-[11px] font-bold rounded-lg py-2"
            >
              Keep existing
            </button>
          </div>
        </motion.div>
      )}

      {statusLine && (
        <p className="text-[11px] text-slate-500 font-mono truncate">{statusLine}</p>
      )}
    </motion.div>
  );
}
