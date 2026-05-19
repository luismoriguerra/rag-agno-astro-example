import { defineMiddleware } from "astro:middleware";

import { verifySignedPayload, SESSION_COOKIE } from "./lib/auth/session";

const PUBLIC_PATHS = new Set([
  "/api/auth/login",
  "/api/auth/callback",
  "/api/auth/logout",
  "/health",
]);

function isPublicAsset(pathname: string): boolean {
  return (
    pathname.startsWith("/_astro/") ||
    pathname.startsWith("/favicon") ||
    pathname.endsWith(".css") ||
    pathname.endsWith(".js") ||
    pathname.endsWith(".map") ||
    pathname.endsWith(".svg") ||
    pathname.endsWith(".ico") ||
    pathname.endsWith(".woff2")
  );
}

function isPublicRoute(pathname: string): boolean {
  if (PUBLIC_PATHS.has(pathname)) return true;
  if (pathname.startsWith("/api/auth/access-token")) return true;
  if (isPublicAsset(pathname)) return true;
  return false;
}

export const onRequest = defineMiddleware(async (context, next) => {
  const { pathname } = context.url;
  if (isPublicRoute(pathname)) {
    return next();
  }

  const secret = process.env.AUTH0_SECRET ?? import.meta.env.AUTH0_SECRET;
  if (!secret) {
    return context.redirect("/api/auth/login");
  }

  const session = verifySignedPayload(
    context.cookies.get(SESSION_COOKIE)?.value,
    secret,
  );
  if (!session) {
    const returnTo = `${pathname}${context.url.search}`;
    return context.redirect(`/api/auth/login?returnTo=${encodeURIComponent(returnTo)}`);
  }

  return next();
});
