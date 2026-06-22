import { useRef } from "react";

export default function UploadZone({ file, onFileChange, disabled }) {
  const inputRef = useRef(null);

  function handleDrop(e) {
    e.preventDefault();
    if (disabled) return;
    const dropped = e.dataTransfer.files[0];
    if (dropped) onFileChange(dropped);
  }

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => e.preventDefault()}
      onClick={() => !disabled && inputRef.current?.click()}
      className={`border-2 border-dashed rounded-xl p-6 text-center transition-colors cursor-pointer
        ${disabled ? "opacity-50 cursor-not-allowed border-slate-200" :
          file ? "border-green-400 bg-green-50" : "border-slate-300 hover:border-navy hover:bg-blue-50"}`}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.doc"
        className="hidden"
        onChange={(e) => onFileChange(e.target.files[0])}
        disabled={disabled}
      />

      {file ? (
        <div className="space-y-2">
          <div className="text-3xl">📄</div>
          <p className="text-sm font-medium text-green-700 truncate">{file.name}</p>
          <p className="text-xs text-slate-500">{(file.size / 1024).toFixed(1)} KB</p>
          {!disabled && (
            <p className="text-xs text-slate-400">Click to replace</p>
          )}
        </div>
      ) : (
        <div className="space-y-2">
          <div className="text-3xl">📂</div>
          <p className="text-sm text-slate-600">Drop your SLO/SRO document here</p>
          <p className="text-xs text-slate-400">PDF, DOCX supported</p>
        </div>
      )}
    </div>
  );
}
