/**
 * SkyMind's real client logo (brain/plane/clouds mark + "SkyMind" wordmark),
 * cropped and background-removed from the marketing asset — see
 * assets/brand/skymind-logo-original.jpeg for the untouched source.
 *
 * The wordmark's "SKY" is a fixed dark navy baked into the raster, so it has
 * no way to invert for dark mode on its own. Rather than recolor pixels on a
 * compressed JPEG-derived asset, both components sit on a `--logo-plate`
 * backing (transparent in light mode, a light stone chip in dark mode — see
 * globals.css) so the logo's actual colors stay untouched either way.
 */
import { CSSProperties } from "react";

/** Icon + "SkyMind" wordmark together — for standalone placements (auth pages, loading state). */
export function LogoFull({ height = 40, className }: { height?: number; className?: string }) {
  const style: CSSProperties = { background: "var(--logo-plate)" };
  return (
    <span className={`inline-flex items-center rounded-2xl px-2.5 py-1.5 ${className || ""}`} style={style}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/brand/skymind-logo-full.png" alt="SkyMind" style={{ height, width: "auto" }} />
    </span>
  );
}

/** Icon only, no wordmark — for compact rows that already show "SkyMind" as text nearby. */
export function LogoIcon({ height = 32, className }: { height?: number; className?: string }) {
  const style: CSSProperties = { background: "var(--logo-plate)" };
  return (
    <span className={`inline-flex items-center rounded-xl px-1.5 py-1 ${className || ""}`} style={style}>
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src="/brand/skymind-icon.png" alt="SkyMind" style={{ height, width: "auto" }} />
    </span>
  );
}
