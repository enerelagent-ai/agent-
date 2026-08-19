import { ExternalLink, Landmark } from "lucide-react";
import Link from "next/link";

import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { ComplexReviewActions } from "@/components/ComplexReviewActions";
import { getComplexReviewQueue } from "@/lib/api";

const PAGE_SIZE = 50;

export default async function ComplexReviewPage({
  searchParams,
}: {
  searchParams: { relation?: string; offset?: string };
}) {
  const relation = ["unit", "landmark", "unknown"].includes(searchParams.relation ?? "")
    ? searchParams.relation as "unit" | "landmark" | "unknown"
    : undefined;
  const parsedOffset = Number(searchParams.offset ?? 0);
  const offset = Number.isInteger(parsedOffset) && parsedOffset >= 0 ? parsedOffset : 0;
  const queue = await getComplexReviewQueue({ relation, offset, limit: PAGE_SIZE });
  const previous = Math.max(0, offset - PAGE_SIZE);
  const next = offset + PAGE_SIZE;

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title="Хотхоны баталгаажуулалтын дараалал" />
        <main className="space-y-5 bg-surface-page p-8">
          <section className="grid gap-4 sm:grid-cols-3">
            <Stat label="Нийт pending" value={queue.pending_unit + queue.pending_landmark} />
            <Stat label="Registry шаардлагатай unit" value={queue.pending_unit} />
            <Stat label="Landmark шалгах" value={queue.pending_landmark} />
          </section>

          <section className="rounded-xl border border-line-grid bg-surface-card p-5">
            <div className="flex flex-wrap items-start justify-between gap-4">
              <div>
                <h2 className="font-semibold text-ink-primary">Evidence queue</h2>
                <p className="mt-1 text-xs text-ink-muted">
                  Approve нь зөвхөн registry болон district guard давсан unit-д нээлттэй. Reject хийхэд legacy хотхоны холбоос audit trail-тай сална.
                </p>
              </div>
              <div className="flex gap-2 text-xs font-semibold">
                <FilterLink label="Бүгд" relation={undefined} active={!relation} />
                <FilterLink label="Unit" relation="unit" active={relation === "unit"} />
                <FilterLink label="Landmark" relation="landmark" active={relation === "landmark"} />
              </div>
            </div>

            <div className="mt-5 overflow-x-auto">
              <table className="w-full min-w-[900px] text-left text-sm">
                <thead className="border-b border-line-grid text-xs text-ink-secondary">
                  <tr>
                    <th className="pb-2 pr-4 font-medium">Хотхон / relation</th>
                    <th className="pb-2 pr-4 font-medium">Evidence</th>
                    <th className="pb-2 pr-4 font-medium">Байршил</th>
                    <th className="pb-2 pr-4 font-medium">Confidence</th>
                    <th className="pb-2 font-medium">Эх зар</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-line-grid">
                  {queue.items.map((item) => (
                    <tr key={item.listing_id}>
                      <td className="py-3 pr-4 align-top">
                        <div className="font-medium text-ink-primary">{item.complex_name}</div>
                        <span className={`mt-1 inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${item.relation === "landmark" ? "bg-amber-50 text-amber-700" : "bg-slate-100 text-slate-600"}`}>
                          {item.relation === "landmark" && <Landmark className="h-3 w-3" aria-hidden />}
                          {item.relation}
                        </span>
                      </td>
                      <td className="max-w-xl py-3 pr-4 align-top">
                        <p className="line-clamp-2 text-ink-primary">{item.evidence_text}</p>
                        <p className="mt-1 text-xs text-ink-muted">alias: {item.matched_alias ?? "—"} · {item.review_reason ?? "manual_review"}</p>
                      </td>
                      <td className="py-3 pr-4 align-top text-ink-secondary">
                        {item.district ?? "—"}
                        {item.address && <div className="mt-1 max-w-52 truncate text-xs text-ink-muted">{item.address}</div>}
                      </td>
                      <td className="py-3 pr-4 align-top tabular-nums text-ink-secondary">{Math.round(item.confidence * 100)}%</td>
                      <td className="py-3 align-top">
                        <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-xs font-semibold text-series-1 hover:underline">
                          #{item.listing_id} <ExternalLink className="h-3.5 w-3.5" aria-hidden />
                        </a>
                        <ComplexReviewActions
                          listingId={item.listing_id}
                          canApprove={item.can_approve}
                          blockReason={item.approval_block_reason}
                        />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {queue.items.length === 0 && (
                <div className="py-12 text-center text-sm text-ink-muted">Энэ шүүлтүүрт pending мөр алга.</div>
              )}
            </div>

            <div className="mt-5 flex items-center justify-between border-t border-line-grid pt-4 text-sm">
              <span className="text-ink-muted">{queue.total} мөрөөс {queue.items.length} харагдаж байна</span>
              <div className="flex gap-2">
                <PageLink label="Өмнөх" offset={previous} relation={relation} disabled={offset === 0} />
                <PageLink label="Дараах" offset={next} relation={relation} disabled={next >= queue.total} />
              </div>
            </div>
          </section>
        </main>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number }) {
  return <div className="rounded-xl border border-line-grid bg-surface-card p-5"><div className="text-xs text-ink-muted">{label}</div><div className="mt-2 text-2xl font-semibold text-ink-primary">{value.toLocaleString("mn-MN")}</div></div>;
}

function FilterLink({ label, relation, active }: { label: string; relation?: string; active: boolean }) {
  const href = relation ? `/complex-review?relation=${relation}` : "/complex-review";
  return <Link href={href} className={`rounded-full px-3 py-1.5 ${active ? "bg-[#111a3d] text-white" : "bg-surface-page text-ink-secondary"}`}>{label}</Link>;
}

function PageLink({ label, offset, relation, disabled }: { label: string; offset: number; relation?: string; disabled: boolean }) {
  if (disabled) return <span className="rounded-md border border-line-grid px-3 py-1.5 text-ink-muted opacity-40">{label}</span>;
  const params = new URLSearchParams({ offset: String(offset) });
  if (relation) params.set("relation", relation);
  return <Link href={`/complex-review?${params}`} className="rounded-md border border-line-grid px-3 py-1.5 text-ink-secondary hover:bg-surface-page">{label}</Link>;
}
