import { useEffect, useRef } from "react";
import { motion } from "framer-motion";

function lineColor(line) {
  if (line.includes("ERROR") || line.includes("Traceback")) return "text-red-400";
  if (line.includes("WARNING")) return "text-yellow-400";
  if (line.includes("Created") || line.includes("complete") || line.includes("Done") || line.includes("✅"))
    return "text-green-400";
  if (line.includes("Generating") || line.includes("Rate limit")) return "text-sky-300";
  if (line.startsWith("===") || line.startsWith("---") || line.startsWith("──"))
    return "text-white font-semibold";
  return "text-gray-300";
}

export default function ProgressLog({ logs, isRunning }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gray-900/95 backdrop-blur rounded-2xl shadow-glass-lg border border-gray-700/60 overflow-hidden"
    >
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800/90 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="w-3 h-3 rounded-full bg-green-500" />
          <span className="ml-2 text-gray-400 text-xs font-mono">Pipeline Output</span>
        </div>
        {isRunning && (
          <span className="text-xs text-green-400 flex items-center gap-1.5 font-mono">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            live
          </span>
        )}
      </div>
      <div className="p-4 h-72 overflow-y-auto font-mono text-xs leading-relaxed">
        {logs.map((line, i) => (
          <motion.div
            key={i}
            initial={{ opacity: 0, x: -6 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2 }}
            className={lineColor(line)}
          >
            {line || " "}
          </motion.div>
        ))}
        {isRunning && <div className="text-green-400 animate-pulse">▋</div>}
        <div ref={bottomRef} />
      </div>
    </motion.div>
  );
}
