"use client";

import {useCallback, useEffect, useState} from "react";

import {ErrorState, LoadingState, StatusBadge} from "@/components/ui";
import {useSession} from "@/components/session-provider";
import {apiRequest} from "@/lib/api";
import type {Claim, Profile} from "@/lib/types";

export default function ProfilePage() {
  const {token} = useSession();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [claims, setClaims] = useState<Claim[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const [profileData, claimData] = await Promise.all([
        apiRequest<Profile>("/api/v1/profile", token),
        apiRequest<Claim[]>("/api/v1/claims", token),
      ]);
      setProfile(profileData);
      setClaims(claimData);
      setError("");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to load profile");
    }
  }, [token]);

  useEffect(() => { void load(); }, [load]);
  if (error && !profile) return <main className="page"><ErrorState message={error} /></main>;
  if (!profile) return <main className="page"><LoadingState /></main>;

  const skillGroups = [
    ["Primary", profile.primary_skills],
    ["Secondary", profile.secondary_skills],
    ["Languages", profile.programming_languages],
    ["Frameworks", profile.frameworks],
    ["Tools", profile.tools],
    ["Domains", profile.domains],
  ] as const;

  return (
    <main className="page">
      <div className="page-heading">
        <div>
          <p className="eyebrow">Profile · {profile.completeness}% complete</p>
          <h1 className="page-title">{profile.title ?? "Untitled profile"}</h1>
          <p className="page-copy">{profile.overview ?? "No overview supplied."}</p>
        </div>
        <StatusBadge value={profile.verification_status} />
      </div>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel">
          <h2 className="section-title">Capabilities</h2>
          <div className="mt-5 space-y-5">
            {skillGroups.map(([label, values]) => (
              <div key={label}>
                <p className="text-xs uppercase tracking-wider text-slate-500">{label}</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  {values.map((item) => <span className="chip" key={item}>{item}</span>)}
                  {!values.length ? <span className="text-sm text-slate-500">Empty</span> : null}
                </div>
              </div>
            ))}
          </div>
        </section>
        <section className="panel">
          <h2 className="section-title">Evidence claims</h2>
          <div className="mt-5 space-y-4">
            {claims.map((claim) => (
              <article key={claim.id} className="rounded-xl border border-white/10 p-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm leading-6">{claim.claim}</p>
                  <StatusBadge value={claim.verification_status} />
                </div>
                <p className="mt-2 text-xs text-slate-500">{claim.category} · {claim.source}</p>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
