import { ArrowLeft, BadgeCheck, MapPin } from "lucide-react";
import Link from "next/link";
import { notFound } from "next/navigation";

import { ComplexSiteHeader } from "@/components/ComplexSiteHeader";
import { MarketplaceListingCard } from "@/components/MarketplaceListingCard";
import { getComplexIntelligenceDetail, getPublicComplex, searchMarketplaceListings, type PublicComplexSummary } from "@/lib/api";
import { formatMnt } from "@/lib/format";

export default async function ComplexDetailPage({ params }: { params: { id: string } }) {
  const id = Number(params.id);
  if (!Number.isInteger(id) || id < 1) {
    try {
      const profile = await getPublicComplex(params.id);
      return <PublicProfile profile={profile} />;
    } catch {
      notFound();
    }
  }
  let complex;
  try {
    complex = await getComplexIntelligenceDetail(id);
  } catch {
    notFound();
  }
  const [sale, rent] = await Promise.all([
    searchMarketplaceListings({ listingType: "sale", complexId: id, limit: 6 }),
    searchMarketplaceListings({ listingType: "rent", complexId: id, limit: 6 }),
  ]);

  return (
    <div className="min-h-screen bg-[#f3f5f7]">
      <ComplexSiteHeader />
      <main className="mx-auto max-w-[1280px] px-4 py-7 sm:px-6 lg:px-8">
        <Link href="/complexes" className="inline-flex items-center gap-1 text-sm font-bold text-slate-500 hover:text-[#e85520]"><ArrowLeft className="h-4 w-4" />Бүх хотхон</Link>
        <section className="mt-5 overflow-hidden rounded-2xl bg-[#20334b] p-6 text-white sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold text-emerald-300"><BadgeCheck className="h-4 w-4" />Баталгаатай хотхон</div>
              <h1 className="mt-2 text-3xl font-black sm:text-4xl">{complex.name}</h1>
              <p className="mt-2 flex items-center gap-1 text-sm text-slate-300"><MapPin className="h-4 w-4" />{complex.district ?? "Байршил тодорхойгүй"}</p>
            </div>
            <div className="rounded-xl bg-white/10 px-5 py-4 text-right"><p className="text-xs text-slate-300">Медиан зарлах үнэ / м²</p><p className="mt-1 text-2xl font-black">{complex.median_sale_price_per_sqm === null ? "—" : formatMnt(complex.median_sale_price_per_sqm)}</p></div>
          </div>
          <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-5">
            <Metric label="Идэвхтэй зар" value={String(complex.active_listings)} />
            <Metric label="Худалдах" value={String(complex.sale_listings)} />
            <Metric label="Түрээс" value={String(complex.rent_listings)} />
            <Metric label="Медиан худалдах" value={complex.median_sale_price === null ? "—" : formatMnt(complex.median_sale_price)} />
            <Metric label="Медиан түрээс" value={complex.median_rent_price === null ? "—" : formatMnt(complex.median_rent_price)} />
          </div>
        </section>

        <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5">
          <h2 className="font-black text-slate-950">Үнийн хүрээ</h2>
          <div className="mt-4 grid gap-4 sm:grid-cols-3"><MetricLight label="Хамгийн бага ₮/м²" value={complex.min_sale_price_per_sqm === null ? "—" : formatMnt(complex.min_sale_price_per_sqm)} /><MetricLight label="Медиан ₮/м²" value={complex.median_sale_price_per_sqm === null ? "—" : formatMnt(complex.median_sale_price_per_sqm)} /><MetricLight label="Хамгийн их ₮/м²" value={complex.max_sale_price_per_sqm === null ? "—" : formatMnt(complex.max_sale_price_per_sqm)} /></div>
          <p className="mt-4 text-xs leading-5 text-slate-500">Эдгээр нь идэвхтэй, давхардалгүй, баталгаатай зарын зарлах үнэ бөгөөд бодит хэлцлийн үнэ биш.</p>
        </section>

        <ListingSection title="Худалдах зарууд" href={`/sale`} items={sale.items} />
        <ListingSection title="Түрээсийн зарууд" href={`/rent`} items={rent.items} />
      </main>
    </div>
  );
}

function PublicProfile({ profile }: { profile: PublicComplexSummary }) {
  return (
    <div className="min-h-screen bg-[#f3f5f7]">
      <ComplexSiteHeader />
      <main className="mx-auto max-w-[1000px] px-4 py-7 sm:px-6 lg:px-8">
        <Link href="/complexes" className="inline-flex items-center gap-1 text-sm font-bold text-slate-500 hover:text-[#e85520]"><ArrowLeft className="h-4 w-4" />Бүх хотхон</Link>
        {profile.photo_url && <div className="mt-5 aspect-[16/7] overflow-hidden rounded-2xl bg-slate-200"><img src={profile.photo_url} alt={`${profile.name} гадна зураг`} className="h-full w-full object-cover" /></div>}
        <section className="mt-5 overflow-hidden rounded-2xl bg-[#20334b] p-6 text-white sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div><p className="text-xs font-bold uppercase tracking-wider text-[#ff9a73]">Хотхоны public тойм · {profile.district}</p><h1 className="mt-2 text-3xl font-black sm:text-4xl">{profile.name}</h1><p className="mt-2 flex items-center gap-1 text-sm text-slate-300"><MapPin className="h-4 w-4" />{profile.has_contour ? "Хэмжсэн контуртай" : "Ойролцоо цэгэн байршил"}</p></div>
            <div className="rounded-xl bg-white/10 px-5 py-4 text-right"><p className="text-xs text-slate-300">Медиан зарлах үнэ / м²</p><p className="mt-1 text-2xl font-black">{profile.median_sale_price_per_sqm === null ? "—" : formatMnt(profile.median_sale_price_per_sqm)}</p></div>
          </div>
          <div className="mt-7 grid grid-cols-2 gap-3 sm:grid-cols-3"><Metric label="Идэвхтэй зар" value={String(profile.active_listings)} /><Metric label="Мэдээллийн огноо" value={profile.data_as_of} /><Metric label="Байршлын төрөл" value={profile.location_kind ?? "point"} /></div>
        </section>
        <section className="mt-6 rounded-xl border border-slate-200 bg-white p-5 text-sm leading-6 text-slate-600">
          <h2 className="font-black text-slate-950">Мэдээллийн тайлбар</h2>
          <p className="mt-2">Энд харагдах тоо нь зарлах үнэ бөгөөд бодит хэлцлийн үнэ биш.</p>
          <p className="mt-3 text-xs font-semibold text-slate-500">Мэдээлэл шинэчлэгдсэн: {profile.data_as_of}</p>
        </section>
      </main>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) { return <div className="rounded-lg bg-white/10 p-3"><p className="text-[11px] text-slate-300">{label}</p><p className="mt-1 font-black">{value}</p></div>; }
function MetricLight({ label, value }: { label: string; value: string }) { return <div><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-lg font-black text-[#20334b]">{value}</p></div>; }
function ListingSection({ title, href, items }: { title: string; href: string; items: Awaited<ReturnType<typeof searchMarketplaceListings>>["items"] }) {
  return <section className="mt-8"><div className="mb-4 flex items-center justify-between"><h2 className="text-xl font-black text-[#20334b]">{title}</h2><Link href={href} className="text-sm font-bold text-[#e85520]">Бүгдийг харах →</Link></div>{items.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{items.map((item) => <MarketplaceListingCard key={item.id} listing={item} />)}</div> : <div className="rounded-xl border border-slate-200 bg-white p-6 text-sm text-slate-500">Одоогоор идэвхтэй зар алга.</div>}</section>;
}
