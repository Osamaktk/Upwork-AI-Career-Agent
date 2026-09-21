const stages = [
  "Sample jobs",
  "Analyze",
  "Match",
  "Client context",
  "Portfolio",
  "Proposal",
  "Fact check",
  "Review",
];

export default function Home() {
  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 py-16">
      <div className="mb-12 flex items-center justify-between gap-6">
        <div>
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-emerald-400">
            Development workspace
          </p>
          <h1 className="max-w-3xl text-4xl font-semibold tracking-tight md:text-6xl">
            Your evidence-backed freelancing operating system.
          </h1>
        </div>
        <span className="rounded-full border border-amber-300/40 bg-amber-300/10 px-4 py-2 text-sm text-amber-200">
          Sample mode
        </span>
      </div>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          ["3", "Sample jobs ready"],
          ["0", "External connections"],
          ["Required", "Human approval"],
        ].map(([value, label]) => (
          <article key={label} className="rounded-2xl border border-emerald-100/10 bg-white/5 p-6">
            <div className="text-3xl font-semibold text-emerald-300">{value}</div>
            <div className="mt-2 text-sm text-slate-400">{label}</div>
          </article>
        ))}
      </section>

      <section className="mt-8 rounded-2xl border border-emerald-100/10 bg-[#0d1b17] p-6 md:p-8">
        <div className="mb-6 flex items-end justify-between gap-4">
          <div>
            <p className="text-sm text-slate-400">Engine path</p>
            <h2 className="mt-1 text-2xl font-semibold">Build and verify locally first</h2>
          </div>
          <span className="text-sm text-emerald-300">Phase 1 foundation</span>
        </div>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {stages.map((stage, index) => (
            <div key={stage} className="rounded-xl border border-emerald-100/10 bg-black/15 p-4">
              <span className="text-xs text-emerald-400">{String(index + 1).padStart(2, "0")}</span>
              <p className="mt-2 font-medium">{stage}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
