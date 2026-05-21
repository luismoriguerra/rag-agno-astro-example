import { createHash, createHmac, randomBytes, timingSafeEqual } from "node:crypto";

export const SESSION_COOKIE = "app_session";
export const REFRESH_COOKIE = "auth_refresh";
export const PKCE_COOKIE = "pkce_verifier";
export const STATE_COOKIE = "oauth_state";
export const ACCESS_COOKIE = "auth_access";

export type SessionPayload = {
  sub: string;
  exp: number;
  name?: string;
  email?: string;
};

export function randomUrlSafe(bytes = 32): string {
  return randomBytes(bytes).toString("base64url");
}

export function signPayload(payload: SessionPayload, secret: string): string {
  const data = Buffer.from(JSON.stringify(payload)).toString("base64url");
  const sig = createHmac("sha256", secret).update(data).digest("base64url");
  return `${data}.${sig}`;
}

export function verifySignedPayload<T extends SessionPayload>(
  value: string | undefined,
  secret: string,
): T | null {
  if (!value) return null;
  const [data, sig] = value.split(".");
  if (!data || !sig) return null;
  const expected = createHmac("sha256", secret).update(data).digest("base64url");
  try {
    if (
      expected.length !== sig.length ||
      !timingSafeEqual(Buffer.from(expected), Buffer.from(sig))
    ) {
      return null;
    }
  } catch {
    return null;
  }
  try {
    const payload = JSON.parse(Buffer.from(data, "base64url").toString("utf8")) as T;
    if (!payload.exp || payload.exp * 1000 < Date.now()) return null;
    return payload;
  } catch {
    return null;
  }
}

export function createPkcePair(): { verifier: string; challenge: string } {
  const verifier = randomUrlSafe(32);
  const challenge = createHash("sha256").update(verifier).digest("base64url");
  return { verifier, challenge };
}
