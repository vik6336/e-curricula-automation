import { motion } from "framer-motion";

const MODULE_TITLES = {
  1: "Containers & Docker",
  2: "Docker Advanced",
  3: "CI/CD & DevOps",
  4: "Cloud Platforms",
  5: "Kubernetes & Multi-Cloud",
};

export default function ModuleSelector({ selected, onChange, moduleInfo, disabled }) {
  function toggle(num) {
    if (disabled) return;
    onChange(
      selected.includes(num) ? selected.filter((m) => m !== num) : [...selected, num]
    );
  }

  function getInfo(num) {
    return moduleInfo.find((m) => m.module === num);
  }

  return (
    <div className="space-y-2">
      {[1, 2, 3, 4, 5].map((num, i) => {
        const info = getInfo(num);
        const isSelected = selected.includes(num);
        const isDone = info?.ppt_count > 0;

        return (
          <motion.button
            key={num}
            initial={{ opacity: 0, x: -12 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: i * 0.05 }}
            whileHover={disabled ? {} : { x: 3 }}
            whileTap={disabled ? {} : { scale: 0.98 }}
            onClick={() => toggle(num)}
            disabled={disabled}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl border-2 text-left transition-colors
              ${disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer"}
              ${isSelected
                ? "border-navy bg-blue-50/70 shadow-glass"
                : "border-slate-200/80 bg-white/50 hover:border-slate-300"}`}
          >
            <motion.div
              animate={isSelected ? { scale: [1, 1.25, 1] } : {}}
              transition={{ duration: 0.25 }}
              className={`w-5 h-5 rounded-md flex items-center justify-center flex-shrink-0
                ${isSelected ? "bg-gradient-to-br from-navy to-navy-light" : "border-2 border-slate-300 bg-white"}`}
            >
              {isSelected && <span className="text-white text-xs font-bold">✓</span>}
            </motion.div>
            <div className="flex-1 min-w-0">
              <p className={`text-sm font-semibold ${isSelected ? "text-navy" : "text-slate-700"}`}>
                Module {num}
              </p>
              <p className="text-xs text-slate-500 truncate">{MODULE_TITLES[num]}</p>
            </div>
            {isDone && (
              <span className="text-[11px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full flex-shrink-0 font-semibold">
                {info.ppt_count} PPTs
              </span>
            )}
          </motion.button>
        );
      })}

      <div className="flex gap-2 pt-1">
        <button
          onClick={() => !disabled && onChange([1, 2, 3, 4, 5])}
          className="text-xs text-navy font-medium hover:underline disabled:opacity-50"
          disabled={disabled}
        >
          Select all
        </button>
        <span className="text-slate-300">|</span>
        <button
          onClick={() => !disabled && onChange([])}
          className="text-xs text-slate-500 hover:underline disabled:opacity-50"
          disabled={disabled}
        >
          Clear
        </button>
      </div>
    </div>
  );
}
