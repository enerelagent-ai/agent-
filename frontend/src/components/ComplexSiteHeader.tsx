import { Building2, Calculator, Home, Map, Search } from "lucide-react";
import Link from "next/link";

export function ComplexSiteHeader() {
  return (
    <header className="border-b border-slate-200 bg-[#101b2b] text-white">
      <div className="mx-auto flex max-w-[1280px] flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6 lg:px-8">
        <Link href="/" className="flex items-center gap-2 text-lg font-black">
          <span className="grid h-9 w-9 place-items-center rounded-lg bg-[#ff6b35]"><Building2 className="h-5 w-5" /></span>
          Enerel<span className="text-[#ff8a5c]">Market</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-1 text-sm font-bold text-slate-200">
          <Link href="/sale" className="flex min-h-10 items-center gap-1.5 rounded-md px-3 hover:bg-white/10"><Home className="h-4 w-4" />Зарууд</Link>
          <Link href="/complexes" className="flex min-h-10 items-center gap-1.5 rounded-md px-3 hover:bg-white/10"><Search className="h-4 w-4" />Хотхонууд</Link>
          <Link href="/complexes/map" className="flex min-h-10 items-center gap-1.5 rounded-md px-3 hover:bg-white/10"><Map className="h-4 w-4" />Газрын зураг</Link>
          <Link href="/bolomj" className="flex min-h-10 items-center gap-1.5 rounded-md px-3 hover:bg-white/10"><Calculator className="h-4 w-4" />Боломж</Link>
        </nav>
      </div>
    </header>
  );
}
