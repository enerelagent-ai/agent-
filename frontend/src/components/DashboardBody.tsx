"use client";

import { useState } from "react";
import { DistrictTable } from "./DistrictTable";
import { RecentListings } from "./RecentListings";
import type { DistrictInvestmentSummary, Listing } from "@/lib/api";

interface DashboardBodyProps {
  investmentSummary: DistrictInvestmentSummary[];
  initialListings: Listing[];
}

// Holds the one piece of state the two sections share: the district applied
// in the listings filter highlights (and scrolls to) that row in the table
// above, so the two sections read as connected rather than independent.
export function DashboardBody({ investmentSummary, initialListings }: DashboardBodyProps) {
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);

  return (
    <>
      <DistrictTable rows={investmentSummary} highlightedDistrict={selectedDistrict} />
      <RecentListings
        initialListings={initialListings}
        districts={investmentSummary.map((row) => row.district)}
        onDistrictApplied={setSelectedDistrict}
      />
    </>
  );
}
