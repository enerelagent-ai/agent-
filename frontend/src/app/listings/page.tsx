import { RecentListings } from "@/components/RecentListings";
import { Sidebar } from "@/components/Sidebar";
import { Topbar } from "@/components/Topbar";
import { getComplexes, getFilteredListings, getInvestmentSummary } from "@/lib/api";

const PAGE_SIZE = 24;

export default async function ListingsPage() {
  const [initialListings, investmentSummary, complexes] = await Promise.all([
    getFilteredListings({ limit: PAGE_SIZE, offset: 0 }),
    getInvestmentSummary(),
    getComplexes(),
  ]);

  return (
    <div className="flex min-h-screen">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar title="Зар мэдээлэл" />
        <main className="flex flex-col gap-5 bg-surface-page p-8">
          <div>
            <h1 className="text-xl font-semibold text-ink-primary">Бүх зар</h1>
            <p className="mt-1 text-sm text-ink-secondary">
              Байршил, хотхон, төрөл болон үнээр шүүж, зах зээлийн харьцуулалттай танилцана уу.
            </p>
          </div>
          <RecentListings
            initialListings={initialListings}
            districts={investmentSummary.map((row) => row.district)}
            complexes={complexes}
            pageSize={PAGE_SIZE}
            paginated
          />
        </main>
      </div>
    </div>
  );
}
