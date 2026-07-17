"use client";

import { InputHTMLAttributes, ReactNode } from "react";
import { LogoFull } from "./Logo";

interface AuthLayoutProps {
  eyebrow: string;
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}

export default function AuthLayout({ eyebrow, title, subtitle, children, footer }: AuthLayoutProps) {
  return (
    <div className="flex-1 flex items-center justify-center px-4 py-10 overflow-y-auto scrollbar-thin animate-fade-up">
      <div className="w-full max-w-md">
        <div className="flex flex-col items-center text-center mb-8">
          <LogoFull height={64} className="mb-5 shadow-lg" />
          <span
            className="text-[10px] tracking-[0.2em] uppercase font-semibold"
            style={{ color: "var(--muted)" }}
          >
            {eyebrow}
          </span>
          <h1 className="font-serif-italic text-4xl mt-2 mb-2" style={{ color: "var(--text)" }}>
            {title}
          </h1>
          <p className="text-sm max-w-xs" style={{ color: "var(--muted)" }}>
            {subtitle}
          </p>
        </div>

        <div className="card rounded-3xl p-7 md:p-8">{children}</div>

        <div className="text-center mt-6 text-sm" style={{ color: "var(--muted)" }}>
          {footer}
        </div>
      </div>
    </div>
  );
}

export function AuthField({
  label,
  ...props
}: { label: string } & InputHTMLAttributes<HTMLInputElement>) {
  return (
    <label className="flex flex-col gap-1.5 text-left">
      <span className="text-xs font-semibold" style={{ color: "var(--muted)" }}>
        {label}
      </span>
      <input
        {...props}
        className="rounded-xl px-4 py-3 text-sm outline-none border transition-colors duration-150 focus:border-current"
        style={{ background: "var(--surface-2)", borderColor: "var(--border)", color: "var(--text)" }}
      />
    </label>
  );
}

export function AuthError({ message }: { message: string }) {
  return (
    <div
      role="alert"
      className="text-sm rounded-xl px-4 py-3 border"
      style={{
        background: "color-mix(in srgb, var(--danger) 12%, transparent)",
        borderColor: "color-mix(in srgb, var(--danger) 35%, transparent)",
        color: "var(--danger)",
      }}
    >
      {message}
    </div>
  );
}

export function AuthSubmit({ children, disabled }: { children: ReactNode; disabled?: boolean }) {
  return (
    <button
      type="submit"
      disabled={disabled}
      className="rounded-xl py-3.5 text-sm font-semibold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
      style={{ background: "var(--accent)", color: "var(--on-accent)" }}
    >
      {children}
    </button>
  );
}
