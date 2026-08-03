import { NextRequest, NextResponse } from "next/server";

import { SESSION_COOKIE_NAME, SESSION_MAX_AGE_SECONDS, createSessionToken } from "@/lib/session";

// Manual constant-time compare (no Node `crypto.timingSafeEqual` -- this
// file is written to work the same way as session.ts, without assuming a
// Node-only API). Not the sole security boundary: every proxied backend
// call is re-checked by the backend's own require_admin dependency
// regardless of what this cookie says, so this is a first gate, not the
// only one.
function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

export async function POST(request: NextRequest) {
  const adminUsername = process.env.ADMIN_USERNAME;
  const adminPassword = process.env.ADMIN_PASSWORD;

  // Matches middleware.ts: unset admin vars means auth isn't configured
  // (local dev), so there's no session to grant.
  if (!adminUsername || !adminPassword) {
    return NextResponse.json({ error: "Auth is not configured" }, { status: 503 });
  }

  const body = await request.json().catch(() => null);
  const username = typeof body?.username === "string" ? body.username : "";
  const password = typeof body?.password === "string" ? body.password : "";

  const valid =
    timingSafeEqual(username, adminUsername) && timingSafeEqual(password, adminPassword);

  // Deliberately the same error for a bad username vs. a bad password --
  // distinguishing them would tell an attacker which one to keep guessing.
  if (!valid) {
    return NextResponse.json({ error: "Invalid credentials" }, { status: 401 });
  }

  const token = await createSessionToken(adminPassword);
  const res = NextResponse.json({ ok: true });
  res.cookies.set(SESSION_COOKIE_NAME, token, {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    path: "/",
    maxAge: SESSION_MAX_AGE_SECONDS,
  });
  return res;
}
