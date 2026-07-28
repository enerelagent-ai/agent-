import type { LucideIcon } from "lucide-react";

interface StatTileProps {
  label: string;
  value: string;
  icon: LucideIcon;
  caption?: string;
}

export function StatTile({ label, value, icon: Icon, caption }: StatTileProps) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border border-line-grid bg-surface-card p-5">
      <div className="flex items-center justify-between">
        <span className="text-sm text-ink-secondary">{label}</span>
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-series-1/10">
          <Icon className="h-4 w-4 text-series-1" aria-hidden />
        </div>
      </div>
      <div className="text-2xl font-semibold text-ink-primary">{value}</div>
      {caption && <div className="text-xs text-ink-muted">{caption}</div>}
    </div>
  );
}
