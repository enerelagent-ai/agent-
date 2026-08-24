import type { ReactNode } from "react";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

export const metadata = {
  title: "Улаанбаатар Үл Хөдлөх Хөрөнгө — Аналитик платформ",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="mn">
      <body className="font-sans">{children}</body>
    </html>
  );
}
