import { motion } from "framer-motion";

export default function GenerateButton({ onClick, disabled, isGenerating }) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      whileHover={disabled ? {} : { scale: 1.02, y: -2 }}
      whileTap={disabled ? {} : { scale: 0.97 }}
      className={`w-full py-4 rounded-2xl font-bold text-base transition-colors
        ${disabled
          ? "bg-slate-200/80 text-slate-400 cursor-not-allowed"
          : "btn-shine bg-gradient-to-r from-maroon via-maroon-light to-maroon bg-[length:200%_100%] animate-gradient-x text-white cursor-pointer shadow-glow"}`}
    >
      {isGenerating ? (
        <span className="flex items-center justify-center gap-3">
          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Generating with Gemini…
        </span>
      ) : (
        <span className="flex items-center justify-center gap-2">
          <motion.span
            animate={{ scale: [1, 1.2, 1] }}
            transition={{ repeat: Infinity, duration: 1.8 }}
          >
            ⚡
          </motion.span>
          Generate Content
        </span>
      )}
    </motion.button>
  );
}
