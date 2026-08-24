import { ComplexExplorer } from "@/components/ComplexExplorer";
import { ComplexSiteHeader } from "@/components/ComplexSiteHeader";
import { getPublicComplexMap } from "@/lib/api";

export default async function ComplexMapPage() {
  const data = await getPublicComplexMap();
  return (
    <div className="min-h-screen bg-[#f3f5f7]">
      <ComplexSiteHeader />
      <main className="mx-auto max-w-[1280px] px-4 py-7 sm:px-6 lg:px-8">
        <h1 className="text-3xl font-black tracking-tight text-[#20334b]">Хотхоны интерактив газрын зураг</h1>
        <p className="mt-2 text-sm text-slate-600">Дүүрэг, нэр, байршлын төрлөөр шүүж хотхоны analytics руу шууд орно.</p>
        <div className="mt-6"><ComplexExplorer complexes={data.profiles} contours={data.contours} mode="map" /></div>
      </main>
    </div>
  );
}
