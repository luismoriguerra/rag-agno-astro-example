import type { APIRoute } from "astro";

import { auth0LogoutUrl, auth0TokenUrl, getAuthConfig } from "../../../lib/auth/config";
import {
  ACCESS_COOKIE,
  PKCE_COOKIE,
  REFRESH_COOKIE,
  SESSION_COOKIE,
  STATE_COOKIE,
  signPayload,
} from "../../../lib/auth/session";

export const GET: APIRoute = async ({ url, cookies, redirect }) => {
  const origin = url.origin;
  const config = getAuthConfig(origin);
  const code = url.searchParams.get("code");
  const state = url.searchParams.get("state");
  const error = url.searchParams.get("error_description") ?? url.searchParams.get("error");

  if (error) {
    cookies.delete(SESSION_COOKIE, { path: "/" });
    cookies.delete(REFRESH_COOKIE, { path: "/" });
    cookies.delete(ACCESS_COOKIE, { path: "/" });
    cookies.delete(PKCE_COOKIE, { path: "/" });
    cookies.delete(STATE_COOKIE, { path: "/" });

    const returnUrl = `${config.appOrigin}/api/auth/login`;
    return redirect(auth0LogoutUrl(config, returnUrl));
  }

  if (!code || !state) {
    return redirect("/api/auth/login");
  }

  const stateCookie = cookies.get(STATE_COOKIE)?.value;
  const pkceVerifier = cookies.get(PKCE_COOKIE)?.value;
  if (!stateCookie || !pkceVerifier) {
    return redirect("/api/auth/login");
  }

  const [expectedState, returnTo] = stateCookie.split(":");
  if (expectedState !== state) {
    return redirect("/api/auth/login");
  }

  const tokenResponse = await fetch(auth0TokenUrl(config), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      grant_type: "authorization_code",
      client_id: config.clientId,
      code_verifier: pkceVerifier,
      code,
      redirect_uri: `${config.appOrigin}/api/auth/callback`,
    }),
  });

  if (!tokenResponse.ok) {
    return redirect("/chat?auth_error=Sign-in%20is%20temporarily%20unavailable.%20Try%20again%20in%20a%20few%20minutes.");
  }

  const tokens = (await tokenResponse.json()) as {
    access_token: string;
    refresh_token?: string;
    expires_in: number;
    id_token?: string;
  };

  const sub = decodeJwtSub(tokens.access_token) ?? "unknown";
  const name = decodeJwtClaim(tokens.access_token, "name");

  let email: string | undefined;
  let picture: string | undefined;
  if (tokens.id_token) {
    email = decodeJwtClaim(tokens.id_token, "email");
    picture = decodeJwtClaim(tokens.id_token, "picture");
  }
  if (!email) email = decodeJwtClaim(tokens.access_token, "email");
  if (!picture) picture = decodeJwtClaim(tokens.access_token, "picture");

  const sessionExp = Math.floor(Date.now() / 1000) + 60 * 60 * 24;
  const sessionValue = signPayload({ sub, exp: sessionExp, name, email, picture }, config.secret);

  cookies.set(SESSION_COOKIE, sessionValue, {
    httpOnly: true,
    sameSite: "lax",
    secure: origin.startsWith("https"),
    path: "/",
    maxAge: 60 * 60 * 24,
  });

  if (tokens.refresh_token) {
    cookies.set(REFRESH_COOKIE, tokens.refresh_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: origin.startsWith("https"),
      path: "/",
      maxAge: 60 * 60 * 24 * 30,
    });
  }

  cookies.set(ACCESS_COOKIE, tokens.access_token, {
    httpOnly: true,
    sameSite: "lax",
    secure: origin.startsWith("https"),
    path: "/",
    maxAge: tokens.expires_in,
  });

  cookies.delete(PKCE_COOKIE, { path: "/" });
  cookies.delete(STATE_COOKIE, { path: "/" });

  return redirect(returnTo || "/chat");
};

function decodeJwtSub(token: string): string | null {
  return decodeJwtClaim(token, "sub") ?? null;
}

function decodeJwtClaim(token: string, claim: string): string | undefined {
  try {
    const payload = token.split(".")[1];
    if (!payload) return undefined;
    const json = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as Record<
      string,
      unknown
    >;
    const value = json[claim];
    return typeof value === "string" ? value : undefined;
  } catch {
    return undefined;
  }
}
