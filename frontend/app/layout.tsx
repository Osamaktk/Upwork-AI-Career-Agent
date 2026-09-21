import type { Metadata } from "next";
import {AppShell} from "@/components/app-shell";
import {SessionProvider} from "@/components/session-provider";
import "./globals.css";

export const metadata: Metadata = {
  title: "Upwork AI Career Agent",
  description: "Human-controlled freelancing workflow dashboard",
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return (
    <html lang="en">
      <body>
        <SessionProvider>
          <AppShell>{children}</AppShell>
        </SessionProvider>
      </body>
    </html>
  );
}
