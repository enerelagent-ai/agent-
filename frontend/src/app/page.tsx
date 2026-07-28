import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { KpiRow } from "@/components/KpiRow";
import { DashboardBody } from "@/components/DashboardBody";
import { DonutChart } from "@/components/DonutChart";
import { PriceTrendChart } from "@/components/PriceTrendChart";
import {
  getInvestmentSummary,
  getListingCountsByType,
  getPriceTrend,
  getRecentListings,
  summarizeInvestment,
} from "@/lib/api";

export default async function DashboardPage() {
  const [investmentSummary, listingCounts, priceTrend, recentListings] = await Promise.all([
    getInvestmentSummary(),
    getListingCountsByType(),
    getPriceTrend(),
    getRecentListings(6),
  ]);

  const totals = summarizeInvestment(investmentSummary);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex flex-1 flex-col">
        <Topbar title="Хяналтын самбар" />
        <main className="flex flex-col gap-6 bg-surface-page p-8">
          <KpiRow totals={totals} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <DonutChart data={listingCounts} />
            <PriceTrendChart data={priceTrend} />
          </div>
          <DashboardBody investmentSummary={investmentSummary} initialListings={recentListings} />
        </main>
      </div>
    </div>
  );
}
