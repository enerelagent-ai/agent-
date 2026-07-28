"use client";

import { ArrowDown, ArrowUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { DistrictInvestmentSummary } from "@/lib/api";
import { formatMnt, formatPercent } from "@/lib/format";

type SortKey = "avg_sale_price" | "gross_rental_yield_pct" | "roi_pct";

const SORTABLE_COLUMNS: { key: SortKey; label: string }[] = [
  { key: "avg_sale_price", label: "Дундаж зарах үнэ" },
  { key: "gross_rental_yield_pct", label: "Түрээсийн өгөөж" },
  { key: "roi_pct", label: "ROI" },
];

interface DistrictTableProps {
  rows: DistrictInvestmentSummary[];
  highlightedDistrict?: string | null;
}

export function DistrictTable({ rows, highlightedDistrict }: DistrictTableProps) {
  const [sortKey, setSortKey] = useState<SortKey | null>(null);
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("desc");
  const rowRefs = useRef<Record<string, HTMLTableRowElement | null>>({});

  useEffect(() => {
    if (highlightedDistrict) {
      rowRefs.current[highlightedDistrict]?.scrollIntoView({ behavior: "smooth", block: "center" });
    }
  }, [highlightedDistrict]);

  function handleSort(key: SortKey) {
    if (sortKey === key) {
      setSortDirection((d) => (d === "desc" ? "asc" : "desc"));
    } else {
      setSortKey(key);
      setSortDirection("desc");
    }
  }

  const sortedRows = sortKey
    ? [...rows].sort((a, b) => (a[sortKey] - b[sortKey]) * (sortDirection === "asc" ? 1 : -1))
    : rows;

  return (
    <div className="rounded-xl border border-line-grid bg-surface-card p-5">
      <h2 className="mb-4 text-base font-semibold text-ink-primary">
        Дүүргийн хөрөнгө оруулалтын үзүүлэлт
      </h2>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-line-grid text-ink-secondary">
              <th className="py-2 pr-4 font-medium">Дүүрэг</th>
              <SortableHeader
                column={SORTABLE_COLUMNS[0]}
                activeKey={sortKey}
                direction={sortDirection}
                onSort={handleSort}
              />
              <th className="py-2 pr-4 font-medium">Үнэ / мкв</th>
              <SortableHeader
                column={SORTABLE_COLUMNS[1]}
                activeKey={sortKey}
                direction={sortDirection}
                onSort={handleSort}
              />
              <SortableHeader
                column={SORTABLE_COLUMNS[2]}
                activeKey={sortKey}
                direction={sortDirection}
                onSort={handleSort}
              />
            </tr>
          </thead>
          <tbody>
            {sortedRows.map((row) => (
              <tr
                key={row.district}
                ref={(el) => {
                  rowRefs.current[row.district] = el;
                }}
                className={`border-b border-line-grid transition-colors last:border-0 ${
                  highlightedDistrict === row.district ? "bg-series-1/10" : ""
                }`}
              >
                <td className="py-2.5 pr-4 font-medium text-ink-primary">{row.district}</td>
                <td className="py-2.5 pr-4 tabular-nums text-ink-secondary">
                  {formatMnt(row.avg_sale_price)}
                </td>
                <td className="py-2.5 pr-4 tabular-nums text-ink-secondary">
                  {row.avg_price_per_sqm !== null ? formatMnt(row.avg_price_per_sqm) : "—"}
                </td>
                <td className="py-2.5 pr-4 tabular-nums text-ink-secondary">
                  {formatPercent(row.gross_rental_yield_pct)}
                </td>
                <td className="py-2.5 pr-4 tabular-nums text-ink-secondary">
                  {formatPercent(row.roi_pct)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function SortableHeader({
  column,
  activeKey,
  direction,
  onSort,
}: {
  column: { key: SortKey; label: string };
  activeKey: SortKey | null;
  direction: "asc" | "desc";
  onSort: (key: SortKey) => void;
}) {
  const isActive = activeKey === column.key;
  return (
    <th className="py-2 pr-4 font-medium">
      <button
        type="button"
        onClick={() => onSort(column.key)}
        className="flex items-center gap-1 text-ink-secondary hover:text-ink-primary"
      >
        {column.label}
        {isActive &&
          (direction === "desc" ? (
            <ArrowDown className="h-3.5 w-3.5" aria-hidden />
          ) : (
            <ArrowUp className="h-3.5 w-3.5" aria-hidden />
          ))}
      </button>
    </th>
  );
}
