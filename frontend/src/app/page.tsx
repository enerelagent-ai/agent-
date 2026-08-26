import { ArrowRight, BarChart3, Building2, Calculator, Home, Map, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { AffordabilityExplorer } from "@/components/AffordabilityExplorer";
import { ComplexSiteHeader } from "@/components/ComplexSiteHeader";
import { MarketplaceListingCard } from "@/components/MarketplaceListingCard";
import { getPublicComplexes, getTodaysOpportunity, searchMarketplaceListings } from "@/lib/api";
import { getAvailableAffordability } from "@/lib/publicAffordability";

export default async function HomePage() {
  const [sale, rent, complexes, affordability, opportunity] = await Promise.all([
    searchMarketplaceListings({ listingType: "sale", limit: 6 }).catch(() => null),
    searchMarketplaceListings({ listingType: "rent", limit: 3 }).catch(() => null),
    getPublicComplexes().catch(() => []),
    getAvailableAffordability().catch(() => null),
    getTodaysOpportunity().catch(() => null),
  ]);
  const activeComplexListings = complexes.reduce((sum, item) => sum + item.active_listings, 0);
  const contourCount = complexes.filter((item) => item.has_contour).length;
  const featuredComplexes = [...complexes].sort((a, b) => b.active_listings - a.active_listings).slice(0, 6);

  return <div className="min-h-screen bg-[#f3f5f7] text-slate-900">
    <ComplexSiteHeader />
    <main>
      <section className="overflow-hidden bg-[#101b2b] text-white">
        <div className="mx-auto grid max-w-[1280px] gap-10 px-4 py-12 sm:px-6 lg:grid-cols-[1.15fr_.85fr] lg:px-8 lg:py-16">
          <div>
            <p className="text-xs font-black uppercase tracking-[.2em] text-[#ff8a5c]">Зар · Хотхон · Анализ · Боломж</p>
            <h1 className="mt-4 max-w-3xl text-4xl font-black leading-tight sm:text-5xl">Орон сууц хайхаас эхлээд хөрөнгө оруулалтаа тооцох хүртэл нэг дор.</h1>
            <p className="mt-5 max-w-2xl text-base leading-7 text-slate-300">Худалдах, түрээслэх заруудыг хотхон болон газрын зурагтай нь харьцуулж, зах зээлийн өгөгдөлд тулгуурлан боломжит үнийн хүрээгээ тооцоорой.</p>
            <div className="mt-7 flex flex-wrap gap-3"><Link href="/sale" className="inline-flex min-h-12 items-center gap-2 rounded-lg bg-[#ff6b35] px-5 py-3 text-sm font-black hover:bg-[#ed5b29]"><Search className="h-4 w-4" />Зар хайх</Link><Link href="#affordability" className="inline-flex min-h-12 items-center gap-2 rounded-lg border border-white/20 bg-white/10 px-5 py-3 text-sm font-black hover:bg-white/15"><Calculator className="h-4 w-4" />Боломжоо тооцох</Link></div>
          </div>
          <div className="grid grid-cols-2 gap-3 self-end"><HeroStat value={sale?.items.length ? "20,000+" : "—"} label="идэвхтэй зарын сан" icon={Home} /><HeroStat value={complexes.length.toLocaleString("mn-MN")} label="public хотхон" icon={Building2} /><HeroStat value={contourCount.toLocaleString("mn-MN")} label="контуртай хотхон" icon={Map} /><HeroStat value={activeComplexListings.toLocaleString("mn-MN")} label="хотхонд холбогдсон зар" icon={BarChart3} /></div>
        </div>
      </section>

      <div className="mx-auto max-w-[1280px] px-4 py-9 sm:px-6 lg:px-8">
        <section className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4"><JourneyCard href="/sale" icon={Home} title="Худалдах зар" text="Үнэ, дүүрэг, өрөө, хотхоноор шүүнэ" /><JourneyCard href="/rent" icon={Search} title="Түрээсийн зар" text="Түрээсийн саналыг тусад нь харьцуулна" /><JourneyCard href="/complexes" icon={Building2} title="Хотхонууд" text="м² үнэ, зарын тоо, байршлын мэдээлэл" /><JourneyCard href="/complexes/map" icon={Map} title="Газрын зураг" text="Дүүрэг болон контураар интерактив хайна" /></section>

        {opportunity && <section className="mt-9 overflow-hidden rounded-2xl border border-emerald-200 bg-emerald-50 p-6 sm:flex sm:items-center sm:justify-between sm:gap-8"><div><p className="text-xs font-black uppercase tracking-wider text-emerald-700">Өнөөдрийн зах зээлийн тойм</p><h2 className="mt-2 text-2xl font-black text-[#20334b]">{opportunity.district}: өгөөж {opportunity.gross_rental_yield_pct.toFixed(1)}%</h2><p className="mt-2 text-sm text-slate-600">{opportunity.n_sale} худалдах, {opportunity.n_rent} түрээсийн зарын харьцуулалт · {opportunity.confidence_tier} итгэлцэл</p></div><Link href="/sale#market-analysis" className="mt-4 inline-flex shrink-0 items-center gap-2 text-sm font-black text-emerald-800 sm:mt-0">Дэлгэрэнгүй анализ <ArrowRight className="h-4 w-4" /></Link></section>}

        <SectionHead eyebrow="Marketplace" title="Шинээр нэмэгдсэн худалдах зарууд" href="/sale" />
        {sale?.items.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{sale.items.map((item) => <MarketplaceListingCard key={item.id} listing={item} />)}</div> : <Unavailable />}

        <section className="mt-14" id="complexes"><SectionHead eyebrow="Хотхоны intelligence" title="Идэвхтэй хотхонууд" href="/complexes" compact /><div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{featuredComplexes.map((item) => <Link key={item.source_slug} href={`/complexes/${item.source_slug}`} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-[#ff6b35] hover:shadow-md"><div className="flex items-start justify-between gap-3"><div><h3 className="font-black group-hover:text-[#e85520]">{item.name}</h3><p className="mt-1 text-xs text-slate-500">{item.district ?? "Байршил тодорхойгүй"}</p></div><ShieldCheck className="h-5 w-5 text-emerald-600" /></div><p className="mt-5 text-xl font-black text-[#20334b]">{item.median_sale_price_per_sqm === null ? "Үнэ хүрэлцэхгүй" : `${(item.median_sale_price_per_sqm / 1_000_000).toFixed(2)} сая ₮/м²`}</p><p className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-500"><strong className="text-slate-900">{item.active_listings}</strong> идэвхтэй зар · {item.has_contour ? "контуртай" : "цэгэн байршил"}</p></Link>)}</div></section>

        <section className="mt-14 scroll-mt-6" id="affordability"><div className="mb-6 max-w-3xl"><p className="text-xs font-black uppercase tracking-[.18em] text-[#e85520]">Орон сууцны боломж</p><h2 className="mt-2 text-3xl font-black text-[#20334b]">Танд ямар байр тохирох вэ?</h2><p className="mt-3 text-sm leading-6 text-slate-600">Хадгаламж, урьдчилгаа, зээлийн хязгаар болон талбайн шаардлагыг одоогийн зарын сантай зэрэг харьцуулна.</p></div>{affordability ? <AffordabilityExplorer data={affordability} /> : <Unavailable text="Боломжийн шинэ snapshot импортлогдсоны дараа тооцоолуур энд харагдана." />}</section>

        <SectionHead eyebrow="Түрээс" title="Шинэ түрээсийн зарууд" href="/rent" />
        {rent?.items.length ? <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">{rent.items.map((item) => <MarketplaceListingCard key={item.id} listing={item} />)}</div> : <Unavailable />}
      </div>
    </main>
    <footer className="mt-8 border-t border-slate-200 bg-white"><div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-3 px-4 py-7 text-xs text-slate-500 sm:px-6 lg:px-8"><span>Enerel Market · Зар ба зах зээлийн мэдээлэл</span><span>Зарлах үнэ нь бодит хэлцлийн үнэ биш.</span></div></footer>
  </div>;
}

function HeroStat({ value, label, icon: Icon }: { value: string; label: string; icon: typeof Home }) { return <div className="rounded-2xl border border-white/10 bg-white/[.07] p-4"><Icon className="h-5 w-5 text-[#ff8a5c]" /><p className="mt-3 text-2xl font-black">{value}</p><p className="mt-1 text-xs text-slate-400">{label}</p></div>; }
function JourneyCard({ href, icon: Icon, title, text }: { href: string; icon: typeof Home; title: string; text: string }) { return <Link href={href} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-[#ff6b35]"><span className="grid h-10 w-10 place-items-center rounded-xl bg-[#fff1eb] text-[#e85520]"><Icon className="h-5 w-5" /></span><h2 className="mt-4 font-black text-[#20334b] group-hover:text-[#e85520]">{title}</h2><p className="mt-1 text-xs leading-5 text-slate-500">{text}</p></Link>; }
function SectionHead({ eyebrow, title, href, compact = false }: { eyebrow: string; title: string; href: string; compact?: boolean }) { return <div className={`${compact ? "mb-5" : "mb-5 mt-14"} flex items-end justify-between gap-4`}><div><p className="text-xs font-black uppercase tracking-[.18em] text-[#e85520]">{eyebrow}</p><h2 className="mt-2 text-2xl font-black text-[#20334b] sm:text-3xl">{title}</h2></div><Link href={href} className="flex shrink-0 items-center gap-1 text-sm font-black text-[#e85520]">Бүгдийг харах <ArrowRight className="h-4 w-4" /></Link></div>; }
function Unavailable({ text = "Мэдээллийг түр ачаалж чадсангүй." }: { text?: string }) { return <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">{text}</div>; }
