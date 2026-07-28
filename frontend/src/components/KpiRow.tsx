import { Home, Percent, Coins } from "lucide-react";
import { StatTile } from "./StatTile";
import { formatMnt, formatNumber, formatPercent } from "@/lib/format";
import type { InvestmentSummaryTotals } from "@/lib/api";

export function KpiRow({ totals }: { totals: InvestmentSummaryTotals }) {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      <StatTile
        label="Нийт зар (шинжилгээнд буй дүүргүүд)"
        value={formatNumber(totals.totalListings)}
        icon={Home}
        caption={`${totals.districtCount} дүүрэг — зөвхөн орон сууцны зах зээл`}
      />
      <StatTile
        label="Дундаж үнэ / мкв"
        value={formatMnt(totals.avgPricePerSqm)}
        icon={Coins}
        caption="Зарах үнээр, орон сууц"
      />
      <StatTile
        label="Дундаж түрээсийн өгөөж"
        value={formatPercent(totals.avgYieldPct)}
        icon={Percent}
        caption="Жилээр, гэрээт өгөөж (gross)"
      />
    </div>
  );
}
