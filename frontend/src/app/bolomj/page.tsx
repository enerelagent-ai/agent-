import { AffordabilityExplorer } from "@/components/AffordabilityExplorer";
import { ComplexSiteHeader } from "@/components/ComplexSiteHeader";
import { getPublicAffordability } from "@/lib/api";

export default async function AffordabilityPage() {
  const data = await getPublicAffordability();
  return <div className="min-h-screen bg-[#f3f5f7]">
    <ComplexSiteHeader />
    <main className="mx-auto max-w-[1280px] px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-7 max-w-3xl">
        <p className="text-xs font-extrabold uppercase tracking-[0.18em] text-[#e85520]">Орон сууцны боломж</p>
        <h1 className="mt-2 text-3xl font-black tracking-tight text-[#20334b] sm:text-4xl">Танд ямар байр тохирох вэ?</h1>
        <p className="mt-3 text-sm leading-6 text-slate-600">Хадгаламжийн хэмжээгээр 30%-ийн урьдчилгаа, зээлийн дээд хэмжээ болон талбайн шаардлагыг зэрэг тооцож одоогийн зах зээлээс боломжит хүрээг харуулна.</p>
      </div>
      <AffordabilityExplorer data={data} />
      <section className="mt-7 rounded-xl border border-amber-200 bg-amber-50 p-4 text-xs leading-5 text-amber-950">
        <strong>Анхаарах нь:</strong> Энэ нь урьдчилсан мэдээллийн тооцоо бөгөөд зээлийн зөвшөөрөл, санхүүгийн зөвлөгөө биш. Эцсийн шалгуур, орлого ба зээлжих чадварыг банк өөрөө шийднэ. Өгөгдөл: {data.data_as_of} · Эх сурвалж: hotkhon.mn public мэдээлэл.
      </section>
    </main>
  </div>;
}
