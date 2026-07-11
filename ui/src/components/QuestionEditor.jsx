import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const VERBS = [
  "Choose", "Count", "Cite", "Define", "Describe", "Distinguish", "Draw",
  "Find", "Group", "Identify", "Know", "Label", "List", "Listen", "Locate",
  "Match", "Memorize", "Name", "Outline", "Quote", "Read", "Repeat",
  "Recall", "Recite", "Relate", "Review", "Recognize", "Record",
  "Reproduce", "Select", "State", "Sequence", "Show", "Sort", "Tell",
  "Underline", "Write",
];
const BLOOMS = { 1: "Remember", 2: "Understand", 3: "Apply", 4: "Analyze", 5: "Evaluate", 6: "Create" };
const MINS = { mcqs: 5, short_questions: 2, long_questions: 1 };
const KIND_LABEL = { mcqs: "MCQ", short_questions: "Short", long_questions: "Long" };

function blankQuestion(kind) {
  if (kind === "mcqs")
    return { question: "", options: ["", "", "", ""], correct_option: 1,
             blooms_level: 2, taxonomy_verb: "Identify", program_outcomes: [1] };
  return { question: "", answer: "", level: 2, taxonomy_verb: "Describe",
           program_outcomes: [1] };
}

/** Metadata row: Bloom's / Level select, taxonomy verb, PO checkboxes. */
function MetaControls({ q, kind, onPatch }) {
  const levelKey = kind === "mcqs" ? "blooms_level" : "level";
  return (
    <div className="flex flex-wrap items-center gap-3 mt-2">
      <label className="text-[10px] font-semibold text-slate-500 flex items-center gap-1">
        Bloom's
        <select
          value={q[levelKey]}
          onChange={(e) => onPatch({ [levelKey]: Number(e.target.value) })}
          className="text-xs border border-slate-300 rounded-md px-1.5 py-1 bg-white"
        >
          {Object.entries(BLOOMS).map(([n, name]) => (
            <option key={n} value={n}>{n} — {name}</option>
          ))}
        </select>
      </label>
      <label className="text-[10px] font-semibold text-slate-500 flex items-center gap-1">
        Verb
        <select
          value={q.taxonomy_verb}
          onChange={(e) => onPatch({ taxonomy_verb: e.target.value })}
          className="text-xs border border-slate-300 rounded-md px-1.5 py-1 bg-white"
        >
          {VERBS.map((v) => <option key={v} value={v}>{v}</option>)}
        </select>
      </label>
      <div className="text-[10px] font-semibold text-slate-500 flex items-center gap-2">
        POs
        {[1, 2, 3].map((p) => (
          <label key={p} className="flex items-center gap-0.5 cursor-pointer">
            <input
              type="checkbox"
              checked={q.program_outcomes.includes(p)}
              onChange={(e) => {
                const pos = e.target.checked
                  ? [...q.program_outcomes, p].sort()
                  : q.program_outcomes.filter((x) => x !== p);
                onPatch({ program_outcomes: pos.length ? pos : [1] });
              }}
              className="w-3 h-3 accent-navy"
            />
            PO{String(p).padStart(2, "0")}
          </label>
        ))}
      </div>
    </div>
  );
}

/** AI regenerate row: feedback input + button. */
function RegenRow({ busy, onRegen }) {
  const [feedback, setFeedback] = useState("");
  return (
    <div className="flex gap-2 mt-2">
      <input
        value={feedback}
        onChange={(e) => setFeedback(e.target.value)}
        placeholder="Optional feedback for AI (e.g. 'make it harder', 'focus on Kubernetes')"
        className="flex-1 text-[11px] border border-purple-200 bg-purple-50/50 rounded-lg px-2 py-1.5 placeholder:text-slate-400"
        disabled={busy}
      />
      <button
        onClick={() => onRegen(feedback)}
        disabled={busy}
        className="text-[11px] font-bold bg-gradient-to-r from-purple-600 to-purple-500 text-white px-3 py-1.5 rounded-lg disabled:opacity-50 whitespace-nowrap"
      >
        {busy ? "Regenerating…" : "↻ AI Regenerate"}
      </button>
    </div>
  );
}

export default function QuestionEditor({ api, apiKey, module, onClose, onSaved, fullPage = false }) {
  const [bank, setBank] = useState(null);
  const [openSession, setOpenSession] = useState(0);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);
  const [regenBusy, setRegenBusy] = useState(null); // "sIdx:kind:qIdx"
  const [error, setError] = useState("");

  function apiFetch(path, opts = {}) {
    return fetch(`${api}${path}`, {
      ...opts,
      headers: { "X-API-Key": apiKey, ...(opts.headers || {}) },
    });
  }

  useEffect(() => {
    (async () => {
      const res = await apiFetch(`/api/questions/bank/${module}`);
      if (res.ok) setBank(await res.json());
      else setError("Could not load question bank.");
    })();
  }, [module]);

  function patchQuestion(sIdx, kind, qIdx, patch) {
    setBank((prev) => {
      const next = structuredClone(prev);
      Object.assign(next.sessions[sIdx][kind][qIdx], patch);
      return next;
    });
    setDirty(true);
  }

  function deleteQuestion(sIdx, kind, qIdx) {
    setBank((prev) => {
      const next = structuredClone(prev);
      next.sessions[sIdx][kind].splice(qIdx, 1);
      return next;
    });
    setDirty(true);
  }

  function addQuestion(sIdx, kind) {
    setBank((prev) => {
      const next = structuredClone(prev);
      next.sessions[sIdx][kind].push(blankQuestion(kind));
      return next;
    });
    setDirty(true);
  }

  async function regen(sIdx, kind, qIdx, feedback) {
    const key = `${sIdx}:${kind}:${qIdx}`;
    setRegenBusy(key);
    setError("");
    try {
      const res = await apiFetch("/api/questions/regenerate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          module,
          session: bank.sessions[sIdx].session,
          kind,
          index: qIdx,
          feedback,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "failed");
      const { question } = await res.json();
      setBank((prev) => {
        const next = structuredClone(prev);
        next.sessions[sIdx][kind][qIdx] = question;
        return next;
      });
      // regen saves server-side already; local unsaved edits stay dirty
    } catch (e) {
      setError(`AI regeneration failed: ${e.message}`);
    } finally {
      setRegenBusy(null);
    }
  }

  async function save() {
    setSaving(true);
    setError("");
    try {
      const res = await apiFetch(`/api/questions/bank/${module}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessions: bank.sessions }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || "save failed");
      setDirty(false);
      onSaved?.();
    } catch (e) {
      setError(String(e.message));
    } finally {
      setSaving(false);
    }
  }

  const inputCls = fullPage
    ? "w-full text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-navy"
    : "w-full text-xs border border-slate-300 rounded-lg px-2 py-1.5 bg-white focus:outline-none focus:border-navy";

  const panel = (
      <motion.div
        initial={{ y: 30, scale: 0.98 }}
        animate={{ y: 0, scale: 1 }}
        className={`glass-deep rounded-2xl shadow-glass-lg w-full bg-white/90 ${
          fullPage ? "" : "max-w-4xl"
        }`}
      >
        {/* header */}
        <div className="sticky top-0 z-10 bg-white/95 backdrop-blur rounded-t-2xl border-b border-slate-200 px-6 py-4 flex items-center justify-between">
          <div>
            <h2 className="text-base font-extrabold text-navy">
              ✏️ Edit Question Bank — Module {module}
            </h2>
            <p className="text-[11px] text-slate-500">
              {bank?.module_title} · changes go to the portal exactly as edited
            </p>
          </div>
          <div className="flex items-center gap-2">
            {dirty && (
              <span className="text-[10px] font-bold text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-2 py-0.5">
                unsaved changes
              </span>
            )}
            <button
              onClick={save}
              disabled={!dirty || saving}
              className="text-xs font-bold bg-gradient-to-r from-maroon to-maroon-light text-white px-4 py-2 rounded-lg disabled:opacity-40"
            >
              {saving ? "Saving…" : "💾 Save"}
            </button>
            <button
              onClick={onClose}
              className="text-xs font-bold border border-slate-300 text-slate-600 px-3 py-2 rounded-lg bg-white"
            >
              {fullPage ? "Close Tab" : "Close"}
            </button>
          </div>
        </div>

        {error && (
          <div className="mx-6 mt-3 text-[11px] text-red-700 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
            {error}
          </div>
        )}

        {/* body */}
        <div className="p-6 space-y-3">
          {!bank && !error && <p className="text-sm text-slate-500">Loading…</p>}
          {bank?.sessions.map((sess, sIdx) => (
            <div key={sess.session} className="border border-slate-200 rounded-xl overflow-hidden bg-white/70">
              <button
                onClick={() => setOpenSession(openSession === sIdx ? -1 : sIdx)}
                className="w-full flex items-center justify-between px-4 py-3 text-left"
              >
                <span className="text-sm font-bold text-navy">Session {sess.session}</span>
                <span className="text-[10px] text-slate-500">
                  {sess.mcqs.length} MCQ · {sess.short_questions.length} short ·{" "}
                  {sess.long_questions.length} long {openSession === sIdx ? "▲" : "▼"}
                </span>
              </button>

              <AnimatePresence>
                {openSession === sIdx && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: "auto", opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    className="overflow-hidden"
                  >
                    <div className="px-4 pb-4 space-y-4">
                      {["mcqs", "short_questions", "long_questions"].map((kind) => (
                        <div key={kind}>
                          <div className="flex items-center justify-between mt-2 mb-1.5">
                            <h4 className="text-[11px] font-extrabold uppercase tracking-wide text-maroon">
                              {KIND_LABEL[kind]} questions
                              <span className="text-slate-400 font-medium normal-case"> · min {MINS[kind]}</span>
                            </h4>
                            <button
                              onClick={() => addQuestion(sIdx, kind)}
                              className="text-[10px] font-bold text-navy hover:underline"
                            >
                              + Add
                            </button>
                          </div>

                          {sess[kind].map((q, qIdx) => {
                            const busyKey = `${sIdx}:${kind}:${qIdx}`;
                            return (
                              <div key={qIdx} className="border border-slate-200 rounded-xl p-3 mb-2 bg-white">
                                <div className="flex items-start gap-2">
                                  <span className="text-[10px] font-bold text-slate-400 mt-2">
                                    {qIdx + 1}.
                                  </span>
                                  <div className="flex-1 space-y-1.5">
                                    <textarea
                                      value={q.question}
                                      onChange={(e) => patchQuestion(sIdx, kind, qIdx, { question: e.target.value })}
                                      rows={2}
                                      placeholder="Question text"
                                      className={inputCls}
                                    />
                                    {kind === "mcqs" ? (
                                      q.options.map((opt, oIdx) => (
                                        <div key={oIdx} className="flex items-center gap-2">
                                          <input
                                            type="radio"
                                            name={`correct-${busyKey}`}
                                            checked={q.correct_option === oIdx + 1}
                                            onChange={() => patchQuestion(sIdx, kind, qIdx, { correct_option: oIdx + 1 })}
                                            className="accent-green-600"
                                            title="Mark as correct answer"
                                          />
                                          <input
                                            value={opt}
                                            onChange={(e) => {
                                              const options = [...q.options];
                                              options[oIdx] = e.target.value;
                                              patchQuestion(sIdx, kind, qIdx, { options });
                                            }}
                                            placeholder={`Option ${oIdx + 1}`}
                                            className={`${inputCls} ${q.correct_option === oIdx + 1 ? "border-green-400 bg-green-50/50" : ""}`}
                                          />
                                        </div>
                                      ))
                                    ) : (
                                      <textarea
                                        value={q.answer}
                                        onChange={(e) => patchQuestion(sIdx, kind, qIdx, { answer: e.target.value })}
                                        rows={kind === "long_questions" ? 4 : 2}
                                        placeholder="Model answer"
                                        className={inputCls}
                                      />
                                    )}
                                    <MetaControls
                                      q={q}
                                      kind={kind}
                                      onPatch={(patch) => patchQuestion(sIdx, kind, qIdx, patch)}
                                    />
                                    <RegenRow
                                      busy={regenBusy === busyKey}
                                      onRegen={(fb) => regen(sIdx, kind, qIdx, fb)}
                                    />
                                  </div>
                                  <button
                                    onClick={() => deleteQuestion(sIdx, kind, qIdx)}
                                    disabled={sess[kind].length <= MINS[kind]}
                                    title={sess[kind].length <= MINS[kind]
                                      ? `Portal requires at least ${MINS[kind]}`
                                      : "Delete question"}
                                    className="text-slate-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed text-sm mt-1.5"
                                  >
                                    🗑
                                  </button>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ))}
        </div>
      </motion.div>
  );

  if (fullPage) return panel;

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] bg-navy/30 backdrop-blur-sm flex items-start justify-center overflow-y-auto py-8 px-4"
      onClick={(e) => e.target === e.currentTarget && !dirty && onClose()}
    >
      {panel}
    </motion.div>
  );
}
