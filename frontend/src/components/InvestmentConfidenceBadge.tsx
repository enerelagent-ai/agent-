"use client";

import { AlertTriangle, CheckCircle2, ShieldCheck } from "lucide-react";

import type { DistrictInvestmentSummary } from "@/lib/api";
import { formatMnt } from "@/lib/format";
import { InfoTooltip } from "./InfoTooltip";

type ConfidenceData = Pick<
  DistrictInvestmentSummary,
  | "confidence_tier"
  | "data_as_of"
  | "room_coverage_pct"
  | "area_coverage_pct"
  | "price_guard_excluded_pct"
  | "confidence_formula_version"
  | "reproducibility"
>;

const TIER = {
  high: {
    label: "Өндөр итгэлцэл",
    className: "border-emerald-200 bg-emerald-50 text-emerald-700",
    darkClassName: "border-emerald-300/25 bg-emerald-300/10 text-emerald-200",
    Icon: ShieldCheck,
  },
  medium: {
    label: "Дунд итгэлцэл",
    className: "border-amber-200 bg-amber-50 text-amber-700",
    darkClassName: "border-amber-300/25 bg-amber-300/10 text-amber-200",
    Icon: CheckCircle2,
  },
  low: {
    label: "Бага итгэлцэл",
    className: "border-orange-200 bg-orange-50 text-orange-700",
    darkClassName: "border-orange-300/25 bg-orange-300/10 text-orange-200",
    Icon: AlertTriangle,
  },
  unavailable: {
    label: "Тооцоолох боломжгүй",
    className: "border-slate-200 bg-slate-50 text-slate-600",
    darkClassName: "border-white/20 bg-white/10 text-white/70",
    Icon: AlertTriangle,
  },
} as const;

export function InvestmentConfidenceBadge({
  data,
  dark = false,
}: {
  data: ConfidenceData;
  dark?: boolean;
}) {
  const tier = TIER[data.confidence_tier];
  const { reproducibility } = data;
  const asOf = new Date(data.data_as_of).toLocaleString("mn-MN", {
    timeZone: "Asia/Ulaanbaatar",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  const calculatedAt = new Date(reproducibility.calculated_at).toLocaleString("mn-MN", {
    timeZone: "Asia/Ulaanbaatar",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
  const explanation =
    `${reproducibility.n_sale} худалдах / ${reproducibility.n_rent} түрээслэх зар. ` +
    `Өгөгдөл: ${asOf}. Өрөөний coverage ${data.room_coverage_pct.toFixed(1)}%, ` +
    `талбайн coverage ${data.area_coverage_pct.toFixed(1)}%, price guard-аар ` +
    `${data.price_guard_excluded_pct.toFixed(1)}% хасагдсан. ` +
    `Медиан үнэ ${formatMnt(reproducibility.median_sale_price)}, медиан сарын түрээс ` +
    `${formatMnt(reproducibility.median_rent_price)}. Тооцоолсон: ${calculatedAt}. ` +
    `Бүлэг: ${reproducibility.comparison_group}. ` +
    `Formula: ${reproducibility.formula_version}; confidence: ${data.confidence_formula_version}.`;
  const Icon = tier.Icon;

  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className={`inline-flex items-center gap-1 rounded-full border px-2 py-1 text-xs font-semibold ${
          dark ? tier.darkClassName : tier.className
        }`}
      >
        <Icon className="h-3.5 w-3.5" aria-hidden />
        {tier.label}
      </span>
      <InfoTooltip
        text={explanation}
        triggerClassName={dark ? "text-white/50 hover:text-white" : undefined}
      />
    </span>
  );
}
