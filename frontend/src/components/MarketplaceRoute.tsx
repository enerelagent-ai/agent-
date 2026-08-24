import { MarketplaceBrowse } from "@/components/MarketplaceBrowse";
import {
  getListingFacets,
  getInvestmentSummary,
  searchMarketplaceListings,
  type TransactionType,
} from "@/lib/api";

export async function MarketplaceRoute({
  listingType,
}: {
  listingType: TransactionType;
}) {
  const [facets, initialPage, investmentSummary] = await Promise.all([
    getListingFacets(listingType),
    searchMarketplaceListings({ listingType, limit: 24 }),
    getInvestmentSummary(),
  ]);

  return (
    <MarketplaceBrowse
      listingType={listingType}
      facets={facets}
      initialPage={initialPage}
      investmentSummary={investmentSummary}
    />
  );
}
