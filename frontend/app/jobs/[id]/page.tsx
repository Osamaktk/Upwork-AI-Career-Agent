"use client";

import Link from "next/link";
import {useParams} from "next/navigation";
import {useCallback, useEffect, useState} from "react";

import {useSession} from "@/components/session-provider";
import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {apiRequest} from "@/lib/api";
import type {
  ClientAnalysis,
  EvidenceGraph,
  JobDetail,
  PortfolioSelection,
} from "@/lib/types";

export default function JobDetailPage() {
  const {id} = useParams<{id: string}>();
  const {token} = useSession();
  const [job, setJob] = useState<JobDetail | null>(null);
  const [portfolioSelection, setPortfolioSelection] = useState<PortfolioSelection | null>(null);
  const [evidence, setEvidence] = useState<EvidenceGraph | null>(null);
  const [clientAnalysis, setClientAnalysis] = useState<ClientAnalysis | null>(null);
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

  async function runJobAction(label: string, suffix: string) {
    setRunning(label);
    setError("");
    try {
      await apiRequest(`/api/v1/jobs/${id}/${suffix}`, token, {method: "POST"});
      await load();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Action failed");
    } finally {
      setRunning("");
    }
  }

  async function selectPortfolio() {
    setRunning("portfolio");
    setError("");
    try {
      setPortfolioSelection(
        await apiRequest<PortfolioSelection>(`/api/v1/jobs/${id}/portfolio-selection`, token, {
          method: "POST",
        }),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Portfolio selection failed");
    } finally {
      setRunning("");
    }
  }

  async function rebuildEvidence() {
    setRunning("evidence");
    setError("");
    try {
      setEvidence(
        await apiRequest<EvidenceGraph>(`/api/v1/jobs/${id}/evidence/rebuild`, token, {
          method: "POST",
        }),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Evidence graph failed");
    } finally {
      setRunning("");
    }
  }

  async function analyzeClient() {
    if (!job?.client_id) return;
    setRunning("client");
    setError("");
    try {
      setClientAnalysis(
        await apiRequest<ClientAnalysis>(
          `/api/v1/clients/${job.client_id}/analyze?job_id=${id}`,
          token,
          {method: "POST"},
        ),
      );
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Client analysis failed");
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
            <button className="button-secondary" onClick={() => runJobAction("analyze", "analyze")} disabled={Boolean(running)}>
              {running === "analyze" ? "Analyzing…" : "Analyze"}
            </button>
            <button className="button-primary" onClick={() => runJobAction("match", "match")} disabled={Boolean(running)}>
              {running === "match" ? "Matching…" : "Match"}
            </button>
            <button className="button-secondary" onClick={selectPortfolio} disabled={Boolean(running)}>
              {running === "portfolio" ? "Ranking…" : "Select portfolio"}
            </button>
            <button className="button-secondary" onClick={rebuildEvidence} disabled={Boolean(running)}>
              {running === "evidence" ? "Building…" : "Build evidence"}
            </button>
            {job.client_id ? (
              <button className="button-secondary" onClick={analyzeClient} disabled={Boolean(running)}>
                {running === "client" ? "Analyzing client…" : "Analyze client"}
              </button>
            ) : null}
          </section>
        </aside>
      </div>
      {portfolioSelection ? <PortfolioResults selection={portfolioSelection} /> : null}
      {evidence ? <EvidenceResults graph={evidence} /> : null}
      {clientAnalysis ? (
        <section className="panel mt-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <p className="eyebrow">Client analysis</p>
            {job.client_id ? <Link className="text-sm text-emerald-300" href={`/clients/${job.client_id}`}>Open sourced client record</Link> : null}
          </div>
          <MatchList title="Requirements" values={clientAnalysis.requirements} />
          <MatchList title="Unknowns" values={clientAnalysis.unknowns} />
          <MatchList title="Questions" values={clientAnalysis.questions} />
        </section>
      ) : null}
    </main>
  );
}

function PortfolioResults({selection}: {selection: PortfolioSelection}) {
  return (
    <section className="panel mt-8">
      <p className="eyebrow">Portfolio relevance · {selection.formula_version}</p>
      <div className="mt-5 grid gap-4 md:grid-cols-2">
        {selection.ranked_projects.map((project) => (
          <article className="rounded-xl border border-white/10 p-4" key={project.project_id}>
            <div className="flex items-start justify-between gap-4">
              <h2 className="section-title">{project.title}</h2>
              <span className="text-xl font-semibold text-emerald-300">{Number(project.relevance_score).toFixed(0)}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-300">{project.explanation}</p>
            <p className="mt-3 text-xs text-slate-500">{project.verified_claim_ids.length} verified claim(s)</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function EvidenceResults({graph}: {graph: EvidenceGraph}) {
  return (
    <section className="panel mt-8">
      <p className="eyebrow">Evidence graph · {graph.proposal_ready_link_count} ready link(s)</p>
      <div className="mt-5 space-y-3">
        {graph.links.map((link) => (
          <article className="rounded-xl border border-emerald-300/15 p-4" key={link.id}>
            <p className="text-sm text-emerald-200">{link.requirement} → {link.skill}</p>
            <p className="mt-2 text-sm text-slate-300">{link.claim}</p>
            <p className="mt-2 text-xs text-slate-500">Portfolio: {link.portfolio_project ?? "No project attached"}</p>
          </article>
        ))}
        <MatchList title="Unsupported requirements" values={graph.unsupported_requirements} />
      </div>
    </section>
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
