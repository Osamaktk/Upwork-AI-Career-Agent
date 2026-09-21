"use client";

import {useCallback, useEffect, useState} from "react";

import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {PortfolioProject} from "@/lib/types";

export default function PortfolioPage() {
  const {token} = useSession();
  const [projects, setProjects] = useState<PortfolioProject[] | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setProjects(await apiRequest<PortfolioProject[]>("/api/v1/portfolio", token));
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load portfolio");
    }
  }, [token]);

  useEffect(() => { void load(); }, [load]);

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Portfolio</p>
          <h1 className="page-title">Evidence-backed projects</h1>
        </div>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {!projects ? (
        <LoadingState />
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {projects.map((project) => (
            <article className="panel" key={project.id}>
              <div className="flex items-start justify-between gap-4">
                <h2 className="text-xl font-semibold">{project.title}</h2>
                <StatusBadge value={project.verification_status} />
              </div>
              <p className="mt-3 text-sm leading-6 text-slate-400">{project.description}</p>
              <div className="mt-5 flex flex-wrap gap-2">
                {[...project.technologies, ...project.skills].map((item) => (
                  <span className="chip" key={item}>{item}</span>
                ))}
              </div>
              <p className="mt-5 text-xs text-slate-500">
                {project.verified_claim_ids.length} verified claim reference(s)
              </p>
            </article>
          ))}
          {!projects.length ? <div className="panel text-slate-400">No portfolio projects yet.</div> : null}
        </div>
      )}
    </main>
  );
}
