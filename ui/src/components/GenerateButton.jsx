export default function GenerateButton({ onClick, disabled, isGenerating }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full py-4 rounded-2xl font-bold text-base transition-all shadow-sm
        ${disabled
          ? "bg-slate-300 text-slate-500 cursor-not-allowed"
          : "bg-maroon hover:bg-red-800 active:scale-95 text-white cursor-pointer shadow-md"}`}
    >
      {isGenerating ? (
        <span className="flex items-center justify-center gap-3">
          <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          Generating...
        </span>
      ) : (
        "⚡ Generate Content"
      )}
    </button>
  );
}
