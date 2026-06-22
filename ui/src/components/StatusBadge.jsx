const CONFIG = {
  uploading: { label: "Uploading document...", color: "bg-blue-100 text-blue-700", dot: "bg-blue-500 animate-pulse" },
  running:   { label: "Generating content...", color: "bg-yellow-100 text-yellow-800", dot: "bg-yellow-500 animate-pulse" },
  done:      { label: "Generation complete!", color: "bg-green-100 text-green-700", dot: "bg-green-500" },
  error:     { label: "Generation failed", color: "bg-red-100 text-red-700", dot: "bg-red-500" },
};

export default function StatusBadge({ status }) {
  const cfg = CONFIG[status];
  if (!cfg) return null;
  return (
    <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium ${cfg.color}`}>
      <span className={`w-2 h-2 rounded-full ${cfg.dot}`} />
      {cfg.label}
    </div>
  );
}
