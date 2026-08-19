import { MarketplaceBrowse } from "@/components/MarketplaceBrowse";
import {
  getListingFacets,
  searchMarketplaceListings,
  type TransactionType,
} from "@/lib/api";

export async function MarketplaceRoute({
  listingType,
}: {
  listingType: TransactionType;
}) {
  const [facets, initialPage] = await Promise.all([
    getListingFacets(listingType),
    searchMarketplaceListings({ listingType, limit: 24 }),
  ]);

  return (
    <MarketplaceBrowse
      listingType={listingType}
      facets={facets}
      initialPage={initialPage}
    />
  );
}
