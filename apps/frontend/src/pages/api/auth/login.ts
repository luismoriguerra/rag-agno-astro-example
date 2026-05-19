import type { APIRoute } from "astro";

import { auth0AuthorizeUrl, getAuthConfig } from "../../../lib/auth/config";
import {
  PKCE_COOKIE,
  STATE_COOKIE,
  createPkcePair,
  randomUrlSafe,
} from "../../../lib/auth/session";

export const GET: APIRoute = async ({ url, cookies, redirect }) => {
  const origin = url.origin;
  const config = getAuthConfig(origin);
  const returnTo = url.searchParams.get("returnTo") ?? "/chat";
  const { verifier, challenge } = createPkcePair();
  const state = randomUrlSafe(16);

  cookies.set(PKCE_COOKIE, verifier, {
    httpOnly: true,
    sameSite: "lax",
    secure: origin.startsWith("https"),
    path: "/",
    maxAge: 600,
  });
  cookies.set(STATE_COOKIE, `${state}:${returnTo}`, {
    httpOnly: true,
    sameSite: "lax",
    secure: origin.startsWith("https"),
    path: "/",
    maxAge: 600,
  });

  const params = new URLSearchParams({
    response_type: "code",
    client_id: config.clientId,
    redirect_uri: `${config.appOrigin}/api/auth/callback`,
    scope: "openid profile email offline_access access:api",
    audience: config.audience,
    state,
    code_challenge: challenge,
    code_challenge_method: "S256",
  });

  return redirect(auth0AuthorizeUrl(config, params));
};
