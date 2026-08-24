"use client";

import Link from "next/link";
import { BarChart3, ChevronDown, ChevronLeft, ChevronRight, Home, Menu, Search, SlidersHorizontal, X } from "lucide-react";
import { useEffect, useState } from "react";

import {
  searchMarketplaceListings,
  type ListingFacets,
  type DistrictInvestmentSummary,
  type MarketplaceListingPage,
  type ListingTypeCount,
  type PriceTrendPoint,
  type TodaysOpportunity,
  type TransactionType,
} from "@/lib/api";
import { formatMnt } from "@/lib/format";
import { MarketplaceListingCard } from "./MarketplaceListingCard";
import { MarketplaceInsightPanel } from "./MarketplaceInsightPanel";
import { MarketplaceDeepAnalysis } from "./MarketplaceDeepAnalysis";

const PAGE_SIZE = 24;

function categoryLabel(value: string): string {
  return value
    .replace(/ түрээслүүлнэ$/u, "")
    .replace(/ зарна$/u, "");
}

interface FilterControlsProps {
  facets: ListingFacets;
  district: string;
  complexId: string;
  propertyType: string;
  rooms: string;
  minPrice: string;
  maxPrice: string;
  loading: boolean;
  onDistrictChange: (value: string) => void;
  onComplexIdChange: (value: string) => void;
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
  complexId,
  propertyType,
  rooms,
  minPrice,
  maxPrice,
  loading,
  onDistrictChange,
  onComplexIdChange,
  onPropertyTypeChange,
  onRoomsChange,
  onMinPriceChange,
  onMaxPriceChange,
  onApply,
  onClear,
}: FilterControlsProps) {
  const complexes = facets.complexes ?? [];
  const availableComplexes = district
    ? complexes.filter((item) => item.district === district)
    : complexes;

  return (
    <div className="space-y-5">
      <label className="block text-[13px] font-bold text-slate-800">
        Дүүрэг
        <select value={district} onChange={(event) => onDistrictChange(event.target.value)} className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-base outline-none transition focus:border-[#ff6b35] focus:ring-2 focus:ring-[#ff6b35]/10 sm:text-sm">
          <option value="">Бүх дүүрэг</option>
          {facets.districts.map((item) => <option key={item.value} value={item.value}>{item.value} ({item.count})</option>)}
        </select>
      </label>

      <label className="block text-[13px] font-bold text-slate-800">
        Хотхон / хороолол
        <select value={complexId} onChange={(event) => onComplexIdChange(event.target.value)} className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-base outline-none transition focus:border-[#ff6b35] focus:ring-2 focus:ring-[#ff6b35]/10 sm:text-sm">
          <option value="">Бүх хотхон</option>
          {availableComplexes.map((item) => (
            <option key={`${item.id}-${item.district ?? ""}`} value={item.id}>
              {item.name} ({item.count})
            </option>
          ))}
        </select>
        <p className="mt-1.5 text-[11px] leading-4 text-slate-400">Зөвхөн баталгаажсан хотхоны холбоосууд</p>
      </label>

      <label className="block text-[13px] font-bold text-slate-800">
        Үл хөдлөхийн төрөл
        <select value={propertyType} onChange={(event) => onPropertyTypeChange(event.target.value)} className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-base outline-none transition focus:border-[#ff6b35] focus:ring-2 focus:ring-[#ff6b35]/10 sm:text-sm">
          <option value="">Бүх төрөл</option>
          {facets.property_types.map((item) => <option key={item.value} value={item.value}>{categoryLabel(item.value)} ({item.count})</option>)}
        </select>
      </label>

      <label className="block text-[13px] font-bold text-slate-800">
        Өрөөний тоо
        <select value={rooms} onChange={(event) => onRoomsChange(event.target.value)} className="mt-2 min-h-11 w-full rounded-md border border-slate-300 bg-white px-3 py-2.5 text-base outline-none transition focus:border-[#ff6b35] focus:ring-2 focus:ring-[#ff6b35]/10 sm:text-sm">
          <option value="">Бүгд</option>
          {facets.rooms.map((item) => <option key={item.value} value={item.value}>{item.value} өрөө ({item.count})</option>)}
        </select>
      </label>

      <div>
        <p className="text-[13px] font-bold text-slate-800">Үнэ</p>
        <div className="mt-2 grid grid-cols-2 gap-2">
          <input aria-label="Доод үнэ" type="number" min="0" inputMode="numeric" value={minPrice} onChange={(event) => onMinPriceChange(event.target.value)} placeholder="Доод" className="min-h-11 min-w-0 rounded-md border border-slate-300 px-3 py-2.5 text-base outline-none focus:border-[#ff6b35] sm:text-sm" />
          <input aria-label="Дээд үнэ" type="number" min="0" inputMode="numeric" value={maxPrice} onChange={(event) => onMaxPriceChange(event.target.value)} placeholder="Дээд" className="min-h-11 min-w-0 rounded-md border border-slate-300 px-3 py-2.5 text-base outline-none focus:border-[#ff6b35] sm:text-sm" />
        </div>
        {facets.price.min !== null && facets.price.max !== null && (
          <p className="mt-1.5 text-xs text-slate-400">{formatMnt(facets.price.min)} – {formatMnt(facets.price.max)}</p>
        )}
      </div>

      <button type="button" onClick={onApply} disabled={loading} className="flex min-h-11 w-full items-center justify-center gap-2 rounded-md bg-[#ff6b35] px-4 py-2.5 text-sm font-extrabold text-white shadow-sm transition hover:bg-[#ed5b29] disabled:opacity-60">
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
  investmentSummary,
  todaysOpportunity,
  listingCounts,
  priceTrend,
}: {
  listingType: TransactionType;
  facets: ListingFacets;
  initialPage: MarketplaceListingPage;
  investmentSummary: DistrictInvestmentSummary[];
  todaysOpportunity: TodaysOpportunity | null;
  listingCounts: ListingTypeCount[];
  priceTrend: PriceTrendPoint[];
}) {
  const [page, setPage] = useState(initialPage);
  const [district, setDistrict] = useState("");
  const [complexId, setComplexId] = useState("");
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
  const activeFilterCount = [district, complexId, propertyType, rooms, minPrice, maxPrice].filter(Boolean).length;

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

  async function load(
    nextCursor?: string,
    nextHistory = cursorHistory,
    propertyTypeOverride?: string,
  ) {
    setLoading(true);
    setError(null);
    try {
      const result = await searchMarketplaceListings({
        listingType,
        district: district || undefined,
        complexId: complexId ? Number(complexId) : undefined,
        propertyType: (propertyTypeOverride ?? propertyType) || undefined,
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

  function selectPropertyType(value: string) {
    setPropertyType(value);
    void load(undefined, [], value);
  }

  function clearFilters() {
    setDistrict("");
    setComplexId("");
    setPropertyType("");
    setRooms("");
    setMinPrice("");
    setMaxPrice("");
    setPage(initialPage);
    setCursor(undefined);
    setCursorHistory([]);
    setError(null);
  }

  function changeDistrict(value: string) {
    setDistrict(value);
    if (complexId) {
      const selectedComplex = facets.complexes?.find((item) => item.id === Number(complexId));
      if (value && selectedComplex?.district !== value) setComplexId("");
    }
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
    <div className="min-h-screen bg-[#f3f5f7] text-slate-900">
      <header className="bg-[#20334b] text-white shadow-sm">
        <div className="border-b border-white/10">
          <div className="mx-auto flex h-9 max-w-[1280px] items-center justify-between px-4 text-[11px] text-slate-300 sm:px-6 lg:px-8">
            <span>Үл хөдлөх хөрөнгийн зар ба бодит зах зээлийн шинжилгээ</span>
            <Link href="#market-analysis" className="hidden items-center gap-1.5 font-semibold hover:text-white sm:flex"><BarChart3 className="h-3.5 w-3.5" /> Зах зээлийн анализ</Link>
          </div>
        </div>
        <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-3 px-4 py-4 sm:flex-nowrap sm:px-6 lg:px-8">
          <Link href="/sale" className="flex items-center gap-2 text-xl font-black tracking-tight">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#ff6b35] text-white"><Home className="h-5 w-5" /></span>
            <span>Enerel<span className="text-[#ff8a5c]">Market</span></span>
          </Link>
          <nav className="order-3 flex w-full items-center gap-1 rounded-lg bg-white/10 p-1 text-sm font-bold sm:order-none sm:w-auto">
            <Link
              href="/sale"
              className={`min-h-10 flex-1 rounded-md px-5 py-2 text-center transition sm:flex-none ${listingType === "sale" ? "bg-white text-[#20334b] shadow-sm" : "text-slate-200 hover:bg-white/10"}`}
            >
              Худалдах
            </Link>
            <Link
              href="/rent"
              className={`min-h-10 flex-1 rounded-md px-5 py-2 text-center transition sm:flex-none ${listingType === "rent" ? "bg-white text-[#20334b] shadow-sm" : "text-slate-200 hover:bg-white/10"}`}
            >
              Түрээслэх
            </Link>
          </nav>
          <Link href="#market-analysis" className="hidden rounded-md bg-[#ff6b35] px-4 py-2.5 text-sm font-extrabold text-white shadow-sm transition hover:bg-[#ed5b29] sm:block">
            Анализ харах
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-4 py-5 sm:px-6 lg:px-8">
        <nav className="mb-4 flex items-center gap-2 text-xs text-slate-500" aria-label="Breadcrumb">
          <Link href="/sale" className="hover:text-[#ff6b35]">Нүүр</Link><ChevronRight className="h-3.5 w-3.5" />
          <span>Үл хөдлөх</span><ChevronRight className="h-3.5 w-3.5" />
          <span className="font-semibold text-slate-700">{transactionLabel}</span>
        </nav>

        <div className="mb-5 overflow-hidden rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
            <div>
              <h1 className="text-xl font-extrabold sm:text-2xl">Үл хөдлөх {transactionLabel.toLowerCase()}</h1>
              <p className="mt-1 text-sm text-slate-500">{facets.total.toLocaleString("mn-MN")} идэвхтэй зар</p>
            </div>
            <Menu className="mt-1 h-5 w-5 text-slate-400 lg:hidden" />
          </div>
          <div className="flex gap-2 overflow-x-auto px-4 py-3 [scrollbar-width:none]">
            <button type="button" onClick={() => selectPropertyType("")} className={`shrink-0 rounded-full px-4 py-2 text-xs font-bold ${propertyType === "" ? "bg-[#20334b] text-white" : "border border-slate-200 bg-white text-slate-700"}`}>Бүх төрөл</button>
            {facets.property_types.slice(0, 7).map((item) => (
              <button key={item.value} type="button" onClick={() => selectPropertyType(item.value)} className={`shrink-0 rounded-full border px-4 py-2 text-xs font-semibold transition ${propertyType === item.value ? "border-[#20334b] bg-[#20334b] text-white" : "border-slate-200 bg-white text-slate-700 hover:border-[#ff6b35] hover:text-[#e85520]"}`}>
                {categoryLabel(item.value)} <span className="text-slate-400">{item.count}</span>
              </button>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={() => setFilterOpen(true)}
          className="mb-4 flex min-h-11 w-full items-center justify-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-bold shadow-sm lg:hidden"
          aria-haspopup="dialog"
          aria-expanded={filterOpen}
        >
          <SlidersHorizontal className="h-4 w-4 text-[#ff6b35]" aria-hidden />
          Зар шүүх
          {activeFilterCount > 0 && (
            <span className="rounded-full bg-[#ff6b35] px-2 py-0.5 text-xs text-white">{activeFilterCount}</span>
          )}
        </button>

        <details className="group mb-4 overflow-hidden rounded-lg border border-slate-200 bg-white xl:hidden">
          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between px-4 text-sm font-extrabold text-[#20334b]">
            <span className="flex items-center gap-2"><BarChart3 className="h-4 w-4 text-[#ff6b35]" /> Зах зээлийн анализ</span>
            <ChevronDown className="h-4 w-4 transition group-open:rotate-180" />
          </summary>
          <div className="border-t border-slate-100 p-3">
            <MarketplaceInsightPanel listingType={listingType} district={district} summaries={investmentSummary} />
          </div>
        </details>

        <div className="grid items-start gap-5 lg:grid-cols-[240px_minmax(0,1fr)] xl:grid-cols-[240px_minmax(0,1fr)_260px]">
          <aside className="hidden overflow-hidden rounded-lg border border-slate-200 bg-white lg:sticky lg:top-5 lg:block">
            <div className="mb-5 flex items-center gap-2 border-b border-slate-100 pb-4">
              <div className="flex w-full items-center gap-2 bg-slate-50 px-5 pt-4"><SlidersHorizontal className="h-4 w-4 text-[#ff6b35]" aria-hidden /><h2 className="text-sm font-extrabold">Нарийвчилсан хайлт</h2></div>
            </div>
            <div className="px-5 pb-5"><FilterControls facets={facets} district={district} complexId={complexId} propertyType={propertyType} rooms={rooms} minPrice={minPrice} maxPrice={maxPrice} loading={loading} onDistrictChange={changeDistrict} onComplexIdChange={setComplexId} onPropertyTypeChange={setPropertyType} onRoomsChange={setRooms} onMinPriceChange={setMinPrice} onMaxPriceChange={setMaxPrice} onApply={applyFilters} onClear={clearFilters} /></div>
          </aside>

          <section aria-busy={loading}>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-200 bg-white px-4 py-3">
              <p className="text-sm text-slate-600"><strong className="text-slate-900">{page.items.length}</strong> зар харуулж байна</p>
              <label className="flex items-center gap-2 text-xs font-semibold text-slate-500">Эрэмбэлэх
                <span className="relative"><select aria-label="Эрэмбэлэх" className="appearance-none rounded-md border border-slate-200 bg-white py-2 pl-3 pr-8 text-xs font-bold text-slate-700"><option>Шинэ нь эхэндээ</option></select><ChevronDown className="pointer-events-none absolute right-2 top-2.5 h-3.5 w-3.5 text-slate-400" /></span>
              </label>
            </div>
            {error && <p role="alert" className="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p>}
            {page.items.length === 0 ? (
              <div className="rounded-xl border border-slate-200 bg-white p-10 text-center text-slate-500">Энэ шүүлтээр зар олдсонгүй.</div>
            ) : (
              <div className={`grid gap-3 sm:grid-cols-2 xl:grid-cols-3 ${loading ? "opacity-60" : ""}`}>
                {page.items.map((listing) => (
                  <MarketplaceListingCard key={listing.id} listing={listing} />
                ))}
              </div>
            )}

            {(cursorHistory.length > 0 || page.has_more) && (
              <div className="mt-6 flex items-center justify-center gap-2 sm:gap-3">
                <button type="button" onClick={previousPage} disabled={loading || cursorHistory.length === 0} className="flex min-h-11 items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold disabled:opacity-40 sm:px-4"><ChevronLeft className="h-4 w-4" aria-hidden /> Өмнөх</button>
                <span className="text-sm text-slate-500">{cursorHistory.length + 1}-р хуудас</span>
                <button type="button" onClick={nextPage} disabled={loading || !page.has_more} className="flex min-h-11 items-center gap-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-semibold disabled:opacity-40 sm:px-4">Дараах <ChevronRight className="h-4 w-4" aria-hidden /></button>
              </div>
            )}
          </section>

          <aside className="hidden xl:sticky xl:top-5 xl:block">
            <MarketplaceInsightPanel listingType={listingType} district={district} summaries={investmentSummary} />
          </aside>
        </div>
      </main>

      <MarketplaceDeepAnalysis
        listingType={listingType}
        district={district}
        todaysOpportunity={todaysOpportunity}
        investmentSummary={investmentSummary}
        listingCounts={listingCounts}
        priceTrend={priceTrend}
      />

      {filterOpen && (
        <div className="fixed inset-0 z-50 lg:hidden" role="dialog" aria-modal="true" aria-label="Зар шүүх">
          <button type="button" className="absolute inset-0 bg-black/45" onClick={() => setFilterOpen(false)} aria-label="Шүүлтүүрийг хаах" />
          <div className="absolute inset-y-0 right-0 flex w-[min(92vw,390px)] flex-col bg-white shadow-2xl">
            <div className="flex items-center justify-between border-b border-slate-200 px-5 py-4">
              <div className="flex items-center gap-2">
                <SlidersHorizontal className="h-5 w-5 text-[#ff6b35]" aria-hidden />
                <h2 className="font-bold">Зар шүүх</h2>
              </div>
              <button type="button" autoFocus onClick={() => setFilterOpen(false)} className="flex h-11 w-11 items-center justify-center rounded-full text-slate-600 hover:bg-slate-100" aria-label="Хаах">
                <X className="h-5 w-5" aria-hidden />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto px-5 py-5">
              <FilterControls facets={facets} district={district} complexId={complexId} propertyType={propertyType} rooms={rooms} minPrice={minPrice} maxPrice={maxPrice} loading={loading} onDistrictChange={changeDistrict} onComplexIdChange={setComplexId} onPropertyTypeChange={setPropertyType} onRoomsChange={setRooms} onMinPriceChange={setMinPrice} onMaxPriceChange={setMaxPrice} onApply={() => { applyFilters(); setFilterOpen(false); }} onClear={clearFilters} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
