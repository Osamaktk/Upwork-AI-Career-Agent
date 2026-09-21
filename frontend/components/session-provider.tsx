"use client";

import {createContext, useContext, useEffect, useMemo, useState} from "react";

import {apiRequest} from "@/lib/api";

type SessionContextValue = {
  token: string;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const SessionContext = createContext<SessionContextValue | null>(null);

export function SessionProvider({children}: {children: React.ReactNode}) {
  const [token, setToken] = useState("");

  useEffect(() => {
    setToken(sessionStorage.getItem("career-agent-token") ?? "");
  }, []);

  const value = useMemo<SessionContextValue>(
    () => ({
      token,
      login: async (email: string, password: string) => {
        const result = await apiRequest<{access_token: string}>("/api/v1/auth/login", "", {
          method: "POST",
          body: JSON.stringify({email, password}),
        });
        sessionStorage.setItem("career-agent-token", result.access_token);
        setToken(result.access_token);
      },
      logout: () => {
        sessionStorage.removeItem("career-agent-token");
        setToken("");
      },
    }),
    [token],
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const context = useContext(SessionContext);
  if (!context) {
    throw new Error("useSession must be used inside SessionProvider");
  }
  return context;
}
