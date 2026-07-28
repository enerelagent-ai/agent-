import type { Listing } from "@/lib/api";
import { formatMnt } from "@/lib/format";

function timeAgo(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "саяхан";
  if (diffHours < 24) return `${diffHours} цагийн өмнө`;
  return `${Math.floor(diffHours / 24)} өдрийн өмнө`;
}

export function RecentListings({ listings }: { listings: Listing[] }) {
  return (
    <div className="rounded-xl border border-line-grid bg-surface-card p-5">
      <h2 className="mb-4 text-base font-semibold text-ink-primary">Шинэ зар мэдээлэл</h2>
      <ul className="flex flex-col divide-y divide-line-grid">
        {listings.map((listing) => (
          <li key={listing.id} className="flex gap-3 py-3 first:pt-0 last:pb-0">
            <div className="h-16 w-20 shrink-0 overflow-hidden rounded-lg bg-surface-page">
              {listing.photo_urls[0] && (
                // eslint-disable-next-line @next/next/no-img-element -- external CDN images, no next.config.js domain allowlist yet
                <img src={listing.photo_urls[0]} alt="" className="h-full w-full object-cover" />
              )}
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-start justify-between gap-2">
                <p className="truncate text-sm font-medium text-ink-primary">{listing.title}</p>
                <span className="shrink-0 text-sm font-semibold text-ink-primary">
                  {listing.price !== null ? formatMnt(listing.price) : "—"}
                </span>
              </div>
              <p className="truncate text-xs text-ink-secondary">
                {listing.district ?? "Байршил тодорхойгүй"}
                {listing.rooms ? ` · ${listing.rooms} өрөө` : ""}
                {listing.area_sqm ? ` · ${listing.area_sqm} мкв` : ""}
              </p>
              <p className="text-xs text-ink-muted">{timeAgo(listing.scraped_at)}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
