import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkyMind — AI Travel Assistant",
  description:
    "Find the best flights and hotels worldwide with SkyMind, your AI-powered travel assistant.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Starfield + background canvas */}
        <div className="bg-canvas" />
        <div className="stars" />

        {/* Main content above backgrounds */}
        <div className="relative z-10 h-screen flex flex-col">
          {children}
        </div>
      </body>
    </html>
  );
}
