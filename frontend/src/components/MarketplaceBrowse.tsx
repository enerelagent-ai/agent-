"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight, MapPin, Search, SlidersHorizontal } from "lucide-react";
import { useState } from "react";

import {
  searchMarketplaceListings,
  type ListingFacets,
  type MarketplaceListingPage,
  type TransactionType,
} from "@/lib/api";
import { formatListingPrice, formatMnt, timeAgo } from "@/lib/format";

const PAGE_SIZE = 24;

function categoryLabel(value: string): string {
  return value
    .replace(/ түрээслүүлнэ$/u, "")
    .replace(/ зарна$/u, "");
}

export function MarketplaceBrowse({
  listingType,
  facets,
  initialPage,
}: {
  listingType: TransactionType;
  facets: ListingFacets;
  initialPage: MarketplaceListingPage;
}) {
  const [page, setPage] = useState(initialPage);
  const [district, setDistrict] = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [rooms, setRooms] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [cursor, setCursor] = useState<string | undefined>();
  const [cursorHistory, setCursorHistory] = useState<Array<string | undefined>>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const transactionLabel = listingType === "sale" ? "Зарна" : "Түрээслүүлнэ";

  async function load(nextCursor?: string, nextHistory = cursorHistory) {
    setLoading(true);
    setError(null);
    try {
      const result = await searchMarketplaceListings({
        listingType,
        district: district || undefined,
        propertyType: propertyType || undefined,
        rooms: rooms ? Number(rooms) : undefined,
        minPrice: minPrice ? Number(minPrice) : undefined,
        maxPrice: maxPrice ? Number(maxPrice) : undefined,
        cursor: nextCursor,
        limit: PAGE_SIZE,
      });
      setPage(result);
      setCursor(nextCursor);
      setCursorHistory(nextHistory);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch {
      setError("Зарын мэдээллийг ачаалж чадсангүй. Дахин оролдоно уу.");
    } finally {
      setLoading(false);
    }
  }

  function applyFilters() {
    void load(undefined, []);
  }

  function clearFilters() {
    setDistrict("");
    setPropertyType("");
    setRooms("");
    setMinPrice("");
    setMaxPrice("");
    setPage(initialPage);
    setCursor(undefined);
    setCursorHistory([]);
    setError(null);
  }

  function nextPage() {
    if (!page.next_cursor) return;
    void load(page.next_cursor, [...cursorHistory, cursor]);
  }

  function previousPage() {
    if (cursorHistory.length === 0) return;
    const previousCursor = cursorHistory[cursorHistory.length - 1];
    void load(previousCursor, cursorHistory.slice(0, -1));
  }

  return (
    <div className="min-h-screen bg-[#f5f5f5] text-slate-900">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-[1440px] items-center justify-between gap-6 px-5 py-4 lg:px-8">
          <Link href="/sale" className="text-xl font-black tracking-tight text-[#e53935]">
            Enerel Market
          </Link>
          <nav className="flex items-center gap-2 rounded-lg bg-slate-100 p-1 text-sm font-semibold">
            <Link
              href="/sale"
              className={`rounded-md px-4 py-2 ${listingType === "sale" ? "bg-white text-[#d92d2d] shadow-sm" : "text-slate-600"}`}
            >
              Худалдах
            </Link>
            <Link
              href="/rent"
              className={`rounded-md px-4 py-2 ${listingType === "rent" ? "bg-white text-[#d92d2d] shadow-sm" : "text-slate-600"}`}
            >
              Түрээслэх
            </Link>
          </nav>
          <Link href="/" className="hidden text-sm font-medium text-slate-600 hover:text-slate-900 sm:block">
            Хөрөнгө оруулалтын самбар
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-[1440px] px-5 py-6 lg:px-8">
        <div className="mb-5">
          <p className="text-sm font-medium text-[#d92d2d]">Үл хөдлөх хөрөнгө</p>
          <h1 className="mt-1 text-2xl font-bold sm:text-3xl">{transactionLabel} зарууд</h1>
          <p className="mt-1 text-sm text-slate-500">
            {facets.total.toLocaleString("mn-MN")} идэвхтэй зар
          </p>
        </div>

        <div className="grid items-start gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="rounded-xl border border-slate-200 bg-white p-5 lg:sticky lg:top-5">
            <div className="mb-5 flex items-center gap-2 border-b border-slate-100 pb-4">
              <SlidersHorizontal className="h-5 w-5 text-[#d92d2d]" aria-hidden />
              <h2 className="font-bold">Зар шүүх</h2>
            </div>

            <div className="space-y-4">
              <label className="block text-sm font-medium text-slate-700">
                Дүүрэг
                <select value={district} onChange={(event) => setDistrict(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm">
                  <option value="">Бүх дүүрэг</option>
                  {facets.districts.map((item) => <option key={item.value} value={item.value}>{item.value} ({item.count})</option>)}
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Үл хөдлөхийн төрөл
                <select value={propertyType} onChange={(event) => setPropertyType(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm">
                  <option value="">Бүх төрөл</option>
                  {facets.property_types.map((item) => <option key={item.value} value={item.value}>{categoryLabel(item.value)} ({item.count})</option>)}
                </select>
              </label>

              <label className="block text-sm font-medium text-slate-700">
                Өрөөний тоо
                <select value={rooms} onChange={(event) => setRooms(event.target.value)} className="mt-1.5 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm">
                  <option value="">Бүгд</option>
                  {facets.rooms.map((item) => <option key={item.value} value={item.value}>{item.value} өрөө ({item.count})</option>)}
                </select>
              </label>

              <div>
                <p className="text-sm font-medium text-slate-700">Үнэ</p>
                <div className="mt-1.5 grid grid-cols-2 gap-2">
                  <input aria-label="Доод үнэ" type="number" min="0" inputMode="numeric" value={minPrice} onChange={(event) => setMinPrice(event.target.value)} placeholder="Доод" className="min-w-0 rounded-lg border border-slate-300 px-3 py-2.5 text-sm" />
                  <input aria-label="Дээд үнэ" type="number" min="0" inputMode="numeric" value={maxPrice} onChange={(event) => setMaxPrice(event.target.value)} placeholder="Дээд" className="min-w-0 rounded-lg border border-slate-300 px-3 py-2.5 text-sm" />
                </div>
                {facets.price.min !== null && facets.price.max !== null && (
                  <p className="mt-1.5 text-xs text-slate-400">{formatMnt(facets.price.min)} – {formatMnt(facets.price.max)}</p>
                )}
              </div>

              <button type="button" onClick={applyFilters} disabled={loading} className="flex w-full items-center justify-center gap-2 rounded-lg bg-[#e53935] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#cf2f2f] disabled:opacity-60">
                <Search className="h-4 w-4" aria-hidden /> {loading ? "Хайж байна…" : "Хайх"}
              </button>
              <button type="button" onClick={clearFilters} disabled={loading} className="w-full text-sm font-medium text-slate-500 hover:text-slate-800 disabled:opacity-60">Цэвэрлэх</button>
            </div>
          </aside>

          <section aria-busy={loading}>
            {error && <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            {page.items.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-500">Энэ шүүлтээр зар олдсонгүй.</div>
            ) : (
              <div className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${loading ? "opacity-60" : ""}`}>
                {page.items.map((listing) => {
                  const price = formatListingPrice(listing);
                  return (
                    <a key={listing.id} href={listing.source_url} target="_blank" rel="noopener noreferrer" className="group overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md">
                      <div className="relative aspect-[4/3] bg-slate-100">
                        {listing.photo_urls[0] ? (
                          // eslint-disable-next-line @next/next/no-img-element -- source CDN domains vary by listing
                          <img src={listing.photo_urls[0]} alt="" className="h-full w-full object-cover transition duration-300 group-hover:scale-[1.02]" />
                        ) : <div className="flex h-full items-center justify-center text-sm text-slate-400">Зураггүй</div>}
                        <span className={`absolute left-3 top-3 rounded-md px-2 py-1 text-xs font-bold text-white ${listingType === "sale" ? "bg-[#e53935]" : "bg-blue-600"}`}>{transactionLabel.toUpperCase()}</span>
                      </div>
                      <div className="p-4">
                        <p className={`text-lg font-bold ${price.isEstimate ? "text-slate-600" : "text-slate-950"}`}>{price.text}</p>
                        {listing.price_per_sqm !== null && !listing.price_negotiable && <p className="mt-0.5 text-xs text-slate-500">{formatMnt(listing.price_per_sqm)} / м²</p>}
                        <h2 className="mt-2 line-clamp-2 min-h-10 text-sm font-semibold leading-5 text-slate-800">{listing.title}</h2>
                        <p className="mt-2 flex items-center gap-1 truncate text-xs text-slate-500"><MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden />{listing.district ?? listing.address ?? "Байршил тодорхойгүй"}</p>
                        <div className="mt-3 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500">
                          <span>{listing.rooms ? `${listing.rooms} өрөө` : categoryLabel(listing.property_type ?? "")}{listing.area_sqm ? ` · ${listing.area_sqm} м²` : ""}</span>
                          <span>{timeAgo(listing.scraped_at)}</span>
                        </div>
                      </div>
                    </a>
                  );
                })}
              </div>
            )}

            {(cursorHistory.length > 0 || page.has_more) && (
              <div className="mt-6 flex items-center justify-center gap-3">
                <button type="button" onClick={previousPage} disabled={loading || cursorHistory.length === 0} className="flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:opacity-40"><ChevronLeft className="h-4 w-4" aria-hidden /> Өмнөх</button>
                <span className="text-sm text-slate-500">{cursorHistory.length + 1}-р хуудас</span>
                <button type="button" onClick={nextPage} disabled={loading || !page.has_more} className="flex items-center gap-1 rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold disabled:opacity-40">Дараах <ChevronRight className="h-4 w-4" aria-hidden /></button>
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
