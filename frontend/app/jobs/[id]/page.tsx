"use client";

import {useParams} from "next/navigation";
import {useCallback, useEffect, useState} from "react";

import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {JobDetail} from "@/lib/types";

export default function JobDetailPage() {
  const {id} = useParams<{id: string}>();
  const {token} = useSession();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState("");

  const load = useCallback(async () => {
    if (!token || !id) return;
    try {
      setJob(await apiRequest<JobDetail>(`/api/v1/jobs/${id}`, token));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load job");
    }
  }, [id, token]);

  useEffect(() => {
    void load();
  }, [load]);

  async function run(label: string, suffix: string) {
    setRunning(label);
    try {
      await apiRequest(`/api/v1/jobs/${id}/${suffix}`, token, {method: "POST"});
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed");
    } finally {
      setRunning("");
    }
  }

  if (error && !job) return <main className="page"><ErrorState message={error} /></main>;
  if (!job) return <main className="page"><LoadingState /></main>;

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Job detail</p>
          <h1 className="page-title">{job.title}</h1>
        </div>
        <div className="flex gap-2">
          <StatusBadge value={job.analysis_state} />
          <StatusBadge value={job.compatibility_status} />
        </div>
      </div>
      {error ? <ErrorState message={error} /> : null}
      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <section className="panel space-y-6">
          <p className="leading-7 text-slate-300">{job.description}</p>
          <div>
            <h2 className="section-title">Required skills</h2>
            <div className="mt-3 flex flex-wrap gap-2">
              {job.required_skills.map((item) => <span className="chip" key={item}>{item}</span>)}
            </div>
          </div>
          {job.analysis ? (
            <div>
              <h2 className="section-title">Extracted deliverables</h2>
              <ul className="mt-3 list-disc space-y-2 pl-5 text-sm text-slate-300">
                {job.analysis.deliverables.map((item) => <li key={item}>{item}</li>)}
              </ul>
            </div>
          ) : null}
        </section>
        <aside className="space-y-6">
          <section className="panel">
            <h2 className="section-title">Compatibility</h2>
            {job.match ? (
              <>
                <div className="mt-4 text-5xl font-semibold text-emerald-300">
                  {Number(job.match.compatibility_score).toFixed(0)}
                </div>
                <p className="mt-4 text-sm leading-6 text-slate-300">{job.match.explanation}</p>
                <MatchList title="Exact" values={job.match.exact_matches} />
                <MatchList title="Missing" values={job.match.missing_skills} />
              </>
            ) : (
              <p className="mt-3 text-sm text-slate-400">No persisted match yet.</p>
            )}
          </section>
          <section className="panel flex flex-wrap gap-3">
            <button className="button-secondary" onClick={() => run("analyze", "analyze")} disabled={Boolean(running)}>
              {running === "analyze" ? "Analyzing…" : "Analyze"}
            </button>
            <button className="button-primary" onClick={() => run("match", "match")} disabled={Boolean(running)}>
              {running === "match" ? "Matching…" : "Match"}
            </button>
          </section>
        </aside>
      </div>
    </main>
  );
}

function MatchList({title, values}: {title: string; values: string[]}) {
  if (!values.length) return null;
  return (
    <div className="mt-5">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>
      <div className="mt-2 flex flex-wrap gap-2">
        {values.map((item) => <span className="chip" key={item}>{item}</span>)}
      </div>
    </div>
  );
}
