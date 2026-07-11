import { useEffect, useState } from "react";
import { motion } from "framer-motion";

/**
 * Course setup. The professor sets the portal course code + name; generated
 * output is namespaced by code on the server, so one app handles any course
 * (one active at a time). Structure stays fixed at 5 modules x 9 sessions.
 */
export default function CourseSetup({ course, onSave, disabled }) {
  const [editing, setEditing] = useState(false);
  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    if (course) {
      setCode(course.code || "");
      setName(course.name || "");
      // Force setup the first time, before any real course is chosen
      if (course.is_default) setEditing(true);
    }
  }, [course]);

  async function submit() {
    setError("");
    setSaving(true);
    const res = await onSave(code.trim(), name.trim());
    setSaving(false);
    if (res.ok) setEditing(false);
    else setError(res.error);
  }

  if (!course) return null;

  if (!editing) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass rounded-2xl shadow-glass px-5 py-3 flex items-center justify-between"
      >
        <div>
          <p className="text-[11px] uppercase tracking-wide text-slate-400 font-semibold">
            Active course
          </p>
          <p className="text-sm font-bold text-navy">
            {course.code}
            <span className="text-slate-500 font-medium"> · {course.name}</span>
          </p>
        </div>
        <button
          onClick={() => setEditing(true)}
          disabled={disabled}
          className="text-xs font-semibold text-navy border border-navy/30 rounded-lg px-3 py-1.5 bg-white disabled:opacity-50"
        >
          Change course
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className="glass rounded-2xl shadow-glass p-5"
    >
      <h2 className="text-sm font-bold text-navy mb-1">Set up your course</h2>
      <p className="text-[11px] text-slate-500 mb-3">
        Enter the eCurricula course code and name. Content is generated for the
        fixed 5 modules of 9 sessions each. Your files stay separate per course.
      </p>
      <div className="flex flex-col sm:flex-row gap-2">
        <input
          value={code}
          onChange={(e) => setCode(e.target.value)}
          placeholder="Course code (e.g. 21CSE597T)"
          className="flex-1 text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-navy"
        />
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Course name"
          className="flex-[2] text-sm border border-slate-300 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-navy"
        />
        <button
          onClick={submit}
          disabled={saving || !code.trim() || !name.trim()}
          className="bg-gradient-to-r from-navy to-navy-light text-white text-sm font-bold rounded-lg px-4 py-2 disabled:opacity-50 whitespace-nowrap"
        >
          {saving ? "Saving…" : "Save course"}
        </button>
      </div>
      {error && <p className="text-[11px] text-red-600 mt-2">{error}</p>}
      {!course.is_default && (
        <button
          onClick={() => setEditing(false)}
          className="text-[11px] text-slate-500 mt-2 hover:underline"
        >
          Cancel
        </button>
      )}
    </motion.div>
  );
}
