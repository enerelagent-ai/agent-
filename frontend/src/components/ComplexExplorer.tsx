"use client";

import { Building2, Map, MapPin, Search, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useMemo, useState } from "react";

import type { PublicComplexSummary } from "@/lib/api";
import { ComplexMap } from "./ComplexMap";

function pricePerSqm(value: number | null): string {
  return value === null ? "Үнэ хүрэлцэхгүй" : `${(value / 1_000_000).toFixed(2)} сая ₮/м²`;
}

export function ComplexExplorer({
  complexes,
  mode,
  contours = {},
}: {
  complexes: PublicComplexSummary[];
  mode: "list" | "map";
  contours?: Record<string, number[][][]>;
}) {
  const [query, setQuery] = useState("");
  const [district, setDistrict] = useState("");
  const [contourOnly, setContourOnly] = useState(false);
  const districts = [...new Set(complexes.map((item) => item.district).filter(Boolean))] as string[];
  const filtered = useMemo(() => {
    const normalized = query.trim().toLocaleLowerCase("mn-MN");
    return complexes.filter((item) =>
      (!district || item.district === district) &&
      (!contourOnly || item.has_contour) &&
      (!normalized || item.name.toLocaleLowerCase("mn-MN").includes(normalized)),
    );
  }, [complexes, contourOnly, district, query]);

  return (
    <>
      <div className="grid gap-3 rounded-xl border border-slate-200 bg-white p-4 shadow-sm md:grid-cols-[minmax(0,1fr)_220px_auto]">
        <label className="relative block">
          <Search className="absolute left-3 top-3.5 h-4 w-4 text-slate-400" />
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Хотхоны нэрээр хайх" className="min-h-11 w-full rounded-lg border border-slate-300 pl-10 pr-3 text-sm outline-none focus:border-[#ff6b35]" />
        </label>
        <select aria-label="Дүүргээр шүүх" value={district} onChange={(event) => setDistrict(event.target.value)} className="min-h-11 rounded-lg border border-slate-300 bg-white px-3 text-sm outline-none focus:border-[#ff6b35]">
          <option value="">Бүх дүүрэг</option>
          {districts.map((item) => <option key={item}>{item}</option>)}
        </select>
        <label className="flex min-h-11 items-center gap-2 rounded-lg border border-slate-200 px-3 text-sm font-semibold text-slate-600">
          <input type="checkbox" checked={contourOnly} onChange={(event) => setContourOnly(event.target.checked)} />
          Зөвхөн контуртай
        </label>
      </div>

      <div className="my-5 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-slate-600"><strong className="text-slate-950">{filtered.length}</strong> public мэдээлэлтэй хотхон</p>
        <div className="flex rounded-lg border border-slate-200 bg-white p-1 text-sm font-bold">
          <Link href="/complexes" className={`flex min-h-9 items-center gap-1.5 rounded-md px-3 ${mode === "list" ? "bg-[#20334b] text-white" : "text-slate-600"}`}><Building2 className="h-4 w-4" />Жагсаалт</Link>
          <Link href="/complexes/map" className={`flex min-h-9 items-center gap-1.5 rounded-md px-3 ${mode === "map" ? "bg-[#20334b] text-white" : "text-slate-600"}`}><Map className="h-4 w-4" />Газрын зураг</Link>
        </div>
      </div>

      {contourOnly && filtered.length === 0 ? (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-6 text-sm leading-6 text-amber-900">
          Манай verified registry-д polygon/contour одоогоор хадгалагдаагүй. Контурын pipeline нэмэгдэхэд энэ шүүлтүүр автоматаар ажиллана.
        </div>
      ) : mode === "map" ? (
        <>
          <ComplexMap complexes={filtered} contours={contours} />
          <p className="mt-3 text-xs leading-5 text-slate-500">Тойргийн хэмжээ нь идэвхтэй зарын тоо. Өнгө нь медиан зарлах ₮/м² үнэ. Координат нь баталгаатай заруудын төв цэг бөгөөд хотхоны албан ёсны хил биш.</p>
        </>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {filtered.map((item) => (
            <Link key={item.source_slug} href={`/complexes/${item.source_slug}`} className="group rounded-xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-[#ff6b35] hover:shadow-md">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h2 className="font-black text-slate-950 group-hover:text-[#e85520]">{item.name}</h2>
                  <p className="mt-1 flex items-center gap-1 text-xs text-slate-500"><MapPin className="h-3.5 w-3.5" />{item.district ?? "Байршил тодорхойгүй"}</p>
                </div>
                <ShieldCheck className="h-5 w-5 shrink-0 text-emerald-600" aria-label="Баталгаатай" />
              </div>
              <p className="mt-5 text-xl font-black text-[#20334b]">{pricePerSqm(item.median_sale_price_per_sqm)}</p>
              <div className="mt-4 grid grid-cols-2 gap-2 border-t border-slate-100 pt-4 text-xs">
                <div><strong className="block text-sm text-slate-900">{item.active_listings}</strong><span className="text-slate-500">идэвхтэй зар</span></div>
                <div className="text-right"><strong className="block text-sm text-slate-900">{item.has_contour ? "Контур" : "Цэг"}</strong><span className="text-slate-500">байршлын төрөл</span></div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </>
  );
}
