import { TrendingUp } from "lucide-react";
import type { TodaysOpportunity } from "@/lib/api";
import { formatMnt, formatPercent, timeAgo } from "@/lib/format";
import { InfoTooltip } from "./InfoTooltip";

const METHODOLOGY_TEXT =
  "Investment_summary_by_district-ийн эрэмбэлсэн жагсаалтын №1 дүүрэг (дундаж " +
  "зарах үнэ, түрээсийн өгөөжийг тэнцвэржүүлсэн, ил тод томьёогоор). Энэ бол " +
  "AI загвар эсвэл урьдчилсан таамаг биш — зөвхөн одоо байгаа бодит зарнуудын " +
  "статистик тоймоос гарсан дүн. Хямд зарын эзлэх хувь тухайн дүүргийн " +
  "харьцуулах боломжтой (дор хаяж 20 ижил төрлийн) зарууд дундах хямд гэж " +
  "тооцогдсон хувиар тооцогдоно.";

// A stat that can genuinely be unavailable (e.g. top_deal_pct when the
// district's own comparable groups are all too thin) renders the same
// fallback text rather than a 0% or a blank -- see calculations.py's
// todays_opportunity() docstring for why null is a real, expected outcome
// here, not a bug.
function Stat({
  label,
  value,
  sampleSize,
}: {
  label: string;
  value: string | null;
  sampleSize?: string;
}) {
  return (
    <div>
      <div className="text-xs text-white/60">{label}</div>
      <div className="mt-1 text-xl font-semibold text-white">
        {value ?? <span className="text-base font-normal text-white/50">Одоогоор тооцоолох боломжгүй</span>}
      </div>
      {sampleSize && value && <div className="mt-0.5 text-xs text-white/40">{sampleSize}</div>}
    </div>
  );
}

export function TodaysOpportunityCard({ data }: { data: TodaysOpportunity | null }) {
  if (!data) {
    return (
      <div className="rounded-xl border border-line-grid bg-surface-card p-6">
        <div className="flex items-center gap-2 text-sm font-medium text-ink-secondary">
          <TrendingUp className="h-4 w-4 text-ink-muted" aria-hidden />
          Өнөөдрийн мэдээллээр тэргүүлж буй дүүрэг
        </div>
        <p className="mt-3 text-ink-primary">Мэдээлэл хүрэлцэхгүй байна</p>
        <p className="mt-1 text-sm text-ink-muted">
          Дор хаяж 20 худалдах болон 20 түрээслэх зартай дүүрэг олдоогүй байна — өгөгдөл
          цугларах хүртэл хүлээнэ үү.
        </p>
      </div>
    );
  }

  return (
    <div className="relative overflow-hidden rounded-xl bg-[#111a3d] p-6 text-white sm:p-8">
      <div className="flex items-center gap-2 text-sm font-medium text-white/70">
        <TrendingUp className="h-4 w-4 text-series-1" aria-hidden />
        Өнөөдрийн мэдээллээр тэргүүлж буй дүүрэг
        <span className="text-white/40">— Өгөгдөлд суурилсан боломж</span>
      </div>

      <h2 className="mt-2 text-3xl font-semibold">{data.district}</h2>

      <div className="mt-6 grid grid-cols-2 gap-x-6 gap-y-5 sm:grid-cols-4">
        <Stat
          label="Дундаж үнэ / м²"
          value={data.avg_price_per_sqm !== null ? formatMnt(data.avg_price_per_sqm) : null}
        />
        <Stat
          label="Түрээсийн өгөөж"
          value={formatPercent(data.gross_rental_yield_pct)}
          sampleSize={`${data.n_sale} зарна, ${data.n_rent} түрээслэнэ`}
        />
        <Stat
          label="Хямд зарын эзлэх хувь"
          value={data.top_deal_pct !== null ? formatPercent(data.top_deal_pct) : null}
          sampleSize={data.n_deals_analyzed > 0 ? `${data.n_deals_analyzed} зарыг харьцуулсан` : undefined}
        />
        <Stat label="Шинжилсэн зар" value={String(data.n_sale + data.n_rent)} />
      </div>

      <p className="mt-6 max-w-xl text-sm leading-relaxed text-white/70">
        Одоогийн өгөгдлөөр {data.district} дүүрэг дундаж үнэ болон түрээсийн өгөөжийн
        харьцуулсан дүнгээр бусад дүүргээс тэргүүлж байна.
      </p>

      <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-1.5 border-t border-white/10 pt-4 text-xs text-white/50">
        <span>Сүүлд шинэчлэгдсэн: {timeAgo(data.last_scraped_at)}</span>
        <span aria-hidden>·</span>
        <span>Энэ дүгнэлт урьдчилсан бөгөөд цаашид өөрчлөгдөж болно</span>
        <InfoTooltip text={METHODOLOGY_TEXT} triggerClassName="text-white/50 hover:text-white" />
      </div>
    </div>
  );
}
