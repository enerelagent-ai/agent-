"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { Banknote, Building2, Home, Landmark } from "lucide-react";

import type { PublicAffordabilitySnapshot } from "@/lib/api";

const fmt = new Intl.NumberFormat("mn-MN");

export function AffordabilityExplorer({ data }: { data: PublicAffordabilitySnapshot }) {
  const [deposit, setDeposit] = useState(60);
  const [district, setDistrict] = useState("");
  const result = useMemo(() => {
    const down = Math.max(0, deposit) * 1_000_000;
    const byDeposit = down / data.rules.min_downpayment_ratio;
    const byCap = down + data.rules.loan_cap_mnt;
    const ceiling = Math.min(byDeposit, byCap);
    const selected = data.listings.filter((item) => !district || data.districts[item[2]] === district);
    const areaFit = selected.filter((item) => item[0] <= data.rules.max_area_sqm);
    const affordable = areaFit.filter((item) => item[1] * 1_000_000 <= ceiling);
    const perDistrict = data.districts.map((name, index) => ({
      name,
      count: affordable.filter((item) => item[2] === index).length,
    })).filter((item) => item.count > 0).sort((a, b) => b.count - a.count);
    return { selected: selected.length, areaFit: areaFit.length, affordable: affordable.length, ceiling, byDeposit, byCap, perDistrict };
  }, [data, deposit, district]);

  return (
    <div className="grid gap-6 lg:grid-cols-[360px_1fr]">
      <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 shadow-sm lg:sticky lg:top-5">
        <label htmlFor="deposit" className="text-sm font-black text-[#20334b]">Таны хадгаламж (сая ₮)</label>
        <div className="mt-3 flex items-center gap-2 rounded-xl border border-slate-300 px-3 focus-within:border-[#e85520]">
          <Banknote className="h-5 w-5 text-slate-400" />
          <input id="deposit" type="number" min="0" max="400" value={deposit} onChange={(event) => setDeposit(Math.max(0, Number(event.target.value) || 0))} className="min-h-12 w-full bg-transparent text-lg font-black outline-none" />
          <span className="whitespace-nowrap text-sm text-slate-500">сая ₮</span>
        </div>
        <input aria-label="Хадгаламжийн хэмжээ" type="range" min="0" max="400" step="5" value={Math.min(400, deposit)} onChange={(event) => setDeposit(Number(event.target.value))} className="mt-4 w-full accent-[#e85520]" />
        <p className="mt-6 text-sm font-black text-[#20334b]">Дүүрэг</p>
        <div className="mt-3 flex flex-wrap gap-2">
          {["", ...data.districts].map((name) => <button key={name || "all"} type="button" onClick={() => setDistrict(name)} className={`min-h-10 rounded-full border px-3 text-xs font-bold ${district === name ? "border-[#e85520] bg-[#fff1eb] text-[#c54214]" : "border-slate-200 text-slate-600 hover:border-slate-400"}`}>{name || "Бүгд"}</button>)}
        </div>
        <div className="mt-6 rounded-xl bg-slate-50 p-4 text-xs leading-5 text-slate-600">
          <strong className="text-slate-900">Тооцооны үндэслэл</strong><br />Урьдчилгаа {Math.round(data.rules.min_downpayment_ratio * 100)}% · зээл {fmt.format(data.rules.loan_cap_mnt / 1_000_000)} сая ₮ хүртэл · талбай {data.rules.max_area_sqm} м² хүртэл.
        </div>
      </aside>

      <div>
        <div className="grid gap-3 sm:grid-cols-3">
          <Stat icon={Home} label={district ? `${district} дүүргийн зар` : "Нийт идэвхтэй зар"} value={fmt.format(result.selected)} />
          <Stat icon={Building2} label={`${data.rules.max_area_sqm} м² шаардлага хангасан`} value={fmt.format(result.areaFit)} />
          <Stat icon={Landmark} label="Таны нөхцөлд багтсан" value={fmt.format(result.affordable)} accent />
        </div>
        <section className="mt-5 rounded-2xl bg-[#20334b] p-6 text-white">
          <p className="text-sm text-slate-300">Байрны үнийн дээд хязгаар</p>
          <p className="mt-1 text-4xl font-black">≈ {fmt.format(Math.round(result.ceiling / 1_000_000))} сая ₮</p>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-300">{result.byDeposit < result.byCap ? "Одоогоор 30%-ийн урьдчилгааны шаардлага таны үнийн хязгаарыг тогтоож байна." : "Одоогоор 150 сая ₮-ийн зээлийн дээд хэмжээ таны үнийн хязгаарыг тогтоож байна."} Энэ хүрээнд нийт зарын {result.selected ? (result.affordable / result.selected * 100).toFixed(result.affordable / result.selected < .01 ? 1 : 0) : 0}% багтлаа.</p>
        </section>
        <section className="mt-5 rounded-2xl border border-slate-200 bg-white p-5">
          <h2 className="text-lg font-black text-[#20334b]">Дүүргээр харах</h2>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {result.perDistrict.map((item) => <Link key={item.name} href={`/complexes?district=${encodeURIComponent(item.name)}`} className="flex items-center justify-between rounded-xl border border-slate-200 p-4 hover:border-[#e85520] hover:bg-[#fffaf7]"><span className="font-bold text-slate-700">{item.name}</span><span className="text-xl font-black text-[#e85520]">{fmt.format(item.count)}</span></Link>)}
          </div>
          {!result.affordable && <p className="mt-4 rounded-xl bg-amber-50 p-4 text-sm text-amber-900">Одоогийн нөхцөлд тохирох зар олдсонгүй. Хадгаламжийн хэмжээг нэмээд дахин үзнэ үү.</p>}
        </section>
      </div>
    </div>
  );
}

function Stat({ icon: Icon, label, value, accent = false }: { icon: typeof Home; label: string; value: string; accent?: boolean }) {
  return <div className={`rounded-2xl border p-5 ${accent ? "border-[#ffb292] bg-[#fff1eb]" : "border-slate-200 bg-white"}`}><Icon className={`h-5 w-5 ${accent ? "text-[#e85520]" : "text-slate-400"}`} /><p className="mt-4 text-2xl font-black text-[#20334b]">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>;
}

