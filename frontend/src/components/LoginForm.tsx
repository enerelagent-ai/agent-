"use client";

import { Eye, EyeOff, Loader2 } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useRef, useState } from "react";

const GENERIC_ERROR = "Нэвтрэх нэр эсвэл нууц үг буруу байна.";

export function LoginForm({ next }: { next: string }) {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [succeeded, setSucceeded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const passwordRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!succeeded) return;
    // Respect prefers-reduced-motion: skip the fade-out delay and go
    // straight there instead of waiting on a transition that won't play.
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const timer = setTimeout(() => router.push(next), reduceMotion ? 0 : 280);
    return () => clearTimeout(timer);
  }, [succeeded, next, router]);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (isSubmitting) return; // guards against Enter-spam double submits
    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        setError(GENERIC_ERROR);
        setPassword("");
        passwordRef.current?.focus();
        return;
      }
      setSucceeded(true);
    } catch {
      setError(GENERIC_ERROR);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div
      className={`w-full max-w-[420px] transition-opacity motion-safe:duration-300 ${
        succeeded ? "opacity-0" : "opacity-100"
      }`}
    >
      <h1 className="text-2xl font-semibold text-ink-primary">Тавтай морилно уу</h1>
      <p className="mt-2 text-sm text-ink-secondary">Шинжилгээний платформдоо нэвтэрнэ үү.</p>

      <form onSubmit={handleSubmit} className="mt-8 space-y-5" noValidate>
        <div>
          <label htmlFor="username" className="mb-2 block text-sm font-medium text-ink-primary">
            Нэвтрэх нэр
          </label>
          <input
            id="username"
            name="username"
            type="text"
            autoComplete="username"
            autoFocus
            required
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            placeholder="Нэвтрэх нэрээ оруулна уу"
            disabled={isSubmitting}
            className="h-[52px] w-full rounded-xl border border-line-grid bg-surface-card px-4 text-base text-ink-primary outline-none transition-colors duration-200 placeholder:text-ink-muted hover:border-line-axis focus:border-series-1 focus:ring-2 focus:ring-series-1/20 disabled:opacity-60"
          />
        </div>

        <div>
          <label htmlFor="password" className="mb-2 block text-sm font-medium text-ink-primary">
            Нууц үг
          </label>
          <div className="relative">
            <input
              ref={passwordRef}
              id="password"
              name="password"
              type={showPassword ? "text" : "password"}
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Нууц үгээ оруулна уу"
              disabled={isSubmitting}
              className="h-[52px] w-full rounded-xl border border-line-grid bg-surface-card px-4 pr-12 text-base text-ink-primary outline-none transition-colors duration-200 placeholder:text-ink-muted hover:border-line-axis focus:border-series-1 focus:ring-2 focus:ring-series-1/20 disabled:opacity-60"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Нууц үг нуух" : "Нууц үг харуулах"}
              aria-pressed={showPassword}
              className="absolute right-0 top-0 flex h-[52px] w-12 items-center justify-center text-ink-muted transition-colors hover:text-ink-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-series-1/40 rounded-r-xl"
            >
              {showPassword ? (
                <EyeOff className="h-4 w-4" aria-hidden />
              ) : (
                <Eye className="h-4 w-4" aria-hidden />
              )}
            </button>
          </div>
        </div>

        {/* Reserved space regardless of error presence, so the button below
            never shifts position when the message appears. */}
        <div className="min-h-5" role="alert" aria-live="assertive">
          {error && <p className="text-sm text-red-700">{error}</p>}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="flex h-[52px] w-full items-center justify-center gap-2 rounded-xl bg-series-1 text-base font-medium text-white transition-colors duration-200 hover:bg-series-1/90 active:bg-series-1/80 disabled:cursor-not-allowed disabled:opacity-70 focus:outline-none focus-visible:ring-2 focus-visible:ring-series-1/40 focus-visible:ring-offset-2"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="h-4 w-4 motion-safe:animate-spin" aria-hidden />
              Нэвтэрч байна…
            </>
          ) : (
            "Нэвтрэх"
          )}
        </button>
      </form>

      <p className="mt-6 text-center text-xs text-ink-muted">
        Зөвхөн эрх бүхий хэрэглэгчдэд зориулагдсан
      </p>
    </div>
  );
}
