"use client";

import { ArrowLeft, Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { LogoutButton } from "@/components/LogoutButton";
import { getDealAlerts } from "@/lib/api";

export function Topbar({ title, publicView = false }: { title: string; publicView?: boolean }) {
  const [unseenCount, setUnseenCount] = useState(0);

  useEffect(() => {
    if (!publicView) {
      getDealAlerts(1).then((feed) => setUnseenCount(feed.unseen_count)).catch(() => undefined);
    }
    const clearBadge = () => setUnseenCount(0);
    window.addEventListener("deal-alerts-seen", clearBadge);
    return () => window.removeEventListener("deal-alerts-seen", clearBadge);
  }, [publicView]);

  return (
    <header className="flex items-center justify-between border-b border-line-grid bg-surface-card px-4 py-4 sm:px-8 sm:py-5">
      <h1 className="text-xl font-semibold text-ink-primary">{title}</h1>
      {publicView ? (
        <Link href="/sale" className="flex items-center gap-1.5 rounded-md border border-line-grid px-3 py-2 text-sm font-semibold text-ink-secondary hover:bg-surface-page">
          <ArrowLeft className="h-4 w-4" aria-hidden /> Зарын зах
        </Link>
      ) : (
      <div className="flex items-center gap-4">
        <Link href="/notifications" aria-label={`${unseenCount} шинэ deal мэдэгдэл`} className="relative text-ink-muted hover:text-ink-primary">
          <Bell className="h-5 w-5" aria-hidden />
          {unseenCount > 0 && (
            <span className="absolute -right-2.5 -top-2.5 flex min-h-4 min-w-4 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-semibold leading-none text-white">
              {unseenCount > 99 ? "99+" : unseenCount}
            </span>
          )}
        </Link>
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-series-1/10 text-sm font-medium text-series-1">
            А
          </div>
          <span className="text-sm text-ink-secondary">Админ хэрэглэгч</span>
        </div>
        <LogoutButton />
      </div>
      )}
    </header>
  );
}
