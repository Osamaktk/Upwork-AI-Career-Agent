"use client";

import Link from "next/link";
import {useEffect, useState} from "react";

import {ErrorState, LoadingState} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {Client} from "@/lib/types";

export default function ClientsPage() {
  const {token} = useSession();
  const [clients, setClients] = useState<Client[] | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    apiRequest<Client[]>("/api/v1/clients", token)
      .then(setClients)
      .catch((caught) => setError(caught instanceof Error ? caught.message : "Unable to load clients"));
  }, [token]);

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Client intelligence</p>
          <h1 className="page-title">Sourced client context</h1>
          <p className="page-copy">Facts, inferences, and unknowns remain visibly separate.</p>
        </div>
      </div>
      {error ? <ErrorState message={error} /> : null}
      {!clients ? (
        <LoadingState />
      ) : (
        <div className="grid gap-5 md:grid-cols-2">
          {clients.map((client) => (
            <Link className="panel block transition hover:border-emerald-300/30" href={`/clients/${client.id}`} key={client.id}>
              <p className="text-xs uppercase tracking-wider text-slate-500">{client.source}</p>
              <h2 className="mt-2 text-xl font-semibold">{client.company ?? client.name ?? "Unnamed client"}</h2>
              <p className="mt-3 text-sm text-slate-400">{client.summary ?? "Open the record to review sourced evidence."}</p>
            </Link>
          ))}
          {!clients.length ? <div className="panel text-slate-400">No client records yet.</div> : null}
        </div>
      )}
    </main>
  );
}
