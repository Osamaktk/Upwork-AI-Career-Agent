"use client";

import {useParams} from "next/navigation";
import {useEffect, useState} from "react";

import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {ClientDetail, ClientFact} from "@/lib/types";

const factStyles = {
  FACT: "border-emerald-300/25 bg-emerald-300/5",
  INFERENCE: "border-amber-300/25 bg-amber-300/5",
  UNKNOWN: "border-slate-300/20 bg-slate-300/5",
};

export default function ClientDetailPage() {
  const {id} = useParams<{id: string}>();
  const {token} = useSession();
  const [client, setClient] = useState<ClientDetail | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token || !id) return;
    apiRequest<ClientDetail>(`/api/v1/clients/${id}`, token)
      .then(setClient)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load client"));
  }, [id, token]);

  if (error && !client) return <main className="page"><ErrorState message={error} /></main>;
  if (!client) return <main className="page"><LoadingState /></main>;

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Client record · {client.source}</p>
          <h1 className="page-title">{client.company ?? client.name ?? "Unnamed client"}</h1>
          <p className="page-copy">Only sourced records marked FACT are presented as verified facts.</p>
        </div>
      </div>
      <section className="grid gap-5 lg:grid-cols-3">
        {(["FACT", "INFERENCE", "UNKNOWN"] as const).map((classification) => (
          <div className="space-y-3" key={classification}>
            <h2 className="section-title">{classification}</h2>
            {client.facts.filter((fact) => fact.classification === classification).map((fact) => (
              <FactCard fact={fact} key={fact.id} />
            ))}
            {!client.facts.some((fact) => fact.classification === classification) ? (
              <div className="panel text-sm text-slate-500">No {classification.toLowerCase()} records.</div>
            ) : null}
          </div>
        ))}
      </section>
      <section className="panel mt-8">
        <h2 className="section-title">Structured analyses</h2>
        <div className="mt-5 space-y-5">
          {client.analyses.map((analysis) => (
            <article className="rounded-xl border border-white/10 p-4" key={analysis.id}>
              <p className="text-xs uppercase tracking-wider text-slate-500">Job {analysis.job_id}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {analysis.requirements.map((item) => <span className="chip" key={item}>{item}</span>)}
              </div>
              <List title="Unknowns" values={analysis.unknowns} />
              <List title="Questions" values={analysis.questions} />
            </article>
          ))}
          {!client.analyses.length ? <p className="text-sm text-slate-500">No client analysis has been run yet.</p> : null}
        </div>
      </section>
    </main>
  );
}

function FactCard({fact}: {fact: ClientFact}) {
  return (
    <article className={`rounded-xl border p-4 ${factStyles[fact.classification]}`}>
      <div className="flex items-center justify-between gap-3">
        <span className="text-xs uppercase tracking-wider text-slate-400">{fact.fact_type}</span>
        <StatusBadge value={fact.verification_status} />
      </div>
      <p className="mt-3 text-sm leading-6 text-slate-200">{fact.fact}</p>
      <p className="mt-3 text-xs text-slate-500">Source: {fact.source_type ?? "none"}</p>
    </article>
  );
}

function List({title, values}: {title: string; values: string[]}) {
  if (!values.length) return null;
  return (
    <div className="mt-4">
      <p className="text-xs uppercase tracking-wider text-slate-500">{title}</p>
      <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-300">
        {values.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}
