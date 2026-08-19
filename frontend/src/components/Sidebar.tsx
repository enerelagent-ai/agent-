"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Bell,
  Building2,
  FileBarChart,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  Store,
  PiggyBank,
  Settings,
  ShieldQuestion,
  TrendingUp,
} from "lucide-react";

interface NavItem {
  label: string;
  icon: typeof LayoutDashboard;
  href: string | null;
}

const NAV_ITEMS: NavItem[] = [
  { label: "Хяналтын самбар", icon: LayoutDashboard, href: "/dashboard" },
  { label: "Зарын зах", icon: Store, href: "/market" },
  { label: "Зар мэдээлэл", icon: ListChecks, href: "/listings" },
  { label: "Зах зээлийн тойм", icon: TrendingUp, href: null },
  { label: "Хөрөнгө оруулалтын өгөөж", icon: PiggyBank, href: "/calculator" },
  { label: "Түрээсийн өгөөж", icon: KeyRound, href: null },
  { label: "Дүрслэл & Тайлан", icon: FileBarChart, href: null },
  { label: "Мэдэгдэл", icon: Bell, href: "/notifications" },
  { label: "Хотхон шалгах", icon: ShieldQuestion, href: "/complex-review" },
  { label: "Тохиргоо", icon: Settings, href: null },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="flex w-64 shrink-0 flex-col bg-[#111a3d] text-white">
      <div className="flex items-center gap-2.5 px-5 py-6">
        <Building2 className="h-6 w-6 shrink-0 text-series-1" aria-hidden />
        <div className="min-w-0">
          <div className="text-sm font-semibold leading-tight">Улаанбаатар</div>
          <div className="text-sm font-semibold leading-tight">Үл хөдлөх хөрөнгө</div>
          <div className="mt-0.5 text-xs text-white/50">Аналитик платформ</div>
        </div>
      </div>

      <nav className="flex-1 space-y-1 px-3 pt-2">
        {NAV_ITEMS.map(({ label, icon: Icon, href }) => {
          const active = href !== null && pathname.startsWith(href);
          return href ? (
            <Link
              key={label}
              href={href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium text-white transition-colors hover:bg-white/10 ${
                active ? "bg-white/10" : ""
              }`}
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              {label}
            </Link>
          ) : (
            <span
              key={label}
              title="Тун удахгүй"
              aria-disabled
              className="flex cursor-not-allowed items-center gap-3 rounded-lg px-3 py-2.5 text-sm text-white/35"
            >
              <Icon className="h-4 w-4 shrink-0" aria-hidden />
              {label}
            </span>
          );
        })}
      </nav>

      <div className="px-3 pb-5 text-xs text-white/30">V1.5 — Хувилбар 1.5.0</div>
    </aside>
  );
}
