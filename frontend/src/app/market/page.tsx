import { redirect } from "next/navigation";

import { marketplaceV2Enabled } from "@/lib/features";

export default function MarketEntryPage() {
  redirect(marketplaceV2Enabled ? "/sale" : "/dashboard");
}
