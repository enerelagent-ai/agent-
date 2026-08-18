import { redirect } from "next/navigation";

import { DashboardPage } from "@/components/DashboardPage";
import { marketplaceV2Enabled } from "@/lib/features";

export default function HomePage() {
  if (marketplaceV2Enabled) redirect("/market");
  return <DashboardPage />;
}
