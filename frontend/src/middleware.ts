import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE_NAME, verifySessionToken } from "@/lib/session";

// Single-admin gate for the whole site (Week 8 deploy). Unset ADMIN_USERNAME/
// ADMIN_PASSWORD (local dev's default -- see backend/app/config.py's same
// opt-in pattern) leaves every route open.
//
// Session-cookie based rather than HTTP Basic Auth: Basic Auth's native
// browser popup can't be styled or given Mongolian copy at all -- there's
// no page behind it to redesign. /login (see app/login/page.tsx) collects
// the same two credentials, and app/api/auth/login/route.ts issues a
// signed cookie on success; this middleware just checks that cookie and
// redirects to /login (preserving the originally-requested path via
// ?next=) when it's missing or invalid. The backend's own Basic Auth
// (require_admin) is unchanged and still re-checked on every proxied API
// call regardless of what this cookie says.
export async function middleware(request: NextRequest) {
  const username = process.env.ADMIN_USERNAME;
  const password = process.env.ADMIN_PASSWORD;

  if (!username || !password) {
    return NextResponse.next();
  }

  const { pathname } = request.nextUrl;
  // The login page and its own API routes must stay reachable *without* a
  // session -- otherwise there's no way to ever reach the form that grants
  // one, and every request loops back to itself.
  if (pathname === "/login" || pathname.startsWith("/api/auth/")) {
    return NextResponse.next();
  }

  const token = request.cookies.get(SESSION_COOKIE_NAME)?.value;
  if (await verifySessionToken(token, password)) {
    return NextResponse.next();
  }

  const loginUrl = new URL("/login", request.url);
  loginUrl.searchParams.set("next", pathname);
  return NextResponse.redirect(loginUrl);
}

export const config = {
  matcher: "/((?!_next/static|_next/image|favicon.ico).*)",
};
