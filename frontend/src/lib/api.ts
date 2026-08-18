// Two different paths to the same backend, depending on where this code
// actually runs:
//
// - In the browser (client components, e.g. RecentListings' filters):
//   relative + same-origin, through src/app/api/backend/[...path]/route.ts,
//   which forwards server-side (see that file for why -- Basic Auth doesn't
//   travel cross-origin, so a direct browser->Render call would 401 with no
//   prompt).
// - On the server (page.tsx is an `async function` Server Component that
//   fetches at request time): Node's fetch() can't resolve a relative URL
//   at all -- there's no browser origin to resolve it against -- so this
//   calls the backend directly instead, attaching the same Basic Auth
//   header the proxy route attaches for the browser path.
const BROWSER_API_URL = "/api/backend";
const SERVER_API_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000";
const ADMIN_USERNAME = process.env.ADMIN_USERNAME;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

export type TransactionType = "sale" | "rent";

export interface DistrictInvestmentSummary {
  district: string;
  n_sale: number;
  n_rent: number;
  avg_sale_price: number;
  min_sale_price: number;
  median_sale_price: number;
  max_sale_price: number;
  avg_price_per_sqm: number | null;
  gross_rental_yield_pct: number;
  roi_pct: number;
  investment_score: number;
  confidence_tier: "high" | "medium" | "low" | "unavailable";
  data_as_of: string;
  room_coverage_pct: number;
  area_coverage_pct: number;
  price_guard_excluded_pct: number;
  confidence_formula_version: string;
  reproducibility: {
    calculated_at: string;
    comparison_group: string;
    n_sale: number;
    n_rent: number;
    median_sale_price: number;
    median_rent_price: number;
    formula_version: string;
  };
}

export interface PriceTrendPoint {
  snapshot_date: string;
  n_listings: number;
  avg_price: number | null;
  avg_price_per_sqm: number | null;
}

// No investment_score/roi_pct -- see analytics.calculations.todays_opportunity's
// docstring on why that composite ranking number is deliberately never
// surfaced to a reader as its own figure.
export interface TodaysOpportunity {
  district: string;
  n_sale: number;
  n_rent: number;
  avg_sale_price: number;
  avg_price_per_sqm: number | null;
  gross_rental_yield_pct: number;
  top_deal_pct: number | null;
  n_deals_analyzed: number;
  last_scraped_at: string;
  confidence_tier: "high" | "medium" | "low" | "unavailable";
  data_as_of: string;
  room_coverage_pct: number;
  area_coverage_pct: number;
  price_guard_excluded_pct: number;
  confidence_formula_version: string;
  reproducibility: DistrictInvestmentSummary["reproducibility"];
}

export interface ListingTypeCount {
  bucket: "apartments" | "other";
  listing_type: "sale" | "rent";
  n: number;
}

export interface ComplexOption {
  id: number;
  canonical_name: string;
}

export interface ListingFacets {
  listing_type: TransactionType;
  total: number;
  districts: Array<{ value: string; count: number }>;
  property_types: Array<{ value: string; count: number }>;
  rooms: Array<{ value: number; count: number }>;
  price: {
    min: number | null;
    max: number | null;
    count: number;
  };
}

export interface MarketplaceListingPage {
  items: Listing[];
  next_cursor: string | null;
  has_more: boolean;
}

export interface MarketplaceSearchFilters {
  listingType: TransactionType;
  district?: string;
  propertyType?: string;
  rooms?: number;
  minPrice?: number;
  maxPrice?: number;
  cursor?: string;
  limit?: number;
}

export interface DealAlertItem {
  id: number;
  title: string;
  source_url: string;
  price: number | null;
  district: string | null;
  complex_name: string | null;
  scraped_at: string;
  deal_pct: number;
}

export interface DealAlertFeed {
  items: DealAlertItem[];
  unseen_count: number;
  last_seen_at: string;
}

export interface Listing {
  id: number;
  source: string;
  source_url: string;
  title: string;
  description: string | null;
  price: number | null;
  price_negotiable: boolean | null;
  area_sqm: number | null;
  price_per_sqm: number | null;
  rooms: number | null;
  floor: number | null;
  total_floors: number | null;
  complex_id: number | null;
  complex_name: string | null;
  listing_type: string | null;
  property_type: string | null;
  district: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  contact_phone: string | null;
  photo_urls: string[];
  view_count: number | null;
  scraped_at: string;
  created_at: string;
  updated_at: string;

  // From analytics.deal_percentages() — null when not applicable (see that
  // function's docstring: non-apartments, thin comparable groups, etc.)
  deal_pct: number | null;
  deal_status: "top_deal" | "needs_review" | "not_notable" | null;
  deal_reason: string | null;
  n_comparable: number | null;
  // Same source as deal_pct — the group's own median price/m² as an
  // absolute number, for showing "your price/m² vs the group's".
  group_median_price_per_sqm: number | null;

  // Independent, stricter comparison within the same canonical complex.
  complex_deal_pct: number | null;
  complex_deal_status: "top_deal" | "needs_review" | "not_notable" | null;
  complex_deal_reason: string | null;
  complex_n_comparable: number | null;
  complex_median_price_per_sqm: number | null;

  // From analytics.estimate_negotiable_price() — only ever set alongside
  // price_negotiable=true, never alongside a deal_pct.
  estimated_price: number | null;
  estimated_price_per_sqm: number | null;
  estimate_basis: "area_based" | "group_median_price" | null;

  // From analytics.rental_yield_by_district_rooms() (Week 5), matched by
  // (district, rooms) regardless of this listing's own listing_type — null
  // when there's no comparable rent-side data for that district+room-count.
  rental_yield_pct: number | null;
  rental_yield_payback_years: number | null;
  rental_yield_n_sale: number | null;
  rental_yield_n_rent: number | null;
}

async function getJSON<T>(path: string): Promise<T> {
  const isServer = typeof window === "undefined";
  const headers: HeadersInit = {};
  if (isServer && ADMIN_USERNAME && ADMIN_PASSWORD) {
    headers["Authorization"] = `Basic ${btoa(`${ADMIN_USERNAME}:${ADMIN_PASSWORD}`)}`;
  }
  const url = isServer ? `${SERVER_API_URL}${path}` : `${BROWSER_API_URL}${path}`;
  const res = await fetch(url, { cache: "no-store", headers });
  if (!res.ok) {
    throw new ApiError(path, res.status);
  }
  return res.json();
}

export class ApiError extends Error {
  constructor(
    public readonly path: string,
    public readonly status: number,
  ) {
    super(`${path} returned ${status}`);
    this.name = "ApiError";
  }
}

async function postJSON<T>(path: string): Promise<T> {
  const isServer = typeof window === "undefined";
  const headers: HeadersInit = {};
  if (isServer && ADMIN_USERNAME && ADMIN_PASSWORD) {
    headers["Authorization"] = `Basic ${btoa(`${ADMIN_USERNAME}:${ADMIN_PASSWORD}`)}`;
  }
  const url = isServer ? `${SERVER_API_URL}${path}` : `${BROWSER_API_URL}${path}`;
  const res = await fetch(url, { method: "POST", cache: "no-store", headers });
  if (!res.ok) throw new Error(`${path} returned ${res.status}`);
  return res.json();
}

export function getDealAlerts(limit = 20): Promise<DealAlertFeed> {
  return getJSON(`/dashboard/deal-alerts?limit=${limit}`);
}

export function markDealAlertsSeen(): Promise<{ last_seen_at: string }> {
  return postJSON("/dashboard/deal-alerts/mark-seen");
}

export function getInvestmentSummary(): Promise<DistrictInvestmentSummary[]> {
  return getJSON("/dashboard/investment-summary");
}

// null when no district clears investment_summary_by_district's own
// data-sufficiency threshold yet -- callers must render that as "not
// available", never as a placeholder or zeroed card.
export function getTodaysOpportunity(): Promise<TodaysOpportunity | null> {
  return getJSON("/dashboard/todays-opportunity");
}

export function getPriceTrend(): Promise<PriceTrendPoint[]> {
  return getJSON("/dashboard/price-trend");
}

export function getListingCountsByType(): Promise<ListingTypeCount[]> {
  return getJSON("/dashboard/listing-counts-by-type");
}

export function getComplexes(): Promise<ComplexOption[]> {
  return getJSON("/dashboard/complexes");
}

export function getListingFacets(
  listingType: TransactionType,
): Promise<ListingFacets> {
  return getJSON(`/listings/facets?listing_type=${listingType}`);
}

export function searchMarketplaceListings(
  filters: MarketplaceSearchFilters,
): Promise<MarketplaceListingPage> {
  const params = new URLSearchParams({ listing_type: filters.listingType });
  if (filters.district) params.set("district", filters.district);
  if (filters.propertyType) params.set("property_type", filters.propertyType);
  if (filters.rooms !== undefined) params.set("rooms", String(filters.rooms));
  if (filters.minPrice !== undefined) params.set("min_price", String(filters.minPrice));
  if (filters.maxPrice !== undefined) params.set("max_price", String(filters.maxPrice));
  if (filters.cursor) params.set("cursor", filters.cursor);
  if (filters.limit !== undefined) params.set("limit", String(filters.limit));
  return getJSON(`/listings/search?${params.toString()}`);
}

export function getRecentListings(limit = 5): Promise<Listing[]> {
  return getJSON(`/dashboard/listings?limit=${limit}`);
}

export function getListing(listingId: number): Promise<Listing> {
  return getJSON(`/listings/${listingId}`);
}

export interface ListingFilters {
  listingType?: TransactionType;
  district?: string;
  propertyType?: string;
  complexId?: number;
  minPrice?: number;
  maxPrice?: number;
  sortBy?: "recent" | "deal_pct";
  dealStatus?: "top_deal" | "needs_review" | "not_notable";
  limit?: number;
  offset?: number;
}

// Client-side counterpart to getRecentListings, for the interactive filter
// controls — same endpoint, just with whichever params are actually set.
export function getFilteredListings(filters: ListingFilters = {}): Promise<Listing[]> {
  const params = new URLSearchParams();
  if (filters.listingType) params.set("listing_type", filters.listingType);
  if (filters.district) params.set("district", filters.district);
  if (filters.propertyType) params.set("property_type", filters.propertyType);
  if (filters.complexId !== undefined) params.set("complex_id", String(filters.complexId));
  if (filters.minPrice !== undefined) params.set("min_price", String(filters.minPrice));
  if (filters.maxPrice !== undefined) params.set("max_price", String(filters.maxPrice));
  if (filters.sortBy) params.set("sort_by", filters.sortBy);
  if (filters.dealStatus) params.set("deal_status", filters.dealStatus);
  params.set("limit", String(filters.limit ?? 6));
  if (filters.offset !== undefined) params.set("offset", String(filters.offset));
  return getJSON(`/dashboard/listings?${params.toString()}`);
}

export interface InvestmentSummaryTotals {
  totalListings: number;
  districtCount: number;
  avgPricePerSqm: number;
  avgYieldPct: number;
}

// Rolls the per-district rows up into headline KPI figures. Weighted by each
// district's own sample size, not a naive average across districts — the
// same recombination principle the backend uses (see
// analytics.calculations.investment_summary_by_district).
export function summarizeInvestment(rows: DistrictInvestmentSummary[]): InvestmentSummaryTotals {
  const totalListings = rows.reduce((sum, r) => sum + r.n_sale + r.n_rent, 0);
  const totalSale = rows.reduce((sum, r) => sum + r.n_sale, 0);
  const pricePerSqmSum = rows.reduce((sum, r) => sum + (r.avg_price_per_sqm ?? 0) * r.n_sale, 0);
  const yieldSum = rows.reduce((sum, r) => sum + r.gross_rental_yield_pct * (r.n_sale + r.n_rent), 0);

  return {
    totalListings,
    districtCount: rows.length,
    avgPricePerSqm: totalSale > 0 ? pricePerSqmSum / totalSale : 0,
    avgYieldPct: totalListings > 0 ? yieldSum / totalListings : 0,
  };
}
