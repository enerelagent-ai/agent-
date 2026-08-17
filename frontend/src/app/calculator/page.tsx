import { InvestmentCalculator } from "@/components/InvestmentCalculator";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";

export default function CalculatorPage() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title="Хөрөнгө оруулалтын өгөөж" />
        <main className="flex flex-col gap-6 bg-surface-page p-8">
          <div>
            <h1 className="text-xl font-semibold text-ink-primary">Investment Calculator</h1>
            <p className="mt-1 max-w-3xl text-sm text-ink-secondary">
              Түрээс, зардал болон санхүүжилтийн бодит нөхцөлөө оруулж gross yield, cap rate, cash-on-cash болон зээлийн даацыг тус тус харьцуулна уу.
            </p>
          </div>
          <InvestmentCalculator />
        </main>
      </div>
    </div>
  );
}
