"use client";

import { ExternalLink, GitCompareArrows, X } from "lucide-react";
import type { Listing } from "@/lib/api";
import { formatListingPrice, formatMnt, formatPercent } from "@/lib/format";

export const MAX_COMPARE_LISTINGS = 3;

export function CompareTray({
  listings,
  open,
  onOpen,
  onClose,
  onRemove,
  onClear,
}: {
  listings: Listing[];
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  onRemove: (id: number) => void;
  onClear: () => void;
}) {
  if (listings.length === 0) return null;

  return (
    <>
      <div className="fixed bottom-5 left-1/2 z-40 flex w-[min(92vw,720px)] -translate-x-1/2 items-center gap-3 rounded-xl border border-line-grid bg-[#111a3d] p-3 text-white shadow-xl">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/10">
          <GitCompareArrows className="h-4 w-4" aria-hidden />
        </div>
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">Харьцуулах жагсаалт · {listings.length}/{MAX_COMPARE_LISTINGS}</p>
          <p className="truncate text-xs text-white/55">{listings.map((row) => row.title).join(" · ")}</p>
        </div>
        <button type="button" onClick={onClear} className="text-xs text-white/60 hover:text-white">Цэвэрлэх</button>
        <button
          type="button"
          onClick={onOpen}
          disabled={listings.length < 2}
          className="rounded-md bg-series-1 px-4 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-45"
        >
          {listings.length < 2 ? "Дахин 1 сонгох" : "Харьцуулах"}
        </button>
      </div>

      {open && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-black/45 p-4" onClick={onClose}>
          <div className="mx-auto my-8 max-w-6xl rounded-xl bg-surface-card p-5 shadow-xl" onClick={(event) => event.stopPropagation()}>
            <div className="mb-5 flex items-start justify-between gap-4">
              <div>
                <h2 className="text-lg font-semibold text-ink-primary">Зар харьцуулах</h2>
                <p className="mt-1 text-xs text-ink-muted">Нэг мөрөнд ижил хэмжүүрүүдийг зэрэгцүүлэв.</p>
              </div>
              <button type="button" onClick={onClose} aria-label="Хаах" className="text-ink-muted hover:text-ink-primary"><X className="h-5 w-5" /></button>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] table-fixed border-collapse text-sm">
                <thead>
                  <tr>
                    <th className="w-44 border-b border-line-grid p-3 text-left text-xs font-medium text-ink-muted">Үзүүлэлт</th>
                    {listings.map((listing) => (
                      <th key={listing.id} className="border-b border-line-grid p-3 text-left align-top">
                        <div className="flex items-start justify-between gap-2">
                          <span className="line-clamp-2 font-semibold text-ink-primary">{listing.title}</span>
                          <button type="button" onClick={() => onRemove(listing.id)} aria-label="Харьцуулалтаас хасах" className="shrink-0 text-ink-muted hover:text-ink-primary"><X className="h-4 w-4" /></button>
                        </div>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  <CompareRow label="Үнэ" listings={listings} render={(row) => formatListingPrice(row).text} />
                  <CompareRow label="Үнэ / мкв" listings={listings} render={(row) => row.price_per_sqm === null ? "—" : formatMnt(row.price_per_sqm)} />
                  <CompareRow label="Талбай" listings={listings} render={(row) => row.area_sqm === null ? "—" : `${row.area_sqm} мкв`} />
                  <CompareRow label="Өрөө · давхар" listings={listings} render={(row) => `${row.rooms ?? "—"} өрөө · ${row.floor ?? "—"}/${row.total_floors ?? "—"}`} />
                  <CompareRow label="Дүүрэг" listings={listings} render={(row) => row.district ?? "—"} />
                  <CompareRow label="Хотхон" listings={listings} render={(row) => row.complex_name ?? "—"} />
                  <CompareRow label="Дүүргээс хямд" listings={listings} render={(row) => row.deal_pct === null ? "—" : formatPercent(row.deal_pct)} />
                  <CompareRow label="Хотхоноос хямд" listings={listings} render={(row) => row.complex_deal_pct === null ? "—" : formatPercent(row.complex_deal_pct)} />
                  <CompareRow label="Gross rental yield" listings={listings} render={(row) => row.rental_yield_pct === null ? "—" : formatPercent(row.rental_yield_pct)} />
                  <CompareRow label="Үзэлт" listings={listings} render={(row) => row.view_count == null ? "—" : row.view_count.toLocaleString("mn-MN")} />
                  <tr>
                    <th className="border-t border-line-grid p-3 text-left text-xs font-medium text-ink-muted">Эх сурвалж</th>
                    {listings.map((listing) => (
                      <td key={listing.id} className="border-t border-line-grid p-3">
                        <a href={listing.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-series-1 hover:underline">Зар харах <ExternalLink className="h-3.5 w-3.5" /></a>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function CompareRow({ label, listings, render }: { label: string; listings: Listing[]; render: (listing: Listing) => string }) {
  return (
    <tr className="odd:bg-surface-page/60">
      <th className="p-3 text-left text-xs font-medium text-ink-muted">{label}</th>
      {listings.map((listing) => <td key={listing.id} className="p-3 tabular-nums text-ink-primary">{render(listing)}</td>)}
    </tr>
  );
}
