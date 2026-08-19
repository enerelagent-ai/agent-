"use client";

import { Check, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { decideComplexReview } from "@/lib/api";

const BLOCK_LABELS: Record<string, string> = {
  landmark_or_unknown_relation: "Landmark-ийг approve хийхгүй",
  complex_location_not_verified: "Хотхоны registry байршил баталгаажаагүй",
  district_guard_failed: "Зарын дүүрэг registry-тэй зөрсөн",
  listing_pointer_changed: "Хотхоны холбоос өөрчлөгдсөн",
};

export function ComplexReviewActions({
  listingId,
  canApprove,
  blockReason,
}: {
  listingId: number;
  canApprove: boolean;
  blockReason: string | null;
}) {
  const router = useRouter();
  const [saving, setSaving] = useState<"approve" | "reject" | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function decide(decision: "approve" | "reject") {
    const label = decision === "approve" ? "баталгаажуулах" : "татгалзаж хотхоны холбоосыг салгах";
    if (!window.confirm(`Энэ evidence-ийг ${label} уу?`)) return;
    setSaving(decision);
    setError(null);
    try {
      await decideComplexReview(listingId, decision);
      router.refresh();
    } catch {
      setError("Шийдвэр хадгалж чадсангүй. Мөр өөрчлөгдсөн эсэхийг шалгана уу.");
    } finally {
      setSaving(null);
    }
  }

  return (
    <div className="mt-2 flex flex-col items-end gap-1">
      <div className="flex gap-1.5">
        <button
          type="button"
          disabled={!canApprove || saving !== null}
          title={!canApprove && blockReason ? BLOCK_LABELS[blockReason] ?? blockReason : undefined}
          onClick={() => decide("approve")}
          className="inline-flex items-center gap-1 rounded-md bg-emerald-600 px-2 py-1 text-[11px] font-semibold text-white disabled:cursor-not-allowed disabled:opacity-35"
        >
          <Check className="h-3 w-3" aria-hidden /> Approve
        </button>
        <button
          type="button"
          disabled={saving !== null}
          onClick={() => decide("reject")}
          className="inline-flex items-center gap-1 rounded-md border border-red-200 px-2 py-1 text-[11px] font-semibold text-red-700 disabled:opacity-35"
        >
          <X className="h-3 w-3" aria-hidden /> Reject
        </button>
      </div>
      {!canApprove && blockReason && (
        <span className="max-w-48 text-right text-[10px] leading-tight text-ink-muted">
          {BLOCK_LABELS[blockReason] ?? blockReason}
        </span>
      )}
      {error && <span className="max-w-48 text-right text-[10px] text-red-600">{error}</span>}
    </div>
  );
}
