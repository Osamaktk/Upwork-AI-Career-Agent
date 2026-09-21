"use client";

import Link from "next/link";
import {useCallback, useEffect, useState} from "react";

import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {JobPage} from "@/lib/types";

export default function JobsPage() {
  const {token} = useSession();
  const [data, setData] = useState<JobPage | null>(null);
  const [error, setError] = useState("");
  const [skill, setSkill] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    const query = skill ? `?skill=${encodeURIComponent(skill)}` : "";
    try {
      setData(await apiRequest<JobPage>(`/api/v1/jobs${query}`, token));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load jobs");
    }
  }, [skill, token]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Jobs</p>
          <h1 className="page-title">Sample opportunity queue</h1>
        </div>
        <input
          className="input max-w-xs"
          placeholder="Filter by skill"
          value={skill}
          onChange={(event) => setSkill(event.target.value)}
        />
      </div>
      {error ? <ErrorState message={error} /> : null}
      {!data ? (
        <LoadingState />
      ) : (
        <div className="space-y-4">
          {data.items.map((job) => (
            <Link key={job.id} href={`/jobs/${job.id}`} className="panel block transition hover:border-emerald-300/30">
              <div className="flex flex-wrap items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-wider text-slate-500">{job.source}</p>
                  <h2 className="mt-1 text-xl font-semibold">{job.title}</h2>
                  <p className="mt-2 text-sm text-slate-400">
                    {job.currency ?? ""} {job.budget_min ?? "Open"}–{job.budget_max ?? "Open"}
                  </p>
                </div>
                <div className="flex gap-2">
                  <StatusBadge value={job.analysis_state} />
                  <StatusBadge value={job.compatibility_status} />
                </div>
              </div>
              <div className="mt-5 flex flex-wrap gap-2">
                {job.required_skills.map((item) => (
                  <span className="chip" key={item}>{item}</span>
                ))}
              </div>
            </Link>
          ))}
          {!data.items.length ? <div className="panel text-slate-400">No jobs match this filter.</div> : null}
        </div>
      )}
    </main>
  );
}
