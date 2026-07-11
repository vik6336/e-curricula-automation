import { motion, AnimatePresence } from "framer-motion";

const CONFIG = {
  uploading:       { label: "Uploading document…",         color: "bg-blue-100/80 text-blue-700",     dot: "bg-blue-500 animate-pulse" },
  running:         { label: "Generating content…",         color: "bg-yellow-100/80 text-yellow-800", dot: "bg-yellow-500 animate-pulse" },
  done:            { label: "Generation complete!",        color: "bg-green-100/80 text-green-700",   dot: "bg-green-500" },
  uploading_portal:{ label: "Uploading to eCurricula…",    color: "bg-purple-100/80 text-purple-700", dot: "bg-purple-500 animate-pulse" },
  awaiting_decision:{ label: "Action needed: existing files found", color: "bg-amber-100/80 text-amber-800", dot: "bg-amber-500 animate-pulse" },
  upload_done:     { label: "Published to eCurricula!",    color: "bg-green-100/80 text-green-700",   dot: "bg-green-500" },
  upload_error:    { label: "Portal upload failed",        color: "bg-red-100/80 text-red-700",       dot: "bg-red-500" },
  error:           { label: "Generation failed",           color: "bg-red-100/80 text-red-700",       dot: "bg-red-500" },
};

export default function StatusBadge({ status }) {
  const cfg = CONFIG[status];
  if (!cfg) return null;
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        initial={{ opacity: 0, y: 8, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: -8, scale: 0.95 }}
        className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold backdrop-blur ${cfg.color}`}
      >
        <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
        {cfg.label}
      </motion.div>
    </AnimatePresence>
  );
}
