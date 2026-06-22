import { useState, useEffect } from "react";
import Header from "./components/Header";
import UploadZone from "./components/UploadZone";
import ModuleSelector from "./components/ModuleSelector";
import GenerateButton from "./components/GenerateButton";
import ProgressLog from "./components/ProgressLog";
import DownloadPanel from "./components/DownloadPanel";
import StatusBadge from "./components/StatusBadge";

const API = "";

export default function App() {
  const [sloFile, setSloFile] = useState(null);
  const [selectedModules, setSelectedModules] = useState([1, 2, 3, 4, 5]);
  const [jobStatus, setJobStatus] = useState(null); // null | "uploading" | "running" | "done" | "error"
  const [logs, setLogs] = useState([]);
  const [moduleInfo, setModuleInfo] = useState([]);

  useEffect(() => {
    fetchModuleInfo();
  }, []);

  async function fetchModuleInfo() {
    try {
      const res = await fetch(`${API}/api/modules`);
      if (res.ok) setModuleInfo(await res.json());
    } catch (_) {}
  }

  async function handleGenerate() {
    if (!sloFile || selectedModules.length === 0) return;

    setLogs([]);
    setJobStatus("uploading");

    // Upload SLO file
    const form = new FormData();
    form.append("file", sloFile);
    const uploadRes = await fetch(`${API}/api/upload/slo`, { method: "POST", body: form });
    if (!uploadRes.ok) {
      setJobStatus("error");
      setLogs(["ERROR: Failed to upload SLO document."]);
      return;
    }

    // Start generation
    const genForm = new FormData();
    genForm.append("modules", selectedModules.join(","));
    const genRes = await fetch(`${API}/api/generate`, { method: "POST", body: genForm });
    if (!genRes.ok) {
      setJobStatus("error");
      setLogs(["ERROR: Failed to start generation."]);
      return;
    }
    const { job_id } = await genRes.json();
    setJobStatus("running");

    // Stream status via SSE
    const es = new EventSource(`${API}/api/status/${job_id}`);
    es.onmessage = (e) => {
      const data = JSON.parse(e.data);
      if (data.type === "log") {
        setLogs((prev) => [...prev, data.line]);
      } else if (data.type === "status") {
        setJobStatus(data.status);
        es.close();
        fetchModuleInfo();
      }
    };
    es.onerror = () => {
      setJobStatus("error");
      es.close();
    };
  }

  const isGenerating = jobStatus === "running" || jobStatus === "uploading";

  return (
    <div className="min-h-screen bg-slate-100">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-8 grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left panel */}
        <div className="lg:col-span-1 space-y-4">
          <div className="bg-white rounded-2xl shadow-sm p-6 border border-slate-200">
            <h2 className="text-base font-semibold text-navy mb-4 flex items-center gap-2">
              <span className="bg-navy text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">1</span>
              Upload SLO Document
            </h2>
            <UploadZone file={sloFile} onFileChange={setSloFile} disabled={isGenerating} />
          </div>

          <div className="bg-white rounded-2xl shadow-sm p-6 border border-slate-200">
            <h2 className="text-base font-semibold text-navy mb-4 flex items-center gap-2">
              <span className="bg-navy text-white text-xs rounded-full w-6 h-6 flex items-center justify-center">2</span>
              Select Modules
            </h2>
            <ModuleSelector
              selected={selectedModules}
              onChange={setSelectedModules}
              moduleInfo={moduleInfo}
              disabled={isGenerating}
            />
          </div>

          <GenerateButton
            onClick={handleGenerate}
            disabled={!sloFile || selectedModules.length === 0 || isGenerating}
            isGenerating={isGenerating}
          />

          {jobStatus && <StatusBadge status={jobStatus} />}
        </div>

        {/* Right panel */}
        <div className="lg:col-span-2 space-y-4">
          {(logs.length > 0 || isGenerating) && (
            <ProgressLog logs={logs} isRunning={isGenerating} />
          )}
          <DownloadPanel moduleInfo={moduleInfo} api={API} />
        </div>
      </main>
    </div>
  );
}
