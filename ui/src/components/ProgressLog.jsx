import { useEffect, useRef } from "react";

export default function ProgressLog({ logs, isRunning }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  return (
    <div className="bg-gray-900 rounded-2xl shadow-sm border border-gray-800 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
        <div className="flex items-center gap-2">
          <span className="w-3 h-3 rounded-full bg-red-500" />
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="w-3 h-3 rounded-full bg-green-500" />
          <span className="ml-2 text-gray-400 text-xs font-mono">Pipeline Output</span>
        </div>
        {isRunning && (
          <span className="text-xs text-green-400 flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-pulse" />
            live
          </span>
        )}
      </div>
      <div className="p-4 h-72 overflow-y-auto font-mono text-xs leading-relaxed">
        {logs.map((line, i) => (
          <div key={i} className={`
            ${line.includes("ERROR") || line.includes("Traceback") ? "text-red-400" :
              line.includes("WARNING") ? "text-yellow-400" :
              line.includes("Created") || line.includes("complete") || line.includes("Done") ? "text-green-400" :
              line.includes("Generating") || line.includes("Rate limit") ? "text-blue-300" :
              line.startsWith("===") || line.startsWith("---") ? "text-white font-semibold" :
              "text-gray-300"}
          `}>
            {line || " "}
          </div>
        ))}
        {isRunning && (
          <div className="text-green-400 animate-pulse">▋</div>
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
