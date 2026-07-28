"use client";

import { useState } from "react";
import { getFilteredListings, type Listing } from "@/lib/api";
import { formatListingPrice, formatPercent } from "@/lib/format";

// Sale and rent listings use different raw property_type strings for the
// same real-world category (see analytics.calculations' _PROPERTY_TYPE_GROUPS
// and the Week 5 investigation) — exact values pulled from the live DB, not
// guessed, since the backend filter is an exact string match.
const SALE_PROPERTY_TYPES = [
  { value: "Орон сууц зарна", label: "Орон сууц" },
  { value: "Газар зарна", label: "Газар" },
  { value: "АОС, хаус, зуслан, амралтын газар зарна", label: "АОС, хаус, зуслан, амралтын газар" },
  { value: "Худалдаа, үйлчилгээний талбай зарна", label: "Худалдаа, үйлчилгээний талбай" },
  { value: "Үйлдвэр, агуулах, oбьект зарна", label: "Үйлдвэр, агуулах, oбьект" },
  { value: "Оффис зарна", label: "Оффис" },
  { value: "Хашаа байшин зарна", label: "Хашаа байшин" },
  { value: "Гараж, контейнер, з-сууц зарна", label: "Гараж, контейнер, з-сууц" },
  { value: "Монгол гэр зарна", label: "Монгол гэр" },
  { value: "00-н өрөө, В1, подвал зарна", label: "00-н өрөө, В1, подвал" },
  { value: "Нийтийн байр, дотуур байр зарна", label: "Нийтийн байр, дотуур байр" },
  { value: "Бусад зарна", label: "Бусад" },
];

const RENT_PROPERTY_TYPES = [
  { value: "Орон сууц түрээслүүлнэ", label: "Орон сууц" },
  { value: "Худалдаа, үйлчилгээний талбай түрээслүүлнэ", label: "Худалдаа, үйлчилгээний талбай" },
  { value: "Оффис түрээслүүлнэ", label: "Оффис" },
  { value: "Үйлдвэр, агуулах, oбьект түрээслүүлнэ", label: "Үйлдвэр, агуулах, oбьект" },
  { value: "АОС, хаус, зуслан, амралтын газар түрээслүүлнэ", label: "АОС, хаус, зуслан, амралтын газар" },
  { value: "Хоногоор байр, байшин түрээслүүлнэ", label: "Хоногоор байр, байшин" },
  { value: "Нийтийн байр, дотуур байр түрээслүүлнэ", label: "Нийтийн байр, дотуур байр" },
  { value: "00-н өрөө, В1, подвал түрээслүүлнэ", label: "00-н өрөө, В1, подвал" },
  { value: "Гараж, контейнер, з-сууц түрээслүүлнэ", label: "Гараж, контейнер, з-сууц" },
  { value: "Хашаа байшин, гэр түрээслүүлнэ", label: "Хашаа байшин, гэр" },
  { value: "Hostel/Хостел", label: "Hostel/Хостел" },
  { value: "Газар түрээслүүлнэ", label: "Газар" },
  { value: "Хурлын өрөө, заал түрээслүүлнэ", label: "Хурлын өрөө, заал" },
];

type Tab = "recent" | "deals";

function timeAgo(isoString: string): string {
  const diffMs = Date.now() - new Date(isoString).getTime();
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  if (diffHours < 1) return "саяхан";
  if (diffHours < 24) return `${diffHours} цагийн өмнө`;
  return `${Math.floor(diffHours / 24)} өдрийн өмнө`;
}

interface RecentListingsProps {
  initialListings: Listing[];
  districts: string[];
  onDistrictApplied?: (district: string | null) => void;
}

export function RecentListings({ initialListings, districts, onDistrictApplied }: RecentListingsProps) {
  const [tab, setTab] = useState<Tab>("recent");
  const [listings, setListings] = useState(initialListings);
  const [district, setDistrict] = useState("");
  const [propertyType, setPropertyType] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [loading, setLoading] = useState(false);

  async function runFetch(nextTab: Tab) {
    setLoading(true);
    try {
      const rows = await getFilteredListings({
        district: district || undefined,
        propertyType: propertyType || undefined,
        minPrice: minPrice ? Number(minPrice) : undefined,
        maxPrice: maxPrice ? Number(maxPrice) : undefined,
        sortBy: nextTab === "deals" ? "deal_pct" : undefined,
        limit: 6,
      });
      setListings(rows);
      onDistrictApplied?.(district || null);
    } finally {
      setLoading(false);
    }
  }

  function selectTab(nextTab: Tab) {
    setTab(nextTab);
    runFetch(nextTab);
  }

  return (
    <div className="rounded-xl border border-line-grid bg-surface-card p-5">
      <div className="mb-4 flex items-center gap-1 border-b border-line-grid">
        <button
          type="button"
          onClick={() => selectTab("recent")}
          className={`border-b-2 px-3 py-2 text-sm font-medium ${
            tab === "recent"
              ? "border-series-1 text-ink-primary"
              : "border-transparent text-ink-muted hover:text-ink-secondary"
          }`}
        >
          Шинэ зар мэдээлэл
        </button>
        <button
          type="button"
          onClick={() => selectTab("deals")}
          className={`border-b-2 px-3 py-2 text-sm font-medium ${
            tab === "deals"
              ? "border-series-1 text-ink-primary"
              : "border-transparent text-ink-muted hover:text-ink-secondary"
          }`}
        >
          Хямд боломж
        </button>
      </div>

      <div className="mb-4 flex flex-wrap items-end gap-3">
        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Дүүрэг
          <select
            value={district}
            onChange={(e) => setDistrict(e.target.value)}
            className="rounded-md border border-line-grid bg-surface-card px-2.5 py-1.5 text-sm text-ink-primary"
          >
            <option value="">Бүгд</option>
            {districts.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Төрөл
          <select
            value={propertyType}
            onChange={(e) => setPropertyType(e.target.value)}
            className="rounded-md border border-line-grid bg-surface-card px-2.5 py-1.5 text-sm text-ink-primary"
          >
            <option value="">Бүгд</option>
            <optgroup label="Худалдах">
              {SALE_PROPERTY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </optgroup>
            <optgroup label="Түрээслэх">
              {RENT_PROPERTY_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </optgroup>
          </select>
        </label>

        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Үнэ, min
          <input
            type="number"
            inputMode="numeric"
            value={minPrice}
            onChange={(e) => setMinPrice(e.target.value)}
            placeholder="0"
            className="w-28 rounded-md border border-line-grid bg-surface-card px-2.5 py-1.5 text-sm text-ink-primary"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-ink-secondary">
          Үнэ, max
          <input
            type="number"
            inputMode="numeric"
            value={maxPrice}
            onChange={(e) => setMaxPrice(e.target.value)}
            placeholder="—"
            className="w-28 rounded-md border border-line-grid bg-surface-card px-2.5 py-1.5 text-sm text-ink-primary"
          />
        </label>

        <button
          type="button"
          onClick={() => runFetch(tab)}
          disabled={loading}
          className="rounded-md bg-series-1 px-4 py-1.5 text-sm font-medium text-white disabled:opacity-60"
        >
          {loading ? "Шүүж байна…" : "Шүүх"}
        </button>
      </div>

      {tab === "deals" && (
        <p className="mb-3 text-xs text-ink-muted">
          Ижил дүүрэг, өрөөний тоо, төрлийн зарын дундаж үнээс мэдэгдэхүйц хямд, өгөгдлийн
          алдаа биш гэж тодорхой итгэлтэй үнэлэгдсэн зарууд эхэнд жагсаана.
        </p>
      )}

      {listings.length === 0 ? (
        <p className="py-4 text-sm text-ink-muted">
          {tab === "deals" ? "Энэ шүүлтээр хямд боломж олдсонгүй." : "Энэ шүүлтээр зар олдсонгүй."}
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-line-grid">
          {listings.map((listing) => {
            const priceDisplay = formatListingPrice(listing);
            return (
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
                    <span
                      className={`shrink-0 text-sm font-semibold ${
                        priceDisplay.isEstimate ? "italic text-ink-secondary" : "text-ink-primary"
                      }`}
                    >
                      {priceDisplay.text}
                    </span>
                  </div>
                  <p className="truncate text-xs text-ink-secondary">
                    {listing.district ?? "Байршил тодорхойгүй"}
                    {listing.rooms ? ` · ${listing.rooms} өрөө` : ""}
                    {listing.area_sqm ? ` · ${listing.area_sqm} мкв` : ""}
                  </p>
                  <div className="mt-1 flex items-center gap-2">
                    <p className="text-xs text-ink-muted">{timeAgo(listing.scraped_at)}</p>
                    {listing.deal_status === "top_deal" && listing.deal_pct !== null && (
                      <span className="rounded-full bg-[#0ca30c]/10 px-2 py-0.5 text-xs font-medium text-[#0ca30c]">
                        ↓ {formatPercent(listing.deal_pct)} дундажаас хямд
                      </span>
                    )}
                  </div>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
