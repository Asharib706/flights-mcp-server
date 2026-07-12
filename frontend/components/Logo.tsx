/**
 * SkyMind's Waypoint mark: an open ring (origin) connected by a route to a
 * filled dot (destination) — built from the Overland accent pair directly,
 * fixed-color like any app icon (doesn't theme-swap with the page).
 */
export function LogoBadge({ size = 40, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="SkyMind"
    >
      <rect x="0" y="0" width="64" height="64" rx="16" fill="#1F5C56" />
      <circle cx="16" cy="46" r="4.5" fill="none" stroke="#F3EFE6" strokeWidth="3" />
      <path
        d="M16,46 C 20,30 34,22 45,18"
        fill="none"
        stroke="#F3EFE6"
        strokeWidth="4.2"
        strokeLinecap="round"
      />
      <circle cx="46" cy="18" r="5.5" fill="#E0966A" />
    </svg>
  );
}

/** Flat, single-color version for inline use next to text — inherits currentColor. */
export function LogoMark({ size = 24, className }: { size?: number; className?: string }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      className={className}
      role="img"
      aria-label="SkyMind"
    >
      <circle cx="16" cy="46" r="4.5" fill="none" stroke="currentColor" strokeWidth="3" opacity="0.55" />
      <path
        d="M16,46 C 20,30 34,22 45,18"
        fill="none"
        stroke="currentColor"
        strokeWidth="4.2"
        strokeLinecap="round"
      />
      <circle cx="46" cy="18" r="5.5" fill="#B5714A" />
    </svg>
  );
}
