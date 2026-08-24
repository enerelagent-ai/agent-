import { MarketplaceBrowse } from "@/components/MarketplaceBrowse";
import {
  getListingFacets,
  getInvestmentSummary,
  getListingCountsByType,
  getPriceTrend,
  getTodaysOpportunity,
  searchMarketplaceListings,
  type TransactionType,
} from "@/lib/api";

export async function MarketplaceRoute({
  listingType,
}: {
  listingType: TransactionType;
}) {
  const [facets, initialPage, investmentSummary, todaysOpportunity, listingCounts, priceTrend] = await Promise.all([
    getListingFacets(listingType),
    searchMarketplaceListings({ listingType, limit: 24 }),
    getInvestmentSummary(),
    getTodaysOpportunity(),
    getListingCountsByType(),
    getPriceTrend(),
  ]);

  return (
    <MarketplaceBrowse
      listingType={listingType}
      facets={facets}
      initialPage={initialPage}
      investmentSummary={investmentSummary}
      todaysOpportunity={todaysOpportunity}
      listingCounts={listingCounts}
      priceTrend={priceTrend}
    />
  );
}
