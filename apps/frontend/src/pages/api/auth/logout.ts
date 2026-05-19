import type { APIRoute } from "astro";

import { auth0LogoutUrl, getAuthConfig } from "../../../lib/auth/config";
import { ACCESS_COOKIE, REFRESH_COOKIE, SESSION_COOKIE } from "../../../lib/auth/session";

export const GET: APIRoute = async ({ url, cookies, redirect }) => {
  const origin = url.origin;
  const config = getAuthConfig(origin);

  cookies.delete(SESSION_COOKIE, { path: "/" });
  cookies.delete(REFRESH_COOKIE, { path: "/" });
  cookies.delete(ACCESS_COOKIE, { path: "/" });

  return redirect(auth0LogoutUrl(config, `${config.appOrigin}/`));
};
