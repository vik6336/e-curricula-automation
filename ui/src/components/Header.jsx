import { motion } from "framer-motion";

export default function Header({ course }) {
  return (
    <motion.header
      initial={{ y: -60, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ type: "spring", stiffness: 120, damping: 18 }}
      className="sticky top-0 z-50 glass shadow-glass"
    >
      <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <motion.div
            whileHover={{ rotate: [0, -6, 6, 0], scale: 1.06 }}
            transition={{ duration: 0.5 }}
            className="bg-gradient-to-br from-maroon to-maroon-light text-white font-extrabold text-lg px-3 py-1.5 rounded-xl shadow-glow"
          >
            SRM
          </motion.div>
          <div>
            <h1 className="text-navy text-lg font-extrabold leading-tight tracking-tight">
              Curricul<span className="text-maroon">AI</span>
            </h1>
            <p className="text-slate-500 text-[11px] font-medium">
              SRM Institute of Science and Technology
            </p>
          </div>
        </div>
        <div className="hidden sm:flex items-center gap-3">
          <div className="flex flex-col items-end">
            <span className="text-navy text-sm font-bold">{course?.code || "—"}</span>
            <span className="text-slate-500 text-[11px] max-w-[220px] truncate">
              {course?.name || "No course selected"}
            </span>
          </div>
          <span className="relative flex h-2.5 w-2.5">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-60" />
            <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-green-500" />
          </span>
        </div>
      </div>
      <div className="h-[3px] bg-gradient-to-r from-navy via-maroon to-navy bg-[length:200%_100%] animate-gradient-x" />
    </motion.header>
  );
}
