import { Bell } from "lucide-react";

import { LogoutButton } from "@/components/LogoutButton";

export function Topbar({ title }: { title: string }) {
  return (
    <header className="flex items-center justify-between border-b border-line-grid bg-surface-card px-8 py-5">
      <h1 className="text-xl font-semibold text-ink-primary">{title}</h1>
      <div className="flex items-center gap-4">
        <Bell className="h-5 w-5 text-ink-muted" aria-hidden />
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
