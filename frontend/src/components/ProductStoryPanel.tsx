import { Building2 } from "lucide-react";

// Left-side panel for the login page only -- static, no data fetching (the
// visitor isn't authenticated yet, so there's nothing real to show besides
// a status line). Deliberately no invented metrics ("AI Investment Score",
// "Expected Appreciation" etc.) since none of that is backed by a real
// calculation; the one dynamic-feeling element is a plain status sentence,
// not a number.
export function ProductStoryPanel() {
  return (
    <div className="relative flex h-full flex-col justify-between gap-8 overflow-hidden bg-[#111a3d] px-8 py-8 text-white sm:px-10 sm:py-10 lg:px-14 lg:py-14">
      {/* Soft gradient + a faint abstract grid standing in for "geographic
          grid" -- not a real map, so there's no fake geodata to maintain. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_15%_20%,rgba(42,120,214,0.25),transparent_45%),radial-gradient(circle_at_85%_80%,rgba(42,120,214,0.15),transparent_50%)]"
      />
      <svg
        aria-hidden
        className="pointer-events-none absolute inset-0 h-full w-full opacity-[0.07]"
        preserveAspectRatio="none"
      >
        <defs>
          <pattern id="grid" width="48" height="48" patternUnits="userSpaceOnUse">
            <path d="M 48 0 L 0 0 0 48" fill="none" stroke="white" strokeWidth="1" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid)" />
      </svg>
      {/* A handful of restrained "pin" points, evoking scattered listings
          across the city without claiming to be a real, navigable map. */}
      <div aria-hidden className="pointer-events-none absolute inset-0 hidden lg:block">
        {[
          { top: "22%", left: "28%" },
          { top: "38%", left: "62%" },
          { top: "58%", left: "40%" },
          { top: "68%", left: "72%" },
          { top: "48%", left: "18%" },
        ].map((pos, i) => (
          <span
            key={i}
            className="absolute h-1.5 w-1.5 rounded-full bg-series-1 motion-safe:animate-pulse"
            style={{ ...pos, animationDuration: "3s", animationDelay: `${i * 0.4}s` }}
          />
        ))}
      </div>

      <div className="relative flex items-center gap-2.5">
        <Building2 className="h-6 w-6 shrink-0 text-series-1" aria-hidden />
        <div className="min-w-0 leading-tight">
          <div className="text-sm font-semibold">Улаанбаатар Үл хөдлөх хөрөнгө</div>
          <div className="text-xs text-white/50">Аналитик платформ</div>
        </div>
      </div>

      <div className="relative max-w-lg">
        <h2 className="text-2xl font-semibold leading-tight sm:text-3xl lg:text-4xl">
          Улаанбаатарын үл хөдлөх хөрөнгийн зах зээлийг
          <br className="hidden sm:block" /> өгөгдөл, шинжилгээгээр ойлго.
        </h2>
        {/* Kept compact on phones per spec -- only the logo + headline show
            there; this and the status line below are non-essential detail. */}
        <p className="mt-5 hidden max-w-md text-base leading-relaxed text-white/70 sm:block">
          Зах зээлийн өөрчлөлт, хөрөнгө оруулалтын боломж, өгөөж болон зарын мэдээллийг нэг
          платформоос шинжилнэ.
        </p>
      </div>

      <div className="relative hidden items-center gap-2.5 text-sm text-white/50 sm:flex">
        <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-series-1 motion-safe:animate-pulse" />
        Өнөөдрийн зах зээлийн мэдээллийг шинжилж байна.
      </div>
    </div>
  );
}
