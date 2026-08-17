import { NextRequest, NextResponse } from "next/server";

// Same-origin proxy to the FastAPI backend. Two reasons this exists instead
// of the browser calling Render directly:
//
// 1. Basic Auth doesn't travel cross-origin. middleware.ts's login prompt
//    only ever earns the browser a cached credential for *this* (Vercel)
//    origin -- a client-side fetch straight to the Render domain would get
//    its own silent 401 with no prompt (fetch() never triggers the native
//    Basic Auth dialog the way a top-level navigation does). Routing
//    through this same-origin handler means the browser's already-cached
//    credential covers it for free.
// 2. It keeps BACKEND_API_URL and the admin password itself out of the
//    client bundle entirely -- both are read here, server-side only, never
//    exposed via a NEXT_PUBLIC_ variable.
const BACKEND_URL = process.env.BACKEND_API_URL ?? "http://localhost:8000";
const ADMIN_USERNAME = process.env.ADMIN_USERNAME;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

export async function GET(request: NextRequest, { params }: { params: { path: string[] } }) {
  const url = `${BACKEND_URL}/${params.path.join("/")}${request.nextUrl.search}`;

  const headers: HeadersInit = {};
  if (ADMIN_USERNAME && ADMIN_PASSWORD) {
    const encoded = Buffer.from(`${ADMIN_USERNAME}:${ADMIN_PASSWORD}`).toString("base64");
    headers["Authorization"] = `Basic ${encoded}`;
  }

  const backendRes = await fetch(url, { headers, cache: "no-store" });
  const body = await backendRes.text();
  return new NextResponse(body, {
    status: backendRes.status,
    headers: { "Content-Type": backendRes.headers.get("Content-Type") ?? "application/json" },
  });
}

export async function POST(request: NextRequest, { params }: { params: { path: string[] } }) {
  const url = `${BACKEND_URL}/${params.path.join("/")}${request.nextUrl.search}`;
  const headers: HeadersInit = {};
  if (ADMIN_USERNAME && ADMIN_PASSWORD) {
    headers["Authorization"] = `Basic ${Buffer.from(`${ADMIN_USERNAME}:${ADMIN_PASSWORD}`).toString("base64")}`;
  }
  const backendRes = await fetch(url, { method: "POST", headers, cache: "no-store" });
  const body = await backendRes.text();
  return new NextResponse(body, {
    status: backendRes.status,
    headers: { "Content-Type": backendRes.headers.get("Content-Type") ?? "application/json" },
  });
}
