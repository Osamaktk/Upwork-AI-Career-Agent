"use client";

import Link from "next/link";
import {FormEvent, useState} from "react";

import {useSession} from "./session-provider";

const navigation = [
  ["Dashboard", "/"],
  ["Jobs", "/jobs"],
  ["Clients", "/clients"],
  ["Profile", "/profile"],
  ["Portfolio", "/portfolio"],
];

export function AppShell({children}: {children: React.ReactNode}) {
  const {token, login, logout} = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    setError("");
    try {
      await login(email, password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="border-b border-emerald-100/10 bg-[#081410]/90 backdrop-blur">
        <div className="mx-auto flex max-w-7xl items-center justify-between gap-6 px-6 py-4">
          <Link href="/" className="font-semibold tracking-tight text-emerald-200">
            Career Agent
          </Link>
          <nav className="flex items-center gap-5 text-sm text-slate-300">
            {navigation.map(([label, href]) => (
              <Link key={href} href={href} className="transition hover:text-emerald-300">
                {label}
              </Link>
            ))}
            {token ? (
              <button onClick={logout} className="rounded-full border border-white/15 px-3 py-1.5">
                Sign out
              </button>
            ) : null}
          </nav>
        </div>
      </header>
      {!token ? (
        <main className="mx-auto max-w-md px-6 py-24">
          <form onSubmit={submit} className="panel space-y-5">
            <div>
              <p className="eyebrow">Local workspace</p>
              <h1 className="mt-2 text-3xl font-semibold">Sign in to review sample data</h1>
              <p className="mt-3 text-sm text-slate-400">
                Use the local account created through the Phase 1 authentication API.
              </p>
            </div>
            <input
              className="input"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email"
              required
            />
            <input
              className="input"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              required
            />
            {error ? <p className="text-sm text-rose-300">{error}</p> : null}
            <button className="button-primary w-full" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </button>
          </form>
        </main>
      ) : (
        children
      )}
    </div>
  );
}
