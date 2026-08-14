import { formatMnt } from "@/lib/format";

export function PriceDistributionBar({ min, median, max }: { min: number; median: number; max: number }) {
  const span = max - min;
  const medianPosition = span > 0 ? Math.min(100, Math.max(0, ((median - min) / span) * 100)) : 50;

  return (
    <div className="min-w-52" title={`Min ${formatMnt(min)} · Median ${formatMnt(median)} · Max ${formatMnt(max)}`}>
      <div className="relative mb-1.5 h-1.5 rounded-full bg-line-grid">
        <div className="absolute inset-y-0 left-0 right-0 rounded-full bg-series-1/25" />
        <span
          className="absolute top-1/2 h-3 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-series-1"
          style={{ left: `${medianPosition}%` }}
          aria-hidden
        />
      </div>
      <div className="flex justify-between gap-2 text-[10px] tabular-nums text-ink-muted">
        <span>{formatMnt(min)}</span>
        <span className="font-medium text-series-1">M {formatMnt(median)}</span>
        <span>{formatMnt(max)}</span>
      </div>
    </div>
  );
}
