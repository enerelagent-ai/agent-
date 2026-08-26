import { getPublicAffordability, type PublicAffordabilitySnapshot } from "./api";

export function parsePublicAffordability(html: string): PublicAffordabilitySnapshot {
  const payload = html.match(/var L\s*=\s*(\[\[[\s\S]*?\]\]),\s*D\s*=\s*(\[[\s\S]*?\]),\s*CAP\s*=\s*(\d+),\s*MIN_DOWN\s*=\s*([\d.]+),\s*MAX_AREA\s*=\s*([\d.]+)/);
  if (!payload) throw new Error("Affordability payload format changed");
  const dates = html.match(/20\d{2}-\d{2}-\d{2}/g) ?? [];
  return {
    source_url: "",
    data_as_of: dates.sort().at(-1) ?? new Date().toISOString().slice(0, 10),
    listings: JSON.parse(payload[1]),
    districts: JSON.parse(payload[2]),
    rules: {
      loan_cap_mnt: Number(payload[3]),
      min_downpayment_ratio: Number(payload[4]),
      max_area_sqm: Number(payload[5]),
      formula_version: "public-v1",
    },
  };
}

async function getFallback(): Promise<PublicAffordabilitySnapshot> {
  const response = await fetch("https://hotkhon.mn/bolomj/", {
    headers: { "User-Agent": "EnerelMarket-PublicImporter/1.0 (+licensed republication)" },
    next: { revalidate: 86400 },
  });
  if (!response.ok) throw new Error(`Affordability feed returned ${response.status}`);
  return parsePublicAffordability(await response.text());
}

export async function getAvailableAffordability(): Promise<PublicAffordabilitySnapshot> {
  try {
    return await getPublicAffordability();
  } catch {
    return getFallback();
  }
}
