import { NextRequest, NextResponse } from "next/server";

const REALM = "Ulaanbaatar Real Estate Analytics";

// Single-admin gate for the whole site (Week 8 deploy). Unset ADMIN_USERNAME/
// ADMIN_PASSWORD (local dev's default -- see backend/app/config.py's same
// opt-in pattern) leaves every route open. Once the browser has answered the
// native Basic Auth prompt once, it resends the same header automatically on
// every later request to this origin -- including the /api/backend/* proxy
// calls the dashboard makes -- so this one check covers the whole app.
export function middleware(request: NextRequest) {
  const username = process.env.ADMIN_USERNAME;
  const password = process.env.ADMIN_PASSWORD;

  if (!username || !password) {
    return NextResponse.next();
  }

  const authHeader = request.headers.get("authorization");
  if (authHeader?.startsWith("Basic ")) {
    const [user, pass] = atob(authHeader.slice(6)).split(":");
    if (user === username && pass === password) {
      return NextResponse.next();
    }
  }

  return new NextResponse("Authentication required", {
    status: 401,
    headers: { "WWW-Authenticate": `Basic realm="${REALM}"` },
  });
}

export const config = {
  matcher: "/((?!_next/static|_next/image|favicon.ico).*)",
};
