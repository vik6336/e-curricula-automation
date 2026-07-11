import { motion } from "framer-motion";

// Downloads require the API key — use a fetch+blob approach instead of plain <a href>
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

export default function DownloadPanel({ moduleInfo, api, apiKey, courseCode }) {
  const hasAny = moduleInfo.some((m) => m.ppt_count > 0);

  if (!hasAny) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.15 }}
      className="glass rounded-2xl shadow-glass p-6"
    >
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-bold text-navy flex items-center gap-2">
          <span className="text-lg">📦</span> Generated Output
        </h2>
        <motion.button
          whileHover={{ scale: 1.04 }}
          whileTap={{ scale: 0.96 }}
          onClick={() => downloadWithKey(`${api}/api/download`, apiKey, `${courseCode || "course"}_all_modules.zip`)}
          className="text-sm bg-gradient-to-r from-navy to-navy-light text-white px-4 py-1.5 rounded-xl font-semibold shadow-glass"
        >
          ↓ Download All
        </motion.button>
      </div>

      <div className="space-y-2.5">
        {moduleInfo.map((m, i) => {
          if (m.ppt_count === 0 && !m.has_pdf) return null;
          return (
            <motion.div
              key={m.module}
              initial={{ opacity: 0, x: 16 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 + i * 0.06 }}
              whileHover={{ x: -3, boxShadow: "0 8px 24px rgba(27,54,93,0.10)" }}
              className="flex items-center justify-between py-3 px-4 rounded-xl bg-white/60 border border-white/70"
            >
              <div>
                <p className="text-sm font-semibold text-slate-800">Module {m.module}</p>
                <p className="text-xs text-slate-500">{m.title || `Module ${m.module} content`}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex gap-1.5 text-[11px] font-semibold">
                  {m.ppt_count > 0 && (
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full">
                      {m.ppt_count} PPTs
                    </span>
                  )}
                  {m.has_pdf && (
                    <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                      PDF
                    </span>
                  )}
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  onClick={() =>
                    downloadWithKey(
                      `${api}/api/download/${m.module}`,
                      apiKey,
                      `module_${m.module}.zip`
                    )
                  }
                  className="text-xs bg-gradient-to-r from-maroon to-maroon-light text-white px-3 py-1.5 rounded-lg font-semibold whitespace-nowrap shadow-sm"
                >
                  ↓ ZIP
                </motion.button>
              </div>
            </motion.div>
          );
        })}
      </div>
    </motion.div>
  );
}
