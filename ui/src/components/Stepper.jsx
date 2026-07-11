import { motion } from "framer-motion";

const STEPS = [
  { id: "upload", icon: "📄", label: "Upload SLO" },
  { id: "generate", icon: "🤖", label: "AI Generation" },
  { id: "review", icon: "📦", label: "Review & Download" },
  { id: "publish", icon: "🚀", label: "Publish to Portal" },
];

// Map jobStatus → index of the step currently active (or completed past)
function activeIndex(jobStatus, hasFile, hasOutput) {
  if (jobStatus === "upload_done") return 4;
  if (jobStatus === "uploading_portal") return 3;
  if (jobStatus === "done" || hasOutput) return 2;
  if (jobStatus === "running" || jobStatus === "uploading") return 1;
  if (hasFile) return 1;
  return 0;
}

export default function Stepper({ jobStatus, hasFile, hasOutput }) {
  const active = activeIndex(jobStatus, hasFile, hasOutput);

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.25 }}
      className="glass rounded-2xl shadow-glass px-6 py-4 max-w-3xl mx-auto"
    >
      <div className="flex items-center">
        {STEPS.map((step, i) => {
          const isDone = i < active;
          const isActive = i === active;
          return (
            <div key={step.id} className="flex items-center flex-1 last:flex-none">
              <div className="flex flex-col items-center gap-1 min-w-[72px]">
                <motion.div
                  animate={
                    isActive
                      ? { scale: [1, 1.12, 1], boxShadow: [
                          "0 0 0 0 rgba(200,16,46,0.3)",
                          "0 0 0 8px rgba(200,16,46,0)",
                          "0 0 0 0 rgba(200,16,46,0)",
                        ] }
                      : {}
                  }
                  transition={{ repeat: isActive ? Infinity : 0, duration: 1.8 }}
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-base font-bold
                    ${isDone ? "bg-gradient-to-br from-green-400 to-green-600 text-white" :
                      isActive ? "bg-gradient-to-br from-maroon to-maroon-light text-white" :
                      "bg-slate-100 text-slate-400 border border-slate-200"}`}
                >
                  {isDone ? "✓" : step.icon}
                </motion.div>
                <span className={`text-[10px] font-semibold text-center leading-tight
                  ${isDone ? "text-green-600" : isActive ? "text-maroon" : "text-slate-400"}`}>
                  {step.label}
                </span>
              </div>
              {i < STEPS.length - 1 && (
                <div className="flex-1 h-1 mx-2 rounded-full bg-slate-200 overflow-hidden mb-4">
                  <motion.div
                    initial={{ width: "0%" }}
                    animate={{ width: isDone ? "100%" : "0%" }}
                    transition={{ duration: 0.6, ease: "easeOut" }}
                    className="h-full bg-gradient-to-r from-green-400 to-green-500"
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </motion.div>
  );
}
