import {
  Building2,
  ChevronRight,
  Eye,
  ImageIcon,
  MapPin,
  Ruler,
} from "lucide-react";
import Link from "next/link";

import type { Listing } from "@/lib/api";
import { formatListingPrice, formatMnt, timeAgo } from "@/lib/format";

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
    <article className="group flex h-full flex-col overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md">
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
              className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.025]"
            />
          ) : (
            <div className="flex h-full flex-col items-center justify-center gap-2 text-sm text-slate-400">
              <ImageIcon className="h-7 w-7" aria-hidden />
              Зураггүй
            </div>
          )}

          <span
            className={`absolute left-3 top-3 rounded-md px-2.5 py-1 text-[11px] font-extrabold tracking-wide text-white shadow-sm ${
              isRent ? "bg-blue-600" : isSale ? "bg-[#e53935]" : "bg-slate-600"
            }`}
          >
            {transactionLabel}
          </span>
          {photoCount > 0 && (
            <span className="absolute bottom-3 right-3 flex items-center gap-1 rounded-md bg-black/65 px-2 py-1 text-xs font-medium text-white">
              <ImageIcon className="h-3.5 w-3.5" aria-hidden /> {photoCount}
            </span>
          )}
        </div>

        <div className="flex flex-1 flex-col p-4">
          <div>
            <p
              className={`leading-tight ${
                price.isEstimate
                  ? "text-sm font-semibold italic text-slate-600"
                  : "text-xl font-extrabold text-slate-950"
              }`}
            >
              {price.text}
            </p>
            <p className="mt-1 min-h-4 text-xs font-medium text-slate-500">
              {listing.price_per_sqm !== null && !listing.price_negotiable
                ? `${formatMnt(listing.price_per_sqm)} / м²`
                : "м² үнэ тодорхойгүй"}
            </p>
          </div>

          <h2 className="mt-3 line-clamp-2 min-h-10 text-sm font-bold leading-5 text-slate-800 group-hover:text-[#c92b2b]">
            {listing.title}
          </h2>

          <p className="mt-2 flex items-start gap-1.5 text-xs leading-5 text-slate-500">
            <MapPin className="mt-0.5 h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden />
            <span className="line-clamp-2">{locationLabel(listing)}</span>
          </p>

          <div className="mt-3 flex min-h-6 flex-wrap items-center gap-x-3 gap-y-1 text-xs font-medium text-slate-600">
            {listing.rooms && (
              <span className="flex items-center gap-1">
                <Building2 className="h-3.5 w-3.5 text-slate-400" aria-hidden />
                {listing.rooms} өрөө
              </span>
            )}
            {listing.area_sqm && (
              <span className="flex items-center gap-1">
                <Ruler className="h-3.5 w-3.5 text-slate-400" aria-hidden />
                {listing.area_sqm} м²
              </span>
            )}
            {listing.floor && (
              <span>{listing.floor}{listing.total_floors ? `/${listing.total_floors}` : ""} давхар</span>
            )}
            {specs.length === 0 && propertyLabel && <span>{propertyLabel}</span>}
          </div>

          <div className="mt-auto flex items-center justify-between gap-3 border-t border-slate-100 pt-3 text-xs text-slate-500">
            <div className="min-w-0">
              {propertyLabel && <p className="truncate font-medium text-slate-600">{propertyLabel}</p>}
              <p title={`Шинэчлэгдсэн: ${new Date(listing.scraped_at).toLocaleString("mn-MN")}`}>
                Шинэчлэгдсэн {timeAgo(listing.scraped_at)}
              </p>
            </div>
            <div className="flex shrink-0 items-center gap-3">
              {listing.view_count !== null && (
                <span className="flex items-center gap-1" title="Эх зарын үзэлт">
                  <Eye className="h-3.5 w-3.5" aria-hidden />
                  {listing.view_count.toLocaleString("mn-MN")}
                </span>
              )}
              <ChevronRight className="h-4 w-4 text-[#d92d2d]" aria-hidden />
            </div>
          </div>
        </div>
      </Link>
    </article>
  );
}
