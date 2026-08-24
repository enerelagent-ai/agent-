import { ComplexExplorer } from "@/components/ComplexExplorer";
import { ComplexSiteHeader } from "@/components/ComplexSiteHeader";
import { getComplexIntelligence } from "@/lib/api";

export default async function ComplexDirectoryPage() {
  const complexes = await getComplexIntelligence();
  const activeListings = complexes.reduce((sum, item) => sum + item.active_listings, 0);

  return (
    <div className="min-h-screen bg-[#f3f5f7]">
      <ComplexSiteHeader />
      <main className="mx-auto max-w-[1280px] px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-7 max-w-3xl">
          <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#e85520]">Хотхоны intelligence</p>
          <h1 className="mt-2 text-3xl font-black tracking-tight text-[#20334b] sm:text-4xl">Улаанбаатарын баталгаатай хотхонууд</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">Хотхон бүрийн идэвхтэй зар, медиан м² үнэ, үнийн хүрээг өдөр тутмын зарын өгөгдлөөс харьцуулна.</p>
          <div className="mt-5 flex flex-wrap gap-6 text-sm text-slate-500"><span><strong className="text-xl text-slate-950">{complexes.length}</strong> хотхон</span><span><strong className="text-xl text-slate-950">{activeListings}</strong> баталгаатай зар</span></div>
        </div>
        <ComplexExplorer complexes={complexes} mode="list" />
      </main>
    </div>
  );
}
