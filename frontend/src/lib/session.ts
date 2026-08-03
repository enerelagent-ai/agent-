// Signs/verifies the login session cookie. Deliberately dependency-free
// (Web Crypto's crypto.subtle + btoa/atob, all runtime globals) rather than
// pulling in a JWT library, and runtime-agnostic on purpose: this is called
// from both middleware.ts (Edge runtime, no Node `crypto`/`Buffer`) and the
// login/logout route handlers (Node runtime) with the exact same code.
//
// The signing key is ADMIN_PASSWORD itself, not a separate secret: anyone
// who knows ADMIN_PASSWORD already has full access to the site (it's the
// single shared admin credential), so deriving the session key from it adds
// no new exposure, and avoids a third env var to configure and keep in
// sync across Vercel/Render on top of the two that already have to match.

export const SESSION_COOKIE_NAME = "session";
export const SESSION_MAX_AGE_SECONDS = 60 * 60 * 24 * 7; // 7 days

function bufferToBase64Url(buf: ArrayBuffer): string {
  const bytes = new Uint8Array(buf);
  let binary = "";
  for (const b of bytes) binary += String.fromCharCode(b);
  return btoa(binary).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function base64UrlToBuffer(b64url: string): ArrayBuffer {
  const padded = b64url + "=".repeat((4 - (b64url.length % 4)) % 4);
  const b64 = padded.replace(/-/g, "+").replace(/_/g, "/");
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

function importKey(secret: string): Promise<CryptoKey> {
  return crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign", "verify"]
  );
}

// Token shape: "<expiry-unix-seconds>.<hmac-sha256 of the expiry, base64url>".
// No payload beyond the expiry -- there's only one account, so "valid
// signature, not expired" is the entire authorization question.
export async function createSessionToken(secret: string): Promise<string> {
  const exp = Math.floor(Date.now() / 1000) + SESSION_MAX_AGE_SECONDS;
  const key = await importKey(secret);
  const sig = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(String(exp)));
  return `${exp}.${bufferToBase64Url(sig)}`;
}

export async function verifySessionToken(
  token: string | undefined,
  secret: string
): Promise<boolean> {
  if (!token) return false;
  const [expStr, sig] = token.split(".");
  if (!expStr || !sig) return false;
  const exp = Number(expStr);
  if (!Number.isFinite(exp) || exp < Math.floor(Date.now() / 1000)) return false;

  try {
    const key = await importKey(secret);
    return await crypto.subtle.verify(
      "HMAC",
      key,
      base64UrlToBuffer(sig),
      new TextEncoder().encode(expStr)
    );
  } catch {
    return false;
  }
}
