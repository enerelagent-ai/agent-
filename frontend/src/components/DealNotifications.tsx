"use client";

import { useState } from "react";
import { CheckCheck, ExternalLink } from "lucide-react";
import { formatMnt, formatPercent, timeAgo } from "@/lib/format";
import { markDealAlertsSeen, type DealAlertFeed } from "@/lib/api";

export function DealNotifications({ initialFeed }: { initialFeed: DealAlertFeed }) {
  const [feed, setFeed] = useState(initialFeed);
  const [saving, setSaving] = useState(false);

  async function markSeen() {
    setSaving(true);
    try {
      const state = await markDealAlertsSeen();
      setFeed((current) => ({ ...current, unseen_count: 0, last_seen_at: state.last_seen_at }));
      window.dispatchEvent(new Event("deal-alerts-seen"));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-xl border border-line-grid bg-surface-card p-5">
      <div className="mb-5 flex items-start justify-between gap-4">
        <div>
          <h2 className="font-semibold text-ink-primary">Итгэлтэй хямд боломжууд</h2>
          <p className="mt-1 text-xs leading-relaxed text-ink-muted">
            Одоогоор top_deal ангилалд байгаа зарууд. Шинэ гэдэг нь хамгийн сүүлд мэдэгдлээ үзсэнээс хойш scrape хийгдсэнийг хэлнэ.
          </p>
        </div>
        <button
          type="button"
          onClick={markSeen}
          disabled={saving || feed.unseen_count === 0}
          className="flex shrink-0 items-center gap-1.5 rounded-md border border-line-grid px-3 py-2 text-sm text-ink-secondary disabled:opacity-40"
        >
          <CheckCheck className="h-4 w-4" aria-hidden />
          {saving ? "Хадгалж байна…" : "Бүгдийг үзсэн"}
        </button>
      </div>

      {feed.items.length === 0 ? (
        <p className="py-8 text-center text-sm text-ink-muted">Одоогоор итгэлтэй хямд боломж алга.</p>
      ) : (
        <ul className="divide-y divide-line-grid">
          {feed.items.map((item) => {
            const unseen = new Date(item.scraped_at) > new Date(feed.last_seen_at);
            return (
              <li key={item.id} className="flex items-start gap-3 py-4 first:pt-0 last:pb-0">
                <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${unseen ? "bg-series-1" : "bg-line-axis"}`} aria-label={unseen ? "Шинэ" : "Үзсэн"} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-start justify-between gap-2">
                    <p className="font-medium text-ink-primary">{item.title}</p>
                    <span className="font-semibold text-ink-primary">{item.price === null ? "—" : formatMnt(item.price)}</span>
                  </div>
                  <p className="mt-1 text-xs text-ink-secondary">
                    {item.complex_name ? `${item.complex_name} · ` : ""}{item.district ?? "Байршил тодорхойгүй"}
                  </p>
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <span className="rounded-full bg-[#0ca30c]/10 px-2 py-0.5 text-xs font-medium text-[#0ca30c]">Дүүргээс ↓ {formatPercent(item.deal_pct)}</span>
                    <span className="text-xs text-ink-muted">{timeAgo(item.scraped_at)}</span>
                    <a href={item.source_url} target="_blank" rel="noopener noreferrer" className="ml-auto flex items-center gap-1 text-xs text-series-1 hover:underline">Зар харах <ExternalLink className="h-3.5 w-3.5" /></a>
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
