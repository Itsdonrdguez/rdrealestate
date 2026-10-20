export default function HomePage() {
  return (
    <main className="min-h-screen bg-slate-950 p-8 text-slate-100">
      <div className="mx-auto max-w-6xl rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <p className="text-sm uppercase tracking-[0.2em] text-emerald-400">Property Intelligence</p>
        <h1 className="mt-4 text-4xl font-bold">Maryland opportunity dashboard</h1>
        <p className="mt-3 max-w-2xl text-slate-300">
          This is the first frontend shell for the owner, property, and opportunity intelligence system.
          Search, filters, markers, and profile pages will be added once the data foundation is approved.
        </p>

        <div className="mt-8 grid gap-4 md:grid-cols-3">
          {['County', 'Owner occupied', 'Years owned'].map((label) => (
            <div key={label} className="rounded-xl border border-slate-700 bg-slate-800 p-4">
              <p className="text-sm text-slate-400">{label}</p>
              <div className="mt-3 h-10 rounded-md bg-slate-700/80" />
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
