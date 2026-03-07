import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkyPilot — AI Flight Assistant",
  description:
    "Find the best flights worldwide with our AI-powered travel assistant. Compare prices, routes, and dates instantly.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {/* Animated background gradient */}
        <div className="bg-animated-gradient" />

        {/* Main content */}
        <div className="relative z-10 h-screen flex flex-col">{children}</div>
      </body>
    </html>
  );
}
