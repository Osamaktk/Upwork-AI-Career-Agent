"use client";

import {useCallback, useEffect, useState} from "react";

import {ErrorState, LoadingState} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {DashboardSummary} from "@/lib/types";

const metricLabels: [keyof DashboardSummary, string][] = [
  ["total_jobs", "Total jobs"],
  ["analyzed_jobs", "Analyzed"],
  ["matched_jobs", "Matched"],
  ["jobs_needing_review", "Needs review"],
  ["profile_completeness", "Profile complete"],
  ["portfolio_count", "Portfolio projects"],
];

export default function DashboardPage() {
  const {token} = useSession();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setSummary(await apiRequest<DashboardSummary>("/api/v1/dashboard/summary", token));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load dashboard");
    }
  }, [token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function runAction(label: string, path: string) {
    setRunning(label);
    setError("");
    try {
      await apiRequest(path, token, {method: "POST"});
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed");
    } finally {
      setRunning("");
    }
  }

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Sample engine</p>
          <h1 className="page-title">Opportunity command center</h1>
          <p className="page-copy">Live data from the local FastAPI service.</p>
        </div>
        <span className="rounded-full border border-amber-300/30 bg-amber-300/10 px-4 py-2 text-sm text-amber-200">
          No Upwork connection
        </span>
      </div>

      {error ? <ErrorState message={error} /> : null}
      {!summary ? (
        <LoadingState />
      ) : (
        <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {metricLabels.map(([key, label]) => (
            <article className="metric" key={key}>
              <div className="text-3xl font-semibold text-emerald-300">
                {summary[key]}
                {key === "profile_completeness" ? "%" : ""}
              </div>
              <p className="mt-2 text-sm text-slate-400">{label}</p>
            </article>
          ))}
        </section>
      )}

      <section className="panel mt-8">
        <p className="eyebrow">Development actions</p>
        <h2 className="mt-2 text-2xl font-semibold">Run the local sample workflow</h2>
        <div className="mt-6 flex flex-wrap gap-3">
          <button
            className="button-secondary"
            onClick={() => runAction("seed", "/api/v1/development/seed")}
            disabled={Boolean(running)}
          >
            {running === "seed" ? "Seeding…" : "Seed synthetic profile"}
          </button>
          <button
            className="button-secondary"
            onClick={() => runAction("import", "/api/v1/jobs/import/sample")}
            disabled={Boolean(running)}
          >
            {running === "import" ? "Importing…" : "Import sample jobs"}
          </button>
          <button
            className="button-primary"
            onClick={() => runAction("analyze", "/api/v1/jobs/analyze/batch")}
            disabled={Boolean(running)}
          >
            {running === "analyze" ? "Analyzing…" : "Analyze and rank"}
          </button>
        </div>
      </section>
    </main>
  );
}
