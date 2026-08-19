import {
  ArrowLeft,
  Building2,
  ExternalLink,
  Eye,
  MapPin,
  Phone,
  Ruler,
} from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ApiError, getListing, type Listing } from "@/lib/api";
import { formatListingPrice, formatMnt, timeAgo } from "@/lib/format";
import { VerifiedComplexBadge } from "@/components/VerifiedComplexBadge";

function categoryLabel(value: string | null): string {
  if (!value) return "Төрөл тодорхойгүй";
  return value.replace(/ түрээслүүлнэ$/u, "").replace(/ зарна$/u, "");
}

function DetailRow({ label, value }: { label: string; value: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-start justify-between gap-5 border-b border-slate-100 py-3 last:border-0">
      <dt className="text-sm text-slate-500">{label}</dt>
      <dd className="text-right text-sm font-semibold text-slate-800">{value}</dd>
    </div>
  );
}

function PhotoGallery({ listing }: { listing: Listing }) {
  const photos = listing.photo_urls.filter(Boolean).slice(0, 5);
  if (photos.length === 0) {
    return (
      <div className="flex aspect-[16/7] items-center justify-center rounded-xl bg-slate-100 text-slate-400">
        Зураг оруулаагүй
      </div>
    );
  }

  return (
    <div className="grid overflow-hidden rounded-xl bg-slate-200 sm:h-[470px] sm:grid-cols-2 sm:gap-1">
      <div className={photos.length === 1 ? "sm:col-span-2" : ""}>
        {/* eslint-disable-next-line @next/next/no-img-element -- source CDN domains vary */}
        <img src={photos[0]} alt={listing.title} className="h-full min-h-72 w-full object-cover" />
      </div>
      {photos.length > 1 && (
        <div className="hidden grid-cols-2 gap-1 sm:grid">
          {photos.slice(1).map((photo, index) => (
            <div key={photo} className="relative overflow-hidden">
              {/* eslint-disable-next-line @next/next/no-img-element -- source CDN domains vary */}
              <img src={photo} alt={`${listing.title} — зураг ${index + 2}`} className="h-full w-full object-cover" />
              {index === 3 && listing.photo_urls.length > 5 && (
                <span className="absolute inset-0 flex items-center justify-center bg-black/55 text-lg font-bold text-white">
                  +{listing.photo_urls.length - 5} зураг
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default async function ListingDetailPage({ params }: { params: { id: string } }) {
  const listingId = Number(params.id);
  if (!Number.isInteger(listingId) || listingId < 1) notFound();

  let listing: Listing;
  try {
    listing = await getListing(listingId);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) notFound();
    throw error;
  }

  const price = formatListingPrice(listing);
  const isRent = listing.listing_type === "rent";
  const backHref = isRent ? "/rent" : "/sale";
  const location = [listing.district, listing.address]
    .filter((value, index, values) => value && values.indexOf(value) === index)
    .join(" · ");

  return (
    <div className="min-h-screen bg-[#f5f5f5] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1240px] items-center justify-between px-5 py-4 lg:px-8">
          <Link href="/sale" className="text-xl font-black tracking-tight text-[#e53935]">Enerel Market</Link>
          <Link href={backHref} className="flex items-center gap-1.5 text-sm font-semibold text-slate-600 hover:text-slate-900">
            <ArrowLeft className="h-4 w-4" aria-hidden /> Зарын жагсаалт
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-[1240px] px-5 py-6 lg:px-8">
        <nav className="mb-4 flex flex-wrap items-center gap-2 text-xs text-slate-500" aria-label="Breadcrumb">
          <Link href={backHref} className="hover:text-[#d92d2d]">{isRent ? "Түрээслэх" : "Худалдах"}</Link>
          <span>/</span>
          <span>{categoryLabel(listing.property_type)}</span>
          <span>/</span>
          <span>Зар №{listing.id}</span>
        </nav>

        <PhotoGallery listing={listing} />

        <div className="mt-6 grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="space-y-6">
            <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-md px-2.5 py-1 text-xs font-extrabold text-white ${isRent ? "bg-blue-600" : "bg-[#e53935]"}`}>
                  {isRent ? "ТҮРЭЭСЛҮҮЛНЭ" : "ЗАРНА"}
                </span>
                <span className="text-xs font-medium text-slate-500">{categoryLabel(listing.property_type)}</span>
              </div>
              <h1 className="mt-3 text-2xl font-bold leading-tight text-slate-950 sm:text-3xl">{listing.title}</h1>
              <p className="mt-3 flex items-start gap-2 text-sm text-slate-600">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-[#e53935]" aria-hidden />
                {location || "Байршил тодорхойгүй"}
              </p>
              <div className="mt-5 flex flex-wrap gap-x-6 gap-y-3 border-y border-slate-100 py-4 text-sm font-semibold text-slate-700">
                {listing.rooms && <span className="flex items-center gap-1.5"><Building2 className="h-4 w-4 text-slate-400" aria-hidden />{listing.rooms} өрөө</span>}
                {listing.area_sqm && <span className="flex items-center gap-1.5"><Ruler className="h-4 w-4 text-slate-400" aria-hidden />{listing.area_sqm} м²</span>}
                {listing.floor && <span>{listing.floor}{listing.total_floors ? `/${listing.total_floors}` : ""} давхар</span>}
                {listing.view_count !== null && <span className="flex items-center gap-1.5"><Eye className="h-4 w-4 text-slate-400" aria-hidden />{listing.view_count.toLocaleString("mn-MN")} үзэлт</span>}
              </div>
              <p className="mt-4 text-xs text-slate-500">Шинэчлэгдсэн {timeAgo(listing.scraped_at)} · Зар №{listing.id}</p>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
              <h2 className="text-lg font-bold">Үндсэн мэдээлэл</h2>
              <dl className="mt-3 grid sm:grid-cols-2 sm:gap-x-8">
                <DetailRow label="Үл хөдлөхийн төрөл" value={categoryLabel(listing.property_type)} />
                <DetailRow label="Өрөө" value={listing.rooms ? `${listing.rooms}` : null} />
                <DetailRow label="Талбай" value={listing.area_sqm ? `${listing.area_sqm} м²` : null} />
                <DetailRow label="Давхар" value={listing.floor ? `${listing.floor}${listing.total_floors ? ` / ${listing.total_floors}` : ""}` : null} />
                {listing.complex_name && (
                  <div className="flex items-center justify-between gap-5 border-b border-slate-100 py-3">
                    <dt className="text-sm text-slate-500">Хотхон</dt>
                    <dd className="flex flex-wrap items-center justify-end gap-2 text-right text-sm font-semibold text-slate-800">
                      {listing.complex_name}
                      {listing.complex_verified && <VerifiedComplexBadge compact />}
                    </dd>
                  </div>
                )}
                <DetailRow label="Дүүрэг" value={listing.district} />
              </dl>
            </section>

            <section className="rounded-xl border border-slate-200 bg-white p-5 sm:p-6">
              <h2 className="text-lg font-bold">Зарын тайлбар</h2>
              <p className="mt-4 whitespace-pre-line text-sm leading-7 text-slate-700">
                {listing.description?.trim() || "Энэ зарт дэлгэрэнгүй тайлбар оруулаагүй байна."}
              </p>
            </section>
          </div>

          <aside className="space-y-4 lg:sticky lg:top-5">
            <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
              <p className={`leading-tight ${price.isEstimate ? "text-base font-semibold italic text-slate-600" : "text-3xl font-black text-slate-950"}`}>{price.text}</p>
              {listing.price_per_sqm !== null && !listing.price_negotiable && <p className="mt-2 text-sm font-medium text-slate-500">{formatMnt(listing.price_per_sqm)} / м²</p>}
              <a href={listing.source_url} target="_blank" rel="noopener noreferrer" className="mt-5 flex w-full items-center justify-center gap-2 rounded-lg bg-[#e53935] px-4 py-3 text-sm font-bold text-white hover:bg-[#cf2f2f]">
                Эх зар дээр харах <ExternalLink className="h-4 w-4" aria-hidden />
              </a>
              {listing.contact_phone && (
                <a href={`tel:${listing.contact_phone}`} className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-slate-300 px-4 py-3 text-sm font-bold text-slate-800 hover:bg-slate-50">
                  <Phone className="h-4 w-4" aria-hidden /> {listing.contact_phone}
                </a>
              )}
              <p className="mt-3 text-xs leading-5 text-slate-400">Үнэ болон зарын төлөв өөрчлөгдсөн байж болно. Эх сурвалж дээр давхар шалгана уу.</p>
            </section>

            {(listing.lat !== null || listing.lng !== null) && (
              <section className="rounded-xl border border-slate-200 bg-white p-5">
                <h2 className="font-bold">Байршил</h2>
                <p className="mt-2 text-sm text-slate-600">{location || "Координат бүртгэгдсэн"}</p>
                {listing.lat !== null && listing.lng !== null && (
                  <a href={`https://www.google.com/maps?q=${listing.lat},${listing.lng}`} target="_blank" rel="noopener noreferrer" className="mt-3 inline-flex items-center gap-1 text-sm font-semibold text-[#d92d2d] hover:underline">Газрын зураг дээр нээх <ExternalLink className="h-4 w-4" aria-hidden /></a>
                )}
              </section>
            )}
          </aside>
        </div>
      </main>
    </div>
  );
}
