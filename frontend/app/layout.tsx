import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HindGPT | Enterprise Console",
  description: "HindGPT enterprise console rebuilt as a Next.js page.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}