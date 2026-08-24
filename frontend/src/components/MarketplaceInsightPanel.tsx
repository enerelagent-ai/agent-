import Link from "next/link";
import { ArrowUpRight, BarChart3, CalendarClock, Home, ShieldCheck } from "lucide-react";

import type { DistrictInvestmentSummary, TransactionType } from "@/lib/api";
import { formatMnt, formatPercent } from "@/lib/format";

const CONFIDENCE_LABELS: Record<DistrictInvestmentSummary["confidence_tier"], string> = {
  high: "Өндөр итгэлтэй",
  medium: "Дунд итгэлтэй",
  low: "Бага итгэлтэй",
  unavailable: "Тооцоолох боломжгүй",
};

export function MarketplaceInsightPanel({
  listingType,
  district,
  summaries,
}: {
  listingType: TransactionType;
  district: string;
  summaries: DistrictInvestmentSummary[];
}) {
  const selected = summaries.find((row) => row.district === district);

  return (
    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="bg-[#20334b] px-4 py-4 text-white">
        <div className="flex items-center gap-2">
          <BarChart3 className="h-5 w-5 text-[#ff8a5c]" aria-hidden />
          <h2 className="font-extrabold">Зах зээлийн анализ</h2>
        </div>
        <p className="mt-1 text-xs leading-5 text-slate-300">
          Зар хайхдаа зах зээлийн бодит харьцуулалтыг зэрэг харна.
        </p>
      </div>

      {selected ? (
        <div className="p-4">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">Сонгосон дүүрэг</p>
              <h3 className="mt-1 text-lg font-black text-slate-950">{selected.district}</h3>
            </div>
            <span className="rounded-full bg-emerald-50 px-2 py-1 text-[10px] font-bold text-emerald-700">
              {CONFIDENCE_LABELS[selected.confidence_tier]}
            </span>
          </div>

          <dl className="mt-4 divide-y divide-slate-100 border-y border-slate-100">
            <InsightRow
              label={listingType === "sale" ? "Медиан зарах үнэ" : "Медиан түрээс"}
              value={formatMnt(listingType === "sale" ? selected.median_sale_price : selected.reproducibility.median_rent_price)}
            />
            <InsightRow label="Дундаж м² үнэ" value={selected.avg_price_per_sqm === null ? "—" : formatMnt(selected.avg_price_per_sqm)} />
            <InsightRow label="Gross rental yield" value={formatPercent(selected.gross_rental_yield_pct)} accent />
            <InsightRow label="Харьцуулсан зар" value={`${selected.n_sale} зарах · ${selected.n_rent} түрээс`} />
          </dl>

          <div className="mt-4 space-y-2 text-[11px] leading-5 text-slate-500">
            <p className="flex items-start gap-2"><ShieldCheck className="mt-0.5 h-3.5 w-3.5 shrink-0 text-emerald-600" />Өрөөний coverage {selected.room_coverage_pct.toFixed(0)}% · Талбай {selected.area_coverage_pct.toFixed(0)}%</p>
            <p className="flex items-start gap-2"><CalendarClock className="mt-0.5 h-3.5 w-3.5 shrink-0" />Өгөгдөл: {new Date(selected.data_as_of).toLocaleDateString("mn-MN")}</p>
          </div>
        </div>
      ) : (
        <div className="p-4">
          <p className="text-sm font-bold text-slate-800">Дүүргүүдийн тойм</p>
          <p className="mt-1 text-xs leading-5 text-slate-500">Filter-ээс дүүрэг сонговол нарийвчилсан үзүүлэлт гарна.</p>
          <div className="mt-3 divide-y divide-slate-100 border-y border-slate-100">
            {summaries.slice(0, 5).map((row) => (
              <div key={row.district} className="flex items-center justify-between gap-3 py-3">
                <div className="min-w-0">
                  <p className="truncate text-xs font-bold text-slate-800">{row.district}</p>
                  <p className="mt-0.5 text-[10px] text-slate-400">{row.n_sale + row.n_rent} харьцуулалт</p>
                </div>
                <div className="text-right">
                  <p className="text-xs font-black text-emerald-700">{formatPercent(row.gross_rental_yield_pct)}</p>
                  <p className="text-[10px] text-slate-400">yield</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="border-t border-slate-100 bg-slate-50 p-3">
        <Link href="/dashboard" className="flex min-h-10 items-center justify-center gap-1.5 rounded-md bg-white text-xs font-extrabold text-[#20334b] ring-1 ring-slate-200 transition hover:text-[#e85520]">
          Дэлгэрэнгүй анализ <ArrowUpRight className="h-3.5 w-3.5" />
        </Link>
        <Link href="/calculator" className="mt-2 flex items-center justify-center gap-1.5 py-1 text-[11px] font-semibold text-slate-500 hover:text-[#e85520]">
          <Home className="h-3.5 w-3.5" /> Өөрийн өгөөжийг тооцоолох
        </Link>
      </div>
    </section>
  );
}

function InsightRow({ label, value, accent = false }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-3 py-3">
      <dt className="text-[11px] text-slate-500">{label}</dt>
      <dd className={`text-right text-xs font-extrabold ${accent ? "text-emerald-700" : "text-slate-900"}`}>{value}</dd>
    </div>
  );
}
