export interface InvestmentInputs {
  purchasePrice: number;
  monthlyRent: number;
  downPayment: number;
  closingAndRenovation: number;
  annualInterestPct: number;
  loanTermYears: number;
  vacancyPct: number;
  monthlyOperatingExpenses: number;
}

export interface InvestmentResults {
  loanAmount: number;
  monthlyDebtPayment: number;
  effectiveAnnualRent: number;
  annualOperatingExpenses: number;
  noi: number;
  annualCashFlow: number;
  initialCashInvested: number;
  grossRentalYieldPct: number | null;
  capRatePct: number | null;
  cashOnCashPct: number | null;
  dscr: number | null;
  paybackYears: number | null;
}

function safeRatio(numerator: number, denominator: number): number | null {
  return denominator > 0 ? numerator / denominator : null;
}

export function calculateInvestment(input: InvestmentInputs): InvestmentResults {
  const purchasePrice = Math.max(0, input.purchasePrice);
  const downPayment = Math.min(purchasePrice, Math.max(0, input.downPayment));
  const loanAmount = Math.max(0, purchasePrice - downPayment);
  const months = Math.max(0, Math.round(input.loanTermYears * 12));
  const monthlyRate = Math.max(0, input.annualInterestPct) / 100 / 12;

  let monthlyDebtPayment = 0;
  if (loanAmount > 0 && months > 0) {
    monthlyDebtPayment = monthlyRate === 0
      ? loanAmount / months
      : loanAmount * monthlyRate * (1 + monthlyRate) ** months
        / ((1 + monthlyRate) ** months - 1);
  }

  const vacancyRate = Math.min(100, Math.max(0, input.vacancyPct)) / 100;
  const effectiveAnnualRent = Math.max(0, input.monthlyRent) * 12 * (1 - vacancyRate);
  const annualOperatingExpenses = Math.max(0, input.monthlyOperatingExpenses) * 12;
  const noi = effectiveAnnualRent - annualOperatingExpenses;
  const annualDebtService = monthlyDebtPayment * 12;
  const annualCashFlow = noi - annualDebtService;
  const initialCashInvested = downPayment + Math.max(0, input.closingAndRenovation);

  const grossYield = safeRatio(Math.max(0, input.monthlyRent) * 12, purchasePrice);
  const capRate = safeRatio(noi, purchasePrice);
  const cashOnCash = safeRatio(annualCashFlow, initialCashInvested);

  return {
    loanAmount,
    monthlyDebtPayment,
    effectiveAnnualRent,
    annualOperatingExpenses,
    noi,
    annualCashFlow,
    initialCashInvested,
    grossRentalYieldPct: grossYield === null ? null : grossYield * 100,
    capRatePct: capRate === null ? null : capRate * 100,
    cashOnCashPct: cashOnCash === null ? null : cashOnCash * 100,
    dscr: annualDebtService > 0 ? noi / annualDebtService : null,
    paybackYears: annualCashFlow > 0 && initialCashInvested > 0
      ? initialCashInvested / annualCashFlow
      : null,
  };
}
