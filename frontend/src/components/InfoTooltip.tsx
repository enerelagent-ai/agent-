"use client";

import { useState } from "react";
import { Info } from "lucide-react";

// Hover OR click opens it (click makes it usable on touch devices too);
// click-away and Escape both close it.
export function InfoTooltip({ text }: { text: string }) {
  const [open, setOpen] = useState(false);

  return (
    <span className="relative inline-flex">
      <button
        type="button"
        aria-label="Тайлбар"
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen((v) => !v)}
        className="flex h-4 w-4 items-center justify-center rounded-full text-ink-muted hover:text-ink-primary"
      >
        <Info className="h-4 w-4" aria-hidden />
      </button>
      {open && (
        <div
          role="tooltip"
          className="absolute left-1/2 top-full z-20 mt-2 w-72 -translate-x-1/2 rounded-lg border border-line-grid bg-surface-card p-3 text-xs leading-relaxed text-ink-secondary shadow-lg"
        >
          {text}
        </div>
      )}
    </span>
  );
}
