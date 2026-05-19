import type { APIRoute } from "astro";

import { auth0TokenUrl, getAuthConfig } from "../../../lib/auth/config";
import {
  ACCESS_COOKIE,
  REFRESH_COOKIE,
  SESSION_COOKIE,
  verifySignedPayload,
} from "../../../lib/auth/session";

export const GET: APIRoute = async ({ cookies, url }) => {
  const origin = url.origin;

  try {
    const config = getAuthConfig(origin);
    const session = verifySignedPayload(
      cookies.get(SESSION_COOKIE)?.value,
      config.secret,
    );
    if (!session) {
      return new Response(JSON.stringify({ message: "Your session expired. Sign in again to continue." }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const existingAccess = cookies.get(ACCESS_COOKIE)?.value;
    if (existingAccess && tokenHasApiScope(existingAccess)) {
      return new Response(JSON.stringify({ access_token: existingAccess }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    const refreshToken = cookies.get(REFRESH_COOKIE)?.value;
    if (!refreshToken) {
      return new Response(JSON.stringify({ message: "Your session expired. Sign in again to continue." }), {
        status: 401,
        headers: { "Content-Type": "application/json" },
      });
    }

    const tokenResponse = await fetch(auth0TokenUrl(config), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        grant_type: "refresh_token",
        client_id: config.clientId,
        refresh_token: refreshToken,
        audience: config.audience,
        scope: "openid profile email access:api",
      }),
    });

    if (!tokenResponse.ok) {
      return new Response(
        JSON.stringify({
          message: "Sign-in is temporarily unavailable. Try again in a few minutes.",
        }),
        { status: 503, headers: { "Content-Type": "application/json" } },
      );
    }

    const tokens = (await tokenResponse.json()) as {
      access_token: string;
      refresh_token?: string;
      expires_in: number;
    };

    cookies.set(ACCESS_COOKIE, tokens.access_token, {
      httpOnly: true,
      sameSite: "lax",
      secure: origin.startsWith("https"),
      path: "/",
      maxAge: tokens.expires_in,
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

    return new Response(JSON.stringify({ access_token: tokens.access_token }), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch {
    return new Response(
      JSON.stringify({
        message: "Unable to access your data. Sign in again or contact support.",
      }),
      { status: 500, headers: { "Content-Type": "application/json" } },
    );
  }
};

function tokenHasApiScope(token: string): boolean {
  try {
    const payload = token.split(".")[1];
    if (!payload) return false;
    const json = JSON.parse(Buffer.from(payload, "base64url").toString("utf8")) as {
      scope?: string;
    };
    return (json.scope ?? "").split(/\s+/).includes("access:api");
  } catch {
    return false;
  }
}
