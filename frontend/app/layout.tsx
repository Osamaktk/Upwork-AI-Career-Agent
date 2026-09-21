import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Upwork AI Career Agent",
  description: "Human-controlled freelancing workflow dashboard",
};

export default function RootLayout({children}: Readonly<{children: React.ReactNode}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
