"use client";

import Link from "next/link";
import { ChevronLeft, ChevronRight, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  searchMarketplaceListings,
  type ListingFacets,
  type MarketplaceListingPage,
  type TransactionType,
} from "@/lib/api";
import { formatMnt } from "@/lib/format";
import { MarketplaceListingCard } from "./MarketplaceListingCard";

const PAGE_SIZE = 24;

function categoryLabel(value: string): string {
  return value
    .replace(/ түрээслүүлнэ$/u, "")
    .replace(/ зарна$/u, "");
}

interface FilterControlsProps {
  facets: ListingFacets;
  district: string;
  propertyType: string;
  rooms: string;
  minPrice: string;
  maxPrice: string;
  loading: boolean;
  onDistrictChange: (value: string) => void;
  onPropertyTypeChange: (value: string) => void;
  onRoomsChange: (value: string) => void;
  onMinPriceChange: (value: string) => void;
  onMaxPriceChange: (value: string) => void;
  onApply: () => void;
  onClear: () => void;
}

function FilterControls({
  facets,
  district,
  propertyType,
  rooms,
  minPrice,
  maxPrice,
  loading,
  onDistrictChange,
  onPropertyTypeChange,
  onRoomsChange,
  onMinPriceChange,
  onMaxPriceChange,
  onApply,
  onClear,
}: FilterControlsProps) {
  return (
    <div className="space-y-4">
      <label className="block text-sm font-medium text-slate-700">
        Дүүрэг
        <select value={district} onChange={(event) => onDistrictChange(event.target.value)} className="mt-1.5 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base sm:text-sm">
          <option value="">Бүх дүүрэг</option>
          {facets.districts.map((item) => <option key={item.value} value={item.value}>{item.value} ({item.count})</option>)}
        </select>
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Үл хөдлөхийн төрөл
        <select value={propertyType} onChange={(event) => onPropertyTypeChange(event.target.value)} className="mt-1.5 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base sm:text-sm">
          <option value="">Бүх төрөл</option>
          {facets.property_types.map((item) => <option key={item.value} value={item.value}>{categoryLabel(item.value)} ({item.count})</option>)}
        </select>
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Өрөөний тоо
        <select value={rooms} onChange={(event) => onRoomsChange(event.target.value)} className="mt-1.5 min-h-11 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-base sm:text-sm">
          <option value="">Бүгд</option>
          {facets.rooms.map((item) => <option key={item.value} value={item.value}>{item.value} өрөө ({item.count})</option>)}
        </select>
      </label>

      <div>
        <p className="text-sm font-medium text-slate-700">Үнэ</p>
        <div className="mt-1.5 grid grid-cols-2 gap-2">
          <input aria-label="Доод үнэ" type="number" min="0" inputMode="numeric" value={minPrice} onChange={(event) => onMinPriceChange(event.target.value)} placeholder="Доод" className="min-h-11 min-w-0 rounded-lg border border-slate-300 px-3 py-2.5 text-base sm:text-sm" />
          <input aria-label="Дээд үнэ" type="number" min="0" inputMode="numeric" value={maxPrice} onChange={(event) => onMaxPriceChange(event.target.value)} placeholder="Дээд" className="min-h-11 min-w-0 rounded-lg border border-slate-300 px-3 py-2.5 text-base sm:text-sm" />
        </div>
        {facets.price.min !== null && facets.price.max !== null && (
          <p className="mt-1.5 text-xs text-slate-400">{formatMnt(facets.price.min)} – {formatMnt(facets.price.max)}</p>
        )}
      </div>

      <button type="button" onClick={onApply} disabled={loading} className="flex min-h-11 w-full items-center justify-center gap-2 rounded-lg bg-[#e53935] px-4 py-2.5 text-sm font-bold text-white hover:bg-[#cf2f2f] disabled:opacity-60">
        <Search className="h-4 w-4" aria-hidden /> {loading ? "Хайж байна…" : "Хайх"}
      </button>
      <button type="button" onClick={onClear} disabled={loading} className="min-h-11 w-full text-sm font-medium text-slate-500 hover:text-slate-800 disabled:opacity-60">Цэвэрлэх</button>
    </div>
  );
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
  const [filterOpen, setFilterOpen] = useState(false);

  const transactionLabel = listingType === "sale" ? "Зарна" : "Түрээслүүлнэ";
  const activeFilterCount = [district, propertyType, rooms, minPrice, maxPrice].filter(Boolean).length;

  useEffect(() => {
    if (!filterOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setFilterOpen(false);
    };
    window.addEventListener("keydown", closeOnEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener("keydown", closeOnEscape);
    };
  }, [filterOpen]);

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
        <div className="mx-auto flex max-w-[1440px] flex-wrap items-center justify-between gap-x-4 gap-y-3 px-5 py-3 sm:flex-nowrap sm:py-4 lg:px-8">
          <Link href="/sale" className="text-xl font-black tracking-tight text-[#e53935]">
            Enerel Market
          </Link>
          <nav className="order-3 flex w-full items-center gap-1 rounded-lg bg-slate-100 p-1 text-sm font-semibold sm:order-none sm:w-auto sm:gap-2">
            <Link
              href="/sale"
              className={`min-h-10 flex-1 rounded-md px-4 py-2 text-center sm:flex-none ${listingType === "sale" ? "bg-white text-[#d92d2d] shadow-sm" : "text-slate-600"}`}
            >
              Худалдах
            </Link>
            <Link
              href="/rent"
              className={`min-h-10 flex-1 rounded-md px-4 py-2 text-center sm:flex-none ${listingType === "rent" ? "bg-white text-[#d92d2d] shadow-sm" : "text-slate-600"}`}
            >
              Түрээслэх
            </Link>
          </nav>
          <Link href="/dashboard" className="hidden text-sm font-medium text-slate-600 hover:text-slate-900 sm:block">
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

        <button
          type="button"
          onClick={() => setFilterOpen(true)}
          className="mb-4 flex min-h-11 w-full items-center justify-center gap-2 rounded-lg border border-slate-300 bg-white px-4 py-2.5 text-sm font-bold shadow-sm lg:hidden"
          aria-haspopup="dialog"
          aria-expanded={filterOpen}
        >
          <SlidersHorizontal className="h-4 w-4 text-[#d92d2d]" aria-hidden />
          Зар шүүх
          {activeFilterCount > 0 && (
            <span className="rounded-full bg-[#e53935] px-2 py-0.5 text-xs text-white">{activeFilterCount}</span>
          )}
        </button>

        <div className="grid items-start gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="hidden rounded-xl border border-slate-200 bg-white p-5 lg:sticky lg:top-5 lg:block">
            <div className="mb-5 flex items-center gap-2 border-b border-slate-100 pb-4">
              <SlidersHorizontal className="h-5 w-5 text-[#d92d2d]" aria-hidden />
              <h2 className="font-bold">Зар шүүх</h2>
            </div>
            <FilterControls facets={facets} district={district} propertyType={propertyType} rooms={rooms} minPrice={minPrice} maxPrice={maxPrice} loading={loading} onDistrictChange={setDistrict} onPropertyTypeChange={setPropertyType} onRoomsChange={setRooms} onMinPriceChange={setMinPrice} onMaxPriceChange={setMaxPrice} onApply={applyFilters} onClear={clearFilters} />
          </aside>

          <section aria-busy={loading}>
            {error && <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            {page.items.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-500">Энэ шүүлтээр зар олдсонгүй.</div>
            ) : (
              <div className={`grid gap-4 sm:grid-cols-2 xl:grid-cols-3 ${loading ? "opacity-60" : ""}`}>
                {page.items.map((listing) => (
                  <MarketplaceListingCard key={listing.id} listing={listing} />
                ))}
              </div>
            )}

            {(cursorHistory.length > 0 || page.has_more) && (
              <div className="mt-6 flex items-center justify-center gap-2 sm:gap-3">
                <button type="button" onClick={previousPage} disabled={loading || cursorHistory.length === 0} className="flex min-h-11 items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold disabled:opacity-40 sm:px-4"><ChevronLeft className="h-4 w-4" aria-hidden /> Өмнөх</button>
                <span className="text-sm text-slate-500">{cursorHistory.length + 1}-р хуудас</span>
                <button type="button" onClick={nextPage} disabled={loading || !page.has_more} className="flex min-h-11 items-center gap-1 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-semibold disabled:opacity-40 sm:px-4">Дараах <ChevronRight className="h-4 w-4" aria-hidden /></button>
              </div>
            )}
          </section>
        </div>
      </main>

      {filterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Зар шүүх">
          <button type="button" className="absolute inset-0 bg-black/45" onClick={() => setFilterOpen(false)} aria-label="Шүүлтүүрийг хаах" />
          <div className="absolute inset-y-0 right-0 flex w-[min(92vw,390px)] flex-col bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="h-5 w-5 text-[#d92d2d]" aria-hidden />
                <h2 className="font-bold">Зар шүүх</h2>
              </div>
              <button type="button" autoFocus onClick={() => setFilterOpen(false)} className="flex h-11 w-11 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100" aria-label="Хаах">
                <X className="h-5 w-5" aria-hidden />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-5">
              <FilterControls facets={facets} district={district} propertyType={propertyType} rooms={rooms} minPrice={minPrice} maxPrice={maxPrice} loading={loading} onDistrictChange={setDistrict} onPropertyTypeChange={setPropertyType} onRoomsChange={setRooms} onMinPriceChange={setMinPrice} onMaxPriceChange={setMaxPrice} onApply={() => { applyFilters(); setFilterOpen(false); }} onClear={clearFilters} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
