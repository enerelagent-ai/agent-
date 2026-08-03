import { NextResponse } from "next/server";

import { SESSION_COOKIE_NAME } from "@/lib/session";

// No UI wired to this yet (out of scope for the login-page redesign that
// introduced it) -- included because a real session mechanism without any
// way to end one is a half-built primitive. Clearing the cookie is enough;
// there's no server-side session store to also invalidate.
export async function POST() {
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE_NAME, "", { path: "/", maxAge: 0 });
  return res;
}
