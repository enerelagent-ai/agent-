"use client";

import { useState } from "react";
import type { PriceTrendPoint } from "@/lib/api";
import { formatMnt } from "@/lib/format";

const WIDTH = 480;
const HEIGHT = 200;
const PADDING = { top: 16, right: 16, bottom: 12, left: 16 };
const TITLE = "Үнийн чиг хандлага (мкв-р дундаж, орон сууц, худалдах)";

export function PriceTrendChart({ data }: { data: PriceTrendPoint[] }) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);
  const points = data.filter((d) => d.avg_price_per_sqm !== null);

  if (points.length === 0) {
    return (
      <div className="rounded-xl border border-line-grid bg-surface-card p-5">
        <h2 className="mb-2 text-base font-semibold text-ink-primary">{TITLE}</h2>
        <p className="text-sm text-ink-muted">Одоогоор мэдээлэл алга.</p>
      </div>
    );
  }

  // A single point is not a trend — a "line" through one value is a
  // meaningless mark. Show it as a plain reading instead; this branch goes
  // away on its own once snapshot_market_prices() has run more than once.
  if (points.length === 1) {
    const point = points[0];
    return (
      <div className="rounded-xl border border-line-grid bg-surface-card p-5">
        <h2 className="mb-2 text-base font-semibold text-ink-primary">{TITLE}</h2>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-semibold text-ink-primary">
            {formatMnt(point.avg_price_per_sqm as number)}
          </span>
          <span className="text-xs text-ink-muted">{point.snapshot_date}</span>
        </div>
        <p className="mt-3 text-xs text-ink-muted">
          Эхний хэмжилт. Тооцоолол дахин ажиллах бүрд шинэ цэг нэмэгдэж, график
          цаашид өөрөө баяжина.
        </p>
      </div>
    );
  }

  const values = points.map((p) => p.avg_price_per_sqm as number);
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const valueRange = maxValue - minValue || 1;
  const plotWidth = WIDTH - PADDING.left - PADDING.right;
  const plotHeight = HEIGHT - PADDING.top - PADDING.bottom;

  const coords = points.map((p, i) => ({
    x: PADDING.left + (i / (points.length - 1)) * plotWidth,
    y: PADDING.top + plotHeight - ((p.avg_price_per_sqm as number - minValue) / valueRange) * plotHeight,
    point: p,
  }));
  const linePath = coords.map((c, i) => `${i === 0 ? "M" : "L"} ${c.x} ${c.y}`).join(" ");
  const areaPath =
    `${linePath} L ${coords[coords.length - 1].x} ${PADDING.top + plotHeight}` +
    ` L ${coords[0].x} ${PADDING.top + plotHeight} Z`;
  const cellWidth = plotWidth / points.length;

  return (
    <div className="rounded-xl border border-line-grid bg-surface-card p-5">
      <h2 className="mb-4 text-base font-semibold text-ink-primary">{TITLE}</h2>
      <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} className="w-full">
        <line
          x1={PADDING.left}
          y1={PADDING.top + plotHeight}
          x2={WIDTH - PADDING.right}
          y2={PADDING.top + plotHeight}
          stroke="#e1e0d9"
          strokeWidth={1}
        />
        <path d={areaPath} fill="#2a78d6" fillOpacity={0.1} stroke="none" />
        <path
          d={linePath}
          fill="none"
          stroke="#2a78d6"
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {coords.map((c, i) => (
          <g key={c.point.snapshot_date}>
            <circle
              cx={c.x}
              cy={c.y}
              r={hoverIndex === i ? 6 : 4}
              fill="#2a78d6"
              stroke="#fcfcfb"
              strokeWidth={2}
            />
            <rect
              x={c.x - cellWidth / 2}
              y={PADDING.top}
              width={cellWidth}
              height={plotHeight}
              fill="transparent"
              onMouseEnter={() => setHoverIndex(i)}
              onMouseLeave={() => setHoverIndex(null)}
              className="cursor-pointer"
            />
          </g>
        ))}
        {hoverIndex !== null && (
          <text
            x={coords[hoverIndex].x}
            y={Math.max(coords[hoverIndex].y - 12, 12)}
            textAnchor="middle"
            fontSize={11}
            fill="#0b0b0b"
          >
            {formatMnt(coords[hoverIndex].point.avg_price_per_sqm as number)}
          </text>
        )}
      </svg>
    </div>
  );
}
