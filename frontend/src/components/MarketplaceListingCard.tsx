import {
  Building2,
  Eye,
  ImageIcon,
  MapPin,
  Ruler,
} from "lucide-react";
import Link from "next/link";

import type { Listing } from "@/lib/api";
import { formatListingPrice, formatMnt, timeAgo } from "@/lib/format";
import { VerifiedComplexBadge } from "./VerifiedComplexBadge";

function categoryLabel(value: string | null): string | null {
  if (!value) return null;
  return value.replace(/ түрээслүүлнэ$/u, "").replace(/ зарна$/u, "");
}

function locationLabel(listing: Listing): string {
  const parts = [listing.district, listing.address].filter(
    (value, index, values): value is string =>
      Boolean(value) && values.indexOf(value) === index,
  );
  return parts.length > 0 ? parts.join(" · ") : "Байршил тодорхойгүй";
}

export function MarketplaceListingCard({ listing }: { listing: Listing }) {
  const price = formatListingPrice(listing);
  const isRent = listing.listing_type === "rent";
  const isSale = listing.listing_type === "sale";
  const transactionLabel = isRent
    ? "ТҮРЭЭСЛҮҮЛНЭ"
    : isSale
      ? "ЗАРНА"
      : "ТӨРӨЛ ТОДОРХОЙГҮЙ";
  const propertyLabel = categoryLabel(listing.property_type);
  const photoCount = listing.photo_urls.length;
  const specs = [
    listing.rooms ? `${listing.rooms} өрөө` : null,
    listing.area_sqm ? `${listing.area_sqm} м²` : null,
    listing.floor
      ? `${listing.floor}${listing.total_floors ? `/${listing.total_floors}` : ""} давхар`
      : null,
  ].filter(Boolean);

  return (
    <article className="group relative flex h-full flex-col overflow-hidden rounded-lg border border-slate-200 bg-white shadow-[0_1px_2px_rgba(15,23,42,0.04)] transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-lg">
      <Link
        href={`/listings/${listing.id}`}
        className="flex h-full flex-col"
        aria-label={`${listing.title} — эх зарыг нээх`}
      >
        <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
          {listing.photo_urls[0] ? (
            // eslint-disable-next-line @next/next/no-img-element -- source CDN domains vary by listing
            <img
              src={listing.photo_urls[0]}
              alt={listing.title}
              loading="lazy"
              className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.035]"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-400">
              <ImageIcon className="h-7 w-7" aria-hidden />
              Зураггүй
            </div>
          )}

          <span
            className={`absolute left-2.5 top-2.5 rounded px-2 py-1 text-[10px] font-black tracking-wide text-white shadow-sm ${
              isRent ? "bg-[#2677d8]" : isSale ? "bg-[#ff6b35]" : "bg-slate-600"
            }`}
          >
            {transactionLabel}
          </span>
          {photoCount > 0 && (
            <span className="absolute bottom-2.5 right-2.5 flex items-center gap-1 rounded bg-black/70 px-2 py-1 text-[11px] font-bold text-white">
              <ImageIcon className="h-3.5 w-3.5" aria-hidden /> {photoCount}
            </span>
          )}
        </div>

        <div className="flex flex-1 flex-col p-3.5">
          {listing.complex_name && (
            <div className="mb-2 flex flex-wrap items-center gap-2 text-[11px] font-bold text-[#49627d]">
              <span>{listing.complex_name}</span>
              {listing.complex_verified && <VerifiedComplexBadge compact />}
            </div>
          )}
          <h2 className="line-clamp-2 min-h-10 text-[14px] font-bold leading-5 text-slate-800 transition group-hover:text-[#e85520]">
            {listing.title}
          </h2>

          <p className="mt-2 flex items-start gap-1 text-[11px] leading-4 text-slate-500">
            <MapPin className="mt-px h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />
            <span className="line-clamp-1">{locationLabel(listing)}</span>
          </p>

          <div className="mt-3 flex min-h-6 flex-wrap items-center gap-1.5 text-[11px] font-semibold text-slate-600">
            {listing.rooms && <span className="rounded bg-slate-100 px-2 py-1"><Building2 className="mr-1 inline h-3 w-3 text-slate-400" />{listing.rooms} өрөө</span>}
            {listing.area_sqm && <span className="rounded bg-slate-100 px-2 py-1"><Ruler className="mr-1 inline h-3 w-3 text-slate-400" />{listing.area_sqm} м²</span>}
            {listing.floor && <span className="rounded bg-slate-100 px-2 py-1">{listing.floor}{listing.total_floors ? `/${listing.total_floors}` : ""} давхар</span>}
            {specs.length === 0 && propertyLabel && <span className="rounded bg-slate-100 px-2 py-1">{propertyLabel}</span>}
          </div>

          <div className="mt-3 border-t border-slate-100 pt-3">
            <p className={`leading-tight ${
                price.isEstimate
                  ? "text-sm font-semibold italic text-slate-600"
                  : "text-lg font-black text-slate-950"
              }`}
            >
              {price.text}
            </p>
            <p className="mt-1 min-h-4 text-[11px] font-medium text-slate-500">
              {listing.price_per_sqm !== null && !listing.price_negotiable
                ? `${formatMnt(listing.price_per_sqm)} / м²`
                : "м² үнэ тодорхойгүй"}
            </p>
          </div>

          <div className="mt-auto flex items-center justify-between gap-3 pt-3 text-[10px] text-slate-500">
            <div className="min-w-0">
              {propertyLabel && <p className="truncate font-medium text-slate-600">{propertyLabel}</p>}
              <p title={`Шинэчлэгдсэн: ${new Date(listing.scraped_at).toLocaleString("mn-MN")}`}>
                {timeAgo(listing.scraped_at)}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              {listing.view_count !== null && (
                <span className="flex items-center gap-1" title="Эх зарын үзэлт">
                  <Eye className="h-3.5 w-3.5" aria-hidden />
                  {listing.view_count.toLocaleString("mn-MN")}
                </span>
              )}
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
}
