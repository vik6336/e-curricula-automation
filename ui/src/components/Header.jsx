export default function Header() {
  return (
    <header className="bg-navy shadow-md">
      <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="bg-maroon text-white font-bold text-xl px-3 py-1 rounded">SRM</div>
          <div>
            <h1 className="text-white text-xl font-bold leading-tight">E-Curricula Generator</h1>
            <p className="text-blue-200 text-xs">SRM Institute of Science and Technology</p>
          </div>
        </div>
        <div className="hidden sm:flex flex-col items-end">
          <span className="text-white text-sm font-medium">21CSE597T</span>
          <span className="text-blue-300 text-xs">Containers & Cloud DevOps</span>
        </div>
      </div>
      <div className="h-1 bg-maroon" />
    </header>
  );
}
