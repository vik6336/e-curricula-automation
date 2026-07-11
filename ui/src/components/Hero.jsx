import { motion } from "framer-motion";

const DELIVERABLES = [
  { icon: "📊", label: "18 PPTs / module", sub: "one per SLO" },
  { icon: "📕", label: "Learning PDF", sub: "consolidated notes" },
  { icon: "📝", label: "Assignments", sub: "coming soon" },
  { icon: "🚀", label: "Portal Upload", sub: "one-click publish" },
];

export default function Hero() {
  return (
    <section className="max-w-6xl mx-auto px-4 pt-10 pb-6 text-center">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      >
        <span className="inline-flex items-center gap-2 glass rounded-full px-4 py-1.5 text-xs font-semibold text-navy shadow-glass mb-5">
          <span className="text-maroon">✦</span> AI-powered e-curricula, from syllabus to portal
        </span>
        <h2 className="text-4xl sm:text-5xl font-black tracking-tight leading-tight">
          <span className="text-gradient">Your entire course content,</span>
          <br />
          <span className="text-navy">generated in minutes.</span>
        </h2>
        <p className="mt-4 text-slate-600 text-sm sm:text-base max-w-2xl mx-auto">
          Upload your SLO/SRO document — CurriculAI turns it into presentation decks,
          learning material, and publishes everything to the eCurricula portal.
        </p>
      </motion.div>

      <motion.div
        initial="hidden"
        animate="show"
        variants={{
          hidden: {},
          show: { transition: { staggerChildren: 0.1, delayChildren: 0.35 } },
        }}
        className="mt-8 grid grid-cols-2 sm:grid-cols-4 gap-3 max-w-3xl mx-auto"
      >
        {DELIVERABLES.map((d) => (
          <motion.div
            key={d.label}
            variants={{
              hidden: { opacity: 0, y: 16, scale: 0.95 },
              show: { opacity: 1, y: 0, scale: 1 },
            }}
            whileHover={{ y: -4, scale: 1.03 }}
            className="glass rounded-2xl px-4 py-3 shadow-glass text-left"
          >
            <div className="text-xl">{d.icon}</div>
            <p className="text-[13px] font-bold text-navy mt-1 leading-tight">{d.label}</p>
            <p className="text-[11px] text-slate-500">{d.sub}</p>
          </motion.div>
        ))}
      </motion.div>
    </section>
  );
}
