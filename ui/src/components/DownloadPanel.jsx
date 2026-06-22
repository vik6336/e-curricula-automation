const MODULE_TITLES = {
  1: "Containers & Docker",
  2: "Docker Advanced",
  3: "CI/CD & DevOps",
  4: "Cloud Platforms",
  5: "Kubernetes & Multi-Cloud",
};

export default function DownloadPanel({ moduleInfo, api }) {
  const hasAny = moduleInfo.some((m) => m.ppt_count > 0);

  if (!hasAny) return null;

  return (
    <div className="bg-white rounded-2xl shadow-sm p-6 border border-slate-200">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-navy">Generated Output</h2>
        <a
          href={`${api}/api/download`}
          className="text-sm bg-navy text-white px-4 py-1.5 rounded-lg hover:bg-blue-900 transition-colors font-medium"
        >
          ↓ Download All
        </a>
      </div>

      <div className="space-y-3">
        {moduleInfo.map((m) => {
          if (m.ppt_count === 0 && !m.has_pdf) return null;
          return (
            <div
              key={m.module}
              className="flex items-center justify-between py-3 px-4 rounded-xl bg-slate-50 border border-slate-100"
            >
              <div>
                <p className="text-sm font-medium text-slate-800">Module {m.module}</p>
                <p className="text-xs text-slate-500">{MODULE_TITLES[m.module]}</p>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex gap-2 text-xs">
                  {m.ppt_count > 0 && (
                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded-full font-medium">
                      {m.ppt_count} PPTs
                    </span>
                  )}
                  {m.has_pdf && (
                    <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full font-medium">
                      PDF
                    </span>
                  )}
                </div>
                <a
                  href={`${api}/api/download/${m.module}`}
                  className="text-xs bg-maroon text-white px-3 py-1.5 rounded-lg hover:bg-red-800 transition-colors font-medium whitespace-nowrap"
                >
                  ↓ Module {m.module}
                </a>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
