import type { DistrictInvestmentSummary } from "@/lib/api";
import { formatMnt, formatPercent } from "@/lib/format";

export function DistrictTable({ rows }: { rows: DistrictInvestmentSummary[] }) {
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
              <th className="py-2 pr-4 font-medium">Дундаж зарах үнэ</th>
              <th className="py-2 pr-4 font-medium">Үнэ / мкв</th>
              <th className="py-2 pr-4 font-medium">Түрээсийн өгөөж</th>
              <th className="py-2 pr-4 font-medium">ROI</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.district} className="border-b border-line-grid last:border-0">
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
