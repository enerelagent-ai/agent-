const API_URL = "http://localhost:8000";

export interface DistrictInvestmentSummary {
  district: string;
  n_sale: number;
  n_rent: number;
  avg_sale_price: number;
  avg_price_per_sqm: number | null;
  gross_rental_yield_pct: number;
  roi_pct: number;
  investment_score: number;
}

export interface PriceTrendPoint {
  snapshot_date: string;
  n_listings: number;
  avg_price: number | null;
  avg_price_per_sqm: number | null;
}

export interface ListingTypeCount {
  bucket: "apartments" | "other";
  listing_type: "sale" | "rent";
  n: number;
}

export interface Listing {
  id: number;
  source: string;
  source_url: string;
  title: string;
  description: string | null;
  price: number | null;
  area_sqm: number | null;
  price_per_sqm: number | null;
  rooms: number | null;
  listing_type: string | null;
  property_type: string | null;
  district: string | null;
  address: string | null;
  lat: number | null;
  lng: number | null;
  contact_phone: string | null;
  photo_urls: string[];
  scraped_at: string;
  created_at: string;
  updated_at: string;
}

async function getJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`${path} returned ${res.status}`);
  }
  return res.json();
}

export function getInvestmentSummary(): Promise<DistrictInvestmentSummary[]> {
  return getJSON("/dashboard/investment-summary");
}

export function getPriceTrend(): Promise<PriceTrendPoint[]> {
  return getJSON("/dashboard/price-trend");
}

export function getListingCountsByType(): Promise<ListingTypeCount[]> {
  return getJSON("/dashboard/listing-counts-by-type");
}

export function getRecentListings(limit = 5): Promise<Listing[]> {
  return getJSON(`/dashboard/listings?limit=${limit}`);
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
