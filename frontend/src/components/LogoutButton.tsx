"use client";

import { LogOut } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

// A session with no way to end it is a half-built primitive -- this is the
// counterpart to LoginForm.tsx / app/api/auth/logout/route.ts. Clearing the
// cookie only affects this browser (see that route's comment: there's no
// server-side session store to revoke against), which is an acceptable
// tradeoff for a single-admin tool.
export function LogoutButton() {
  const router = useRouter();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  async function handleLogout() {
    if (isLoggingOut) return;
    setIsLoggingOut(true);
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      router.push("/login");
    }
  }

  return (
    <button
      type="button"
      onClick={handleLogout}
      disabled={isLoggingOut}
      aria-label="Гарах"
      title="Гарах"
      className="flex h-8 w-8 items-center justify-center rounded-full text-ink-muted transition-colors hover:bg-line-grid hover:text-ink-primary disabled:opacity-60 focus:outline-none focus-visible:ring-2 focus-visible:ring-series-1/40"
    >
      <LogOut className="h-4 w-4" aria-hidden />
    </button>
  );
}
