"use client";

import maplibregl, { type Map as MapLibreMap } from "maplibre-gl";
import { useEffect, useRef } from "react";

import type { PublicComplexSummary } from "@/lib/api";

function priceColor(value: number | null): string {
  if (value === null) return "#64748b";
  if (value < 4_000_000) return "#16a34a";
  if (value < 6_000_000) return "#eab308";
  if (value < 8_000_000) return "#f97316";
  return "#dc2626";
}

export function ComplexMap({ complexes, contours = {} }: { complexes: PublicComplexSummary[]; contours?: Record<string, number[][][]> }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return;
    const located = complexes.filter((item) => item.lat !== null && item.lng !== null);
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: "https://tiles.openfreemap.org/styles/liberty",
      center: [106.917, 47.918],
      zoom: 11,
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl(), "top-right");
    map.on("load", () => {
      map.addSource("complexes", {
        type: "geojson",
        data: {
          type: "FeatureCollection",
          features: located.map((item) => ({
            type: "Feature",
            geometry: { type: "Point", coordinates: [item.lng as number, item.lat as number] },
            properties: {
              slug: item.source_slug,
              name: item.name,
              district: item.district ?? "Дүүрэг тодорхойгүй",
              listings: item.active_listings,
              price: item.median_sale_price_per_sqm,
              color: priceColor(item.median_sale_price_per_sqm),
            },
          })),
        },
      });
      map.addLayer({
        id: "complex-circles",
        type: "circle",
        source: "complexes",
        paint: {
          "circle-radius": ["interpolate", ["linear"], ["get", "listings"], 1, 7, 100, 17],
          "circle-color": ["get", "color"],
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff",
          "circle-opacity": 0.88,
        },
      });
      const polygonFeatures = Object.entries(contours).flatMap(([slug, polygons]) => {
        const profile = located.find((item) => item.source_slug === slug);
        return polygons.map((coordinates) => ({
          type: "Feature" as const,
          geometry: { type: "Polygon" as const, coordinates: [coordinates] },
          properties: { slug, color: priceColor(profile?.median_sale_price_per_sqm ?? null) },
        }));
      });
      map.addSource("complex-contours", { type: "geojson", data: { type: "FeatureCollection", features: polygonFeatures } });
      map.addLayer({ id: "complex-contour-fill", type: "fill", source: "complex-contours", paint: { "fill-color": ["get", "color"], "fill-opacity": 0.24 } }, "complex-circles");
      map.addLayer({ id: "complex-contour-line", type: "line", source: "complex-contours", paint: { "line-color": ["get", "color"], "line-width": 2 } }, "complex-circles");
      map.on("mouseenter", "complex-circles", () => { map.getCanvas().style.cursor = "pointer"; });
      map.on("mouseleave", "complex-circles", () => { map.getCanvas().style.cursor = ""; });
      map.on("click", "complex-circles", (event) => {
        const feature = event.features?.[0];
        if (!feature || feature.geometry.type !== "Point") return;
        const props = feature.properties as Record<string, string | number | null>;
        const root = document.createElement("div");
        const title = document.createElement("strong");
        title.textContent = String(props.name);
        const meta = document.createElement("p");
        meta.textContent = `${props.district} · ${props.listings} идэвхтэй зар`;
        const link = document.createElement("a");
        link.href = `/complexes/${props.slug}`;
        link.textContent = "Analytics харах →";
        link.style.color = "#e85520";
        root.append(title, meta, link);
        new maplibregl.Popup().setLngLat(feature.geometry.coordinates as [number, number]).setDOMContent(root).addTo(map);
      });
    });
    return () => { map.remove(); mapRef.current = null; };
  }, [complexes]);

  return <div ref={containerRef} className="h-[68vh] min-h-[520px] w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-100" aria-label="Хотхоны интерактив газрын зураг" />;
}
