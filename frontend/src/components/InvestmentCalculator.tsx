"use client";

import { useMemo, useState } from "react";
import { Banknote, Gauge, Landmark, Percent, TimerReset, WalletCards } from "lucide-react";
import { formatMnt, formatPercent } from "@/lib/format";
import { calculateInvestment, type InvestmentInputs } from "@/lib/investment";
import { InfoTooltip } from "./InfoTooltip";
import { StatTile } from "./StatTile";

type InputState = Record<keyof InvestmentInputs, string>;

const DEFAULTS: InputState = {
  purchasePrice: "250000000",
  monthlyRent: "1800000",
  downPayment: "75000000",
  closingAndRenovation: "10000000",
  annualInterestPct: "16.8",
  loanTermYears: "20",
  vacancyPct: "5",
  monthlyOperatingExpenses: "250000",
};

const FIELDS: Array<{
  key: keyof InvestmentInputs;
  label: string;
  suffix: string;
  help: string;
}> = [
  { key: "purchasePrice", label: "Худалдан авах үнэ", suffix: "₮", help: "Хэлцэл хийхээр тооцож буй нийт үнэ." },
  { key: "monthlyRent", label: "Сарын түрээс", suffix: "₮", help: "Сарын scheduled rent; vacancy-г дараа нь тусад нь хасна." },
  { key: "downPayment", label: "Урьдчилгаа", suffix: "₮", help: "Өөрөөс гаргах зээлийн урьдчилгаа." },
  { key: "closingAndRenovation", label: "Хаалт ба анхны засвар", suffix: "₮", help: "Худалдан авалтын шимтгэл, бүртгэл, анхны засвар зэрэг эхний бэлэн мөнгө." },
  { key: "annualInterestPct", label: "Зээлийн жилийн хүү", suffix: "%", help: "Сарын тэнцүү төлөлтийн тооцоонд ашиглах нэрлэсэн жилийн хүү." },
  { key: "loanTermYears", label: "Зээлийн хугацаа", suffix: "жил", help: "Үндсэн төлбөр бүрэн amortize хийх хугацаа." },
  { key: "vacancyPct", label: "Сул зогсолт", suffix: "%", help: "Түрээслэгчгүй болон төлбөр тасалдах хугацааны таамаг." },
  { key: "monthlyOperatingExpenses", label: "Сарын үйл ажиллагааны зардал", suffix: "₮", help: "СӨХ, менежмент, засварын reserve, даатгал, татвар зэрэг; зээлийн төлбөрийг энд оруулахгүй." },
];

function metric(value: number | null, suffix = "%") {
  return value === null || !Number.isFinite(value) ? "—" : suffix === "%" ? formatPercent(value) : `${value.toFixed(2)}×`;
}

export function InvestmentCalculator() {
  const [values, setValues] = useState<InputState>(DEFAULTS);
  const inputs = useMemo(
    () => Object.fromEntries(
      Object.entries(values).map(([key, value]) => [key, Number(value) || 0]),
    ) as unknown as InvestmentInputs,
    [values],
  );
  const result = useMemo(() => calculateInvestment(inputs), [inputs]);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(320px,0.8fr)_minmax(0,1.2fr)]">
      <section className="rounded-xl border border-line-grid bg-surface-card p-5">
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            <h2 className="font-semibold text-ink-primary">Таны нөхцөл</h2>
            <p className="mt-1 text-xs leading-relaxed text-ink-muted">Жишээ утгуудыг өөрийн бодит нөхцөлөөр солино уу.</p>
          </div>
          <button type="button" onClick={() => setValues(DEFAULTS)} className="text-xs text-series-1 hover:underline">
            Жишээг сэргээх
          </button>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2">
          {FIELDS.map((field) => (
            <label key={field.key} className="flex flex-col gap-1.5 text-xs text-ink-secondary">
              <span className="flex items-center gap-1.5">
                {field.label} <InfoTooltip text={field.help} />
              </span>
              <span className="flex overflow-hidden rounded-md border border-line-grid bg-white focus-within:border-series-1">
                <input
                  type="number"
                  min="0"
                  step="any"
                  value={values[field.key]}
                  onChange={(event) => setValues((current) => ({ ...current, [field.key]: event.target.value }))}
                  className="min-w-0 flex-1 bg-transparent px-3 py-2 text-sm text-ink-primary outline-none"
                />
                <span className="flex items-center border-l border-line-grid bg-surface-page px-2.5 text-xs text-ink-muted">{field.suffix}</span>
              </span>
            </label>
          ))}
        </div>
      </section>

      <section className="space-y-5">
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatTile label="Gross rental yield" value={metric(result.grossRentalYieldPct)} icon={Percent} caption="Зардал, vacancy хасаагүй" />
          <StatTile label="Cap rate" value={metric(result.capRatePct)} icon={Landmark} caption="NOI ÷ худалдан авах үнэ" />
          <StatTile label="Cash-on-cash" value={metric(result.cashOnCashPct)} icon={WalletCards} caption="Зээлийн төлбөрийн дараах cash flow" />
          <StatTile label="DSCR" value={metric(result.dscr, "×")} icon={Gauge} caption="NOI ÷ жилийн зээлийн төлбөр" />
          <StatTile label="Сарын зээлийн төлбөр" value={formatMnt(result.monthlyDebtPayment)} icon={Banknote} caption={`Зээлийн дүн ${formatMnt(result.loanAmount)}`} />
          <StatTile label="Нөхөгдөх хугацаа" value={result.paybackYears === null ? "—" : `${result.paybackYears.toFixed(1)} жил`} icon={TimerReset} caption="Анхны cash ÷ жилийн cash flow" />
        </div>

        <div className="rounded-xl border border-line-grid bg-surface-card p-5">
          <h2 className="font-semibold text-ink-primary">Жилийн мөнгөн урсгал</h2>
          <dl className="mt-4 divide-y divide-line-grid text-sm">
            <div className="flex justify-between py-2"><dt className="text-ink-secondary">Vacancy хассан түрээс</dt><dd>{formatMnt(result.effectiveAnnualRent)}</dd></div>
            <div className="flex justify-between py-2"><dt className="text-ink-secondary">Үйл ажиллагааны зардал</dt><dd>− {formatMnt(result.annualOperatingExpenses)}</dd></div>
            <div className="flex justify-between py-2 font-medium"><dt>NOI</dt><dd>{formatMnt(result.noi)}</dd></div>
            <div className="flex justify-between py-2"><dt className="text-ink-secondary">Жилийн зээлийн төлбөр</dt><dd>− {formatMnt(result.monthlyDebtPayment * 12)}</dd></div>
            <div className={`flex justify-between py-3 text-base font-semibold ${result.annualCashFlow < 0 ? "text-red-600" : "text-[#0ca30c]"}`}>
              <dt>Татварын өмнөх cash flow</dt><dd>{formatMnt(result.annualCashFlow)}</dd>
            </div>
          </dl>
          <p className="mt-3 text-xs leading-relaxed text-ink-muted">
            Энэ бол таны оруулсан таамаг дээрх scenario calculation; зах зээлийн forecast эсвэл хөрөнгө оруулалтын зөвлөгөө биш. Элэгдэл, орлогын татвар, борлуулалтын үнэ болон борлуулалтын зардал ороогүй.
          </p>
        </div>
      </section>
    </div>
  );
}
