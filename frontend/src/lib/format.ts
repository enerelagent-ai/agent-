export function formatNumber(value: number): string {
  return new Intl.NumberFormat("en-US").format(Math.round(value));
}

export function formatMnt(value: number): string {
  return `${formatNumber(value)}₮`;
}

export function formatPercent(value: number): string {
  return `${value.toFixed(2)}%`;
}

interface PriceLike {
  price: number | null;
  price_negotiable: boolean | null;
  estimated_price: number | null;
}

export interface ListingPriceDisplay {
  text: string;
  isEstimate: boolean;
}

// A price_negotiable listing's own `price` is a placeholder (e.g. "170 ₮
// Үнэ тохирно" parses to a literal ~170), never real — must never be shown
// as if it were a confirmed price. Prefer the group-based estimate with
// clear "estimated, unconfirmed" wording; if no estimate exists either
// (see estimate_negotiable_price()'s own comparability guards), say so
// rather than showing a fabricated or missing number.
export function formatListingPrice(listing: PriceLike): ListingPriceDisplay {
  if (listing.price_negotiable) {
    if (listing.estimated_price !== null) {
      return {
        text: `Ойролцоогоор ~${formatMnt(listing.estimated_price)} (тооцоолсон, батлагдаагүй)`,
        isEstimate: true,
      };
    }
    return { text: "Үнэ тохирно (тооцоолол алга)", isEstimate: true };
  }
  if (listing.price === null) {
    return { text: "—", isEstimate: false };
  }
  return { text: formatMnt(listing.price), isEstimate: false };
}
