"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../components/AuthProvider";
import AuthLayout, { AuthError, AuthField, AuthSubmit } from "../../components/AuthLayout";
import { ApiError } from "../../lib/api";

export default function RegisterPage() {
  const { user, loading, register } = useAuth();
  const router = useRouter();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!loading && user) router.replace("/");
  }, [loading, user, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password, displayName || undefined);
      router.push("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Couldn't reach SkyMind. Try again.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout
      eyebrow="Get started"
      title="Create your account"
      subtitle="A few quick questions after this, then SkyMind starts tailoring trips to you."
      footer={
        <>
          Already have an account?{" "}
          <Link href="/login" className="font-semibold" style={{ color: "var(--accent)" }}>
            Sign in
          </Link>
        </>
      }
    >
      <form onSubmit={handleSubmit} className="flex flex-col gap-4">
        {error && <AuthError message={error} />}
        <AuthField
          label="Name (optional)"
          type="text"
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
        <AuthField
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <AuthField
          label="Password"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <span className="text-xs -mt-2" style={{ color: "var(--muted)" }}>
          At least 8 characters.
        </span>
        <AuthSubmit disabled={submitting}>{submitting ? "Creating account…" : "Create account"}</AuthSubmit>
      </form>
    </AuthLayout>
  );
}
