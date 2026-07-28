"use client";

import { useState } from "react";
import type { ListingTypeCount } from "@/lib/api";
import { formatNumber } from "@/lib/format";

const SEGMENT_LABELS: Record<string, string> = {
  "apartments:sale": "Орон сууц — Худалдах",
  "apartments:rent": "Орон сууц — Түрээслэх",
  "other:sale": "Бусад төрөл — Худалдах",
  "other:rent": "Бусад төрөл — Түрээслэх",
};

// Fixed categorical order, assigned once and never cycled or reassigned by
// rank — slots 1-4 of the dataviz skill's validated default palette.
const SEGMENT_ORDER = ["apartments:sale", "apartments:rent", "other:sale", "other:rent"];
const SEGMENT_COLORS: Record<string, string> = {
  "apartments:sale": "#2a78d6",
  "apartments:rent": "#eb6834",
  "other:sale": "#1baf7a",
  "other:rent": "#eda100",
};

const RADIUS = 60;
const STROKE = 28;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;
const GAP_DEGREES = 3; // surface-color gap between adjacent segments

export function DonutChart({ data }: { data: ListingTypeCount[] }) {
  const [hovered, setHovered] = useState<string | null>(null);

  const byKey = new Map(data.map((d) => [`${d.bucket}:${d.listing_type}`, d.n]));
  const total = data.reduce((sum, d) => sum + d.n, 0);

  let cumulativeDegrees = 0;
  const segments = SEGMENT_ORDER.map((key) => {
    const n = byKey.get(key) ?? 0;
    const fraction = total > 0 ? n / total : 0;
    const degrees = fraction * 360;
    const segment = {
      key,
      n,
      fraction,
      startDegrees: cumulativeDegrees,
      visibleDegrees: Math.max(degrees - GAP_DEGREES, 0),
    };
    cumulativeDegrees += degrees;
    return segment;
  });

  return (
    <div className="rounded-xl border border-line-grid bg-surface-card p-5">
      <h2 className="mb-4 text-base font-semibold text-ink-primary">Зарын төрөл</h2>
      <div className="flex flex-col items-center gap-6 sm:flex-row">
        <div className="relative h-40 w-40 shrink-0">
          <svg viewBox="0 0 140 140" className="h-full w-full -rotate-90">
            {segments.map((s) => (
              <circle
                key={s.key}
                cx={70}
                cy={70}
                r={RADIUS}
                fill="none"
                stroke={SEGMENT_COLORS[s.key]}
                strokeWidth={hovered === s.key ? STROKE + 4 : STROKE}
                strokeDasharray={`${(s.visibleDegrees / 360) * CIRCUMFERENCE} ${CIRCUMFERENCE}`}
                strokeDashoffset={-(s.startDegrees / 360) * CIRCUMFERENCE}
                onMouseEnter={() => setHovered(s.key)}
                onMouseLeave={() => setHovered(null)}
                className="cursor-pointer transition-[stroke-width]"
              />
            ))}
          </svg>
          <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="text-lg font-semibold text-ink-primary">{formatNumber(total)}</span>
            <span className="text-xs text-ink-muted">нийт зар</span>
          </div>
          {hovered && (
            <div className="pointer-events-none absolute -bottom-3 left-1/2 z-10 -translate-x-1/2 translate-y-full whitespace-nowrap rounded-md border border-line-grid bg-surface-card px-2.5 py-1.5 text-xs text-ink-primary shadow-md">
              {SEGMENT_LABELS[hovered]}: {formatNumber(byKey.get(hovered) ?? 0)}
            </div>
          )}
        </div>

        {/* Legend doubles as the table view: every value is visible here,
            not gated behind hover. */}
        <ul className="flex flex-1 flex-col gap-2 text-sm">
          {segments.map((s) => (
            <li
              key={s.key}
              className="flex items-center justify-between gap-3"
              onMouseEnter={() => setHovered(s.key)}
              onMouseLeave={() => setHovered(null)}
            >
              <span className="flex items-center gap-2 text-ink-secondary">
                <span
                  className="h-2.5 w-2.5 shrink-0 rounded-full"
                  style={{ backgroundColor: SEGMENT_COLORS[s.key] }}
                  aria-hidden
                />
                {SEGMENT_LABELS[s.key]}
              </span>
              <span className="tabular-nums text-ink-primary">
                {formatNumber(s.n)} ({(s.fraction * 100).toFixed(0)}%)
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
