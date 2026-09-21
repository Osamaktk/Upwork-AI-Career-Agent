export function StatusBadge({value}: {value: string}) {
  const normalized = value.toLowerCase();
  const color =
    normalized.includes("verified") || normalized.includes("matched") || normalized === "analyzed"
      ? "border-emerald-300/30 bg-emerald-300/10 text-emerald-200"
      : normalized.includes("review") || normalized.includes("pending")
        ? "border-amber-300/30 bg-amber-300/10 text-amber-200"
        : "border-slate-300/20 bg-slate-300/10 text-slate-300";
  return <span className={`rounded-full border px-2.5 py-1 text-xs ${color}`}>{value}</span>;
}

export function LoadingState() {
  return <div className="panel text-sm text-slate-400">Loading API data…</div>;
}

export function ErrorState({message}: {message: string}) {
  return <div className="rounded-2xl border border-rose-300/20 bg-rose-300/10 p-5 text-rose-200">{message}</div>;
}
