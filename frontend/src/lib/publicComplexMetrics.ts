import type { PublicComplexSummary } from "./api";

type Metrics = PublicComplexSummary["profile_metrics"];

function text(value: string): string {
  return value.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ").trim();
}

function metricNumber(html: string, label: string): number | undefined {
  const escaped = label.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const valueThenLabel = new RegExp(`<div class="v[^"]*">\\s*([\\d.]+)[^<]*(?:<small>[^<]*<\\/small>)?\\s*<\\/div>\\s*<div class="k">${escaped}<\\/div>`, "s");
  const labelThenValue = new RegExp(`<div class="k">${escaped}<\\/div>\\s*<div class="v[^"]*">\\s*([\\d.]+)`, "s");
  const match = html.match(valueThenLabel) ?? html.match(labelThenValue);
  return match ? Number(match[1]) : undefined;
}

export function parsePublicComplexMetrics(html: string): Metrics {
  const sub = html.match(/<div class="sub">([\s\S]*?)<\/div>/);
  const range = html.match(/<div class="v">\s*([\d.,]+)\s*[–-]\s*([\d.,]+)[\s\S]*?<div class="k">Үнийн хүрээ/);
  const history = html.match(/<span class="rng">(\d{4}-\d{2}-\d{2})\s*[—-]+\s*(\d{4}-\d{2}-\d{2})<\/span>/);
  const roomSection = html.match(/<h2>Өрөөний тоогоор<\/h2>([\s\S]*?)(?:<h2>Байршлын задаргаа<\/h2>|<div class="sh" style="margin-top:0">\s*<h2>Байршлын задаргаа)/)?.[1] ?? "";
  const locationSection = html.match(/<h2>Байршлын задаргаа<\/h2>([\s\S]*?)(?:<h2>Зах зээлийн байдал<\/h2>|<div class="sh">\s*<h2>Зах зээлийн байдал)/)?.[1] ?? "";
  const driverSection = html.match(/<h2>Үнэд нөлөөлж буй хүчин зүйл<\/h2>([\s\S]*?)<h2>Байрны бүтэц<\/h2>/)?.[1] ?? "";
  return {
    ...(sub ? { building_summary: text(sub[1]) } : {}),
    ...(range ? { price_range_million: [Number(range[1].replaceAll(",", "")), Number(range[2].replaceAll(",", ""))] as [number, number] } : {}),
    location_score: metricNumber(html, "Байршлын оноо"),
    clearance_days: metricNumber(html, "Зар цэвэрлэгдэх"),
    likely_sold: metricNumber(html, "Зарагдсан байж болзошгүй"),
    price_reductions_14d: metricNumber(html, "Үнээ бууруулсан"),
    rental_yield_pct: metricNumber(html, "Түрээсийн өгөөж"),
    ...(history ? { history_range: [history[1], history[2]] as [string, string] } : {}),
    room_price_per_sqm_million: [...roomSection.matchAll(/<td>(\d+) өрөө<\/td>\s*<td class="r">([\d.]+)<\/td>/g)].map((match) => ({ rooms: Number(match[1]), value: Number(match[2]) })),
    location_breakdown: [...locationSection.matchAll(/<div class="lab">\s*<span>([\s\S]*?)<\/span>\s*<span class="num">([\d.]+)<\/span>/g)].map((match) => ({ label: text(match[1]), score: Number(match[2]) })),
    price_drivers: [...driverSection.matchAll(/<span class="lab">([\s\S]*?)<\/span>[\s\S]*?<span class="val [^"]+">([+−-]?[\d.]+)%<\/span>/g)].map((match) => ({ label: text(match[1]), impact_pct: Number(match[2].replace("−", "-")) })),
  };
}

export async function getLicensedPublicProfileMetrics(slug: string): Promise<Metrics> {
  if (!/^[a-z0-9-]+$/.test(slug)) return {};
  try {
    const response = await fetch(`https://hotkhon.mn/hotkhon/${slug}/`, {
      headers: { "User-Agent": "EnerelMarket-PublicImporter/1.0 (+licensed republication)" },
      next: { revalidate: 86400 },
    });
    return response.ok ? parsePublicComplexMetrics(await response.text()) : {};
  } catch {
    return {};
  }
}
