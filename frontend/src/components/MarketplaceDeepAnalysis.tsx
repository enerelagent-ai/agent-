import { DistrictTable } from "@/components/DistrictTable";
import { DonutChart } from "@/components/DonutChart";
import { KpiRow } from "@/components/KpiRow";
import { PriceTrendChart } from "@/components/PriceTrendChart";
import { TodaysOpportunityCard } from "@/components/TodaysOpportunityCard";
import {
  summarizeInvestment,
  type DistrictInvestmentSummary,
  type ListingTypeCount,
  type PriceTrendPoint,
  type TodaysOpportunity,
  type TransactionType,
} from "@/lib/api";

export function MarketplaceDeepAnalysis({
  listingType,
  district,
  todaysOpportunity,
  investmentSummary,
  listingCounts,
  priceTrend,
}: {
  listingType: TransactionType;
  district: string;
  todaysOpportunity: TodaysOpportunity | null;
  investmentSummary: DistrictInvestmentSummary[];
  listingCounts: ListingTypeCount[];
  priceTrend: PriceTrendPoint[];
}) {
  const totals = summarizeInvestment(investmentSummary);

  return (
    <section id="market-analysis" className="scroll-mt-5 border-t border-slate-200 bg-[#eef1f4] py-8 sm:py-10">
      <div className="mx-auto max-w-[1280px] px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <p className="text-xs font-extrabold uppercase tracking-[0.16em] text-[#e85520]">Зарын өгөгдөлд суурилсан</p>
          <h2 className="mt-2 text-2xl font-black tracking-tight text-[#20334b] sm:text-3xl">
            Дэлгэрэнгүй зах зээлийн анализ
          </h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-slate-600">
            {listingType === "sale" ? "Худалдах" : "Түрээслэх"} заруудаа үзэхийн зэрэгцээ үнэ, түрээсийн өгөөж болон дүүргүүдийн харьцуулалтыг нэг дор шалгана.
          </p>
        </div>

        <div className="flex flex-col gap-6">
          <TodaysOpportunityCard data={todaysOpportunity} />
          <KpiRow totals={totals} />
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
            <DonutChart data={listingCounts} />
            <PriceTrendChart data={priceTrend} />
          </div>
          <DistrictTable rows={investmentSummary} highlightedDistrict={district || null} />
        </div>
      </div>
    </section>
  );
}
