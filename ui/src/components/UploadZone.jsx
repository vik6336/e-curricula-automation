import { useRef, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

export default function UploadZone({ file, onFileChange, disabled }) {
  const inputRef = useRef(null);
  const [dragging, setDragging] = useState(false);

  function handleDrop(e) {
    e.preventDefault();
    setDragging(false);
    if (disabled) return;
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFileChange(dropped);
  }

  return (
    <motion.div
      onDrop={handleDrop}
      onDragOver={(e) => {
        e.preventDefault();
        if (!disabled) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onClick={() => !disabled && inputRef.current?.click()}
      animate={dragging ? { scale: 1.02 } : { scale: 1 }}
      whileHover={disabled ? {} : { scale: 1.01 }}
      className={`relative border-2 border-dashed rounded-2xl p-6 text-center transition-colors cursor-pointer overflow-hidden
        ${disabled ? "opacity-50 cursor-not-allowed border-slate-200" :
          dragging ? "border-maroon bg-red-50/50" :
          file ? "border-green-400 bg-green-50/60" : "border-slate-300 hover:border-navy hover:bg-blue-50/50"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.doc"
        className="hidden"
        onChange={(e) => onFileChange(e.target.files[0])}
        disabled={disabled}
      />

      <AnimatePresence mode="wait">
        {file ? (
          <motion.div
            key="file"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.9 }}
            className="space-y-2"
          >
            <motion.div
              initial={{ rotate: -8 }}
              animate={{ rotate: 0 }}
              transition={{ type: "spring", stiffness: 260, damping: 12 }}
              className="text-3xl"
            >
              📄
            </motion.div>
            <p className="text-sm font-semibold text-green-700 truncate">{file.name}</p>
            <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB · ready</p>
            {!disabled && <p className="text-xs text-slate-400">Click to replace</p>}
          </motion.div>
        ) : (
          <motion.div
            key="empty"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="space-y-2"
          >
            <motion.div
              animate={{ y: [0, -6, 0] }}
              transition={{ repeat: Infinity, duration: 2.4, ease: "easeInOut" }}
              className="text-3xl"
            >
              📂
            </motion.div>
            <p className="text-sm font-medium text-slate-600">
              {dragging ? "Drop it!" : "Drop your SLO/SRO document here"}
            </p>
            <p className="text-xs text-slate-400">PDF, DOCX supported</p>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
