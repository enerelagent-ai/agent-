"use client";

import { Bell } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { LogoutButton } from "@/components/LogoutButton";
import { getDealAlerts } from "@/lib/api";

export function Topbar({ title }: { title: string }) {
  const [unseenCount, setUnseenCount] = useState(0);

  useEffect(() => {
    getDealAlerts(1).then((feed) => setUnseenCount(feed.unseen_count)).catch(() => undefined);
    const clearBadge = () => setUnseenCount(0);
    window.addEventListener("deal-alerts-seen", clearBadge);
    return () => window.removeEventListener("deal-alerts-seen", clearBadge);
  }, []);

  return (
    <header className="flex items-center justify-between border-b border-line-grid bg-surface-card px-8 py-5">
      <h1 className="text-xl font-semibold text-ink-primary">{title}</h1>
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
    </header>
  );
}
