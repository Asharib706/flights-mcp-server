import { ImageResponse } from "next/og";

export const size = { width: 64, height: 64 };
export const contentType = "image/png";

export default function Icon() {
  return new ImageResponse(
    (
      <svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
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
    ),
    { ...size }
  );
}
