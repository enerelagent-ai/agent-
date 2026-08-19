import { BadgeCheck } from "lucide-react";

export function VerifiedComplexBadge({ compact = false }: { compact?: boolean }) {
  return (
    <span
      title="Хотхоны нэр, unit relation болон дүүргийн тохирлыг баталгаажуулсан"
      className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-semibold text-emerald-700"
    >
      <BadgeCheck className="h-3.5 w-3.5" aria-hidden />
      {compact ? "Verified" : "Баталгаатай хотхон"}
    </span>
  );
}
