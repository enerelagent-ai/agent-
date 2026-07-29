"use client";

import { X, ExternalLink } from "lucide-react";
import type { Listing } from "@/lib/api";
import { formatListingPrice, formatMnt, formatPercent } from "@/lib/format";

interface ListingDetailModalProps {
  listing: Listing | null;
  onClose: () => void;
}

export function ListingDetailModal({ listing, onClose }: ListingDetailModalProps) {
  if (!listing) return null;

  const priceDisplay = formatListingPrice(listing);
  const hasGroupComparison = listing.group_median_price_per_sqm !== null && listing.price_per_sqm !== null;
  const hasYield = listing.rental_yield_pct !== null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onClick={onClose}
    >
      <div
        className="max-h-[85vh] w-full max-w-lg overflow-y-auto rounded-xl bg-surface-card p-5 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="text-base font-semibold text-ink-primary">{listing.title}</h2>
          <button
            type="button"
            onClick={onClose}
            aria-label="Хаах"
            className="shrink-0 text-ink-muted hover:text-ink-primary"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {listing.photo_urls[0] && (
          // eslint-disable-next-line @next/next/no-img-element -- external CDN images, no next.config.js domain allowlist yet
          <img
            src={listing.photo_urls[0]}
            alt=""
            className="mb-3 h-48 w-full rounded-lg object-cover bg-surface-page"
          />
        )}

        <p className="mb-1 text-xs text-ink-secondary">
          {listing.district ?? "Байршил тодорхойгүй"}
          {listing.rooms ? ` · ${listing.rooms} өрөө` : ""}
          {listing.area_sqm ? ` · ${listing.area_sqm} мкв` : ""}
          {listing.listing_type === "sale" ? " · Худалдах" : listing.listing_type === "rent" ? " · Түрээслэх" : ""}
        </p>

        <p className={`mb-4 text-lg font-semibold ${priceDisplay.isEstimate ? "italic text-ink-secondary" : "text-ink-primary"}`}>
          {priceDisplay.text}
        </p>

        <div className="mb-4 rounded-lg border border-line-grid p-3">
          <h3 className="mb-2 text-sm font-semibold text-ink-primary">Үнэ / мкв харьцуулалт</h3>
          {hasGroupComparison ? (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-ink-secondary">Энэ зарын үнэ / мкв</span>
                <span className="tabular-nums text-ink-primary">{formatMnt(listing.price_per_sqm as number)}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-ink-secondary">Ижил төрлийн зарын дундаж (медиан)</span>
                <span className="tabular-nums text-ink-primary">
                  {formatMnt(listing.group_median_price_per_sqm as number)}
                </span>
              </div>
              {listing.deal_pct !== null && (
                <div className="mt-2 flex items-center justify-between text-sm">
                  <span className="text-ink-secondary">Зөрүү</span>
                  <span
                    className={`font-medium ${listing.deal_pct >= 0 ? "text-[#0ca30c]" : "text-ink-primary"}`}
                  >
                    {listing.deal_pct >= 0 ? "↓" : "↑"} {formatPercent(Math.abs(listing.deal_pct))}
                    {listing.deal_pct >= 0 ? " хямд" : " өндөр"}
                  </span>
                </div>
              )}
              {listing.n_comparable !== null && (
                <p className="mt-2 text-xs text-ink-muted">
                  {listing.n_comparable} харьцуулах боломжтой зар дээр үндэслэв.
                </p>
              )}
              {listing.deal_status === "needs_review" && listing.deal_reason && (
                <p className="mt-2 rounded-md bg-[#fab219]/10 p-2 text-xs text-[#8a5a00]">
                  ⚠ {listing.deal_reason}
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-ink-muted">
              Энэ зарыг харьцуулах хангалттай тооны (дор хаяж 20) ижил төрлийн зар олдсонгүй.
            </p>
          )}
        </div>

        <div className="mb-4 rounded-lg border border-line-grid p-3">
          <h3 className="mb-2 text-sm font-semibold text-ink-primary">Түрээсийн өгөөж</h3>
          {hasYield ? (
            <>
              <div className="flex justify-between text-sm">
                <span className="text-ink-secondary">Тооцоолсон жилийн өгөөж</span>
                <span className="tabular-nums text-ink-primary">
                  {formatPercent(listing.rental_yield_pct as number)}
                </span>
              </div>
              {listing.rental_yield_payback_years !== null && (
                <div className="flex justify-between text-sm">
                  <span className="text-ink-secondary">Өртөг нөхөх хугацаа</span>
                  <span className="tabular-nums text-ink-primary">
                    ~{listing.rental_yield_payback_years} жил
                  </span>
                </div>
              )}
              {listing.rental_yield_n_sale !== null && listing.rental_yield_n_rent !== null && (
                <p className="mt-2 text-xs text-ink-muted">
                  {listing.rental_yield_n_sale} худалдах, {listing.rental_yield_n_rent} түрээслэх зар дээр
                  үндэслэв.
                </p>
              )}
            </>
          ) : (
            <p className="text-sm text-ink-muted">
              Энэ төрлийн байранд түрээсийн өгөөж тооцоолох боломжгүй.
            </p>
          )}
        </div>

        <a
          href={listing.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-center gap-1.5 rounded-md bg-series-1 px-4 py-2 text-sm font-medium text-white"
        >
          Эх сурвалж дээр харах <ExternalLink className="h-4 w-4" />
        </a>
      </div>
    </div>
  );
}
