export type AuthConfig = {
  domain: string;
  clientId: string;
  audience: string;
  secret: string;
  appOrigin: string;
};

/** Public app URL behind Railway/proxies; falls back to the incoming request origin locally. */
export function resolveAppOrigin(fallbackOrigin: string): string {
  const railwayDomain = process.env.RAILWAY_PUBLIC_DOMAIN?.trim();
  if (railwayDomain) {
    return `https://${railwayDomain}`.replace(/\/$/, "");
  }
  return fallbackOrigin.replace(/\/$/, "");
}

export function getAuthConfig(origin: string): AuthConfig {
  const domain = import.meta.env.PUBLIC_AUTH0_DOMAIN;
  const clientId = import.meta.env.PUBLIC_AUTH0_CLIENT_ID;
  const audience = import.meta.env.PUBLIC_AUTH0_AUDIENCE;
  // Server-only secret is injected at runtime (Railway/local .env), not build time.
  const secret = process.env.AUTH0_SECRET ?? import.meta.env.AUTH0_SECRET;

  if (!domain || !clientId || !audience || !secret) {
    throw new Error("Auth0 environment is not fully configured.");
  }

  return {
    domain,
    clientId,
    audience,
    secret,
    appOrigin: resolveAppOrigin(origin),
  };
}

export function auth0AuthorizeUrl(config: AuthConfig, params: URLSearchParams): string {
  return `https://${config.domain}/authorize?${params.toString()}`;
}

export function auth0TokenUrl(config: AuthConfig): string {
  return `https://${config.domain}/oauth/token`;
}

export function auth0LogoutUrl(config: AuthConfig, returnTo: string): string {
  const params = new URLSearchParams({
    client_id: config.clientId,
    returnTo,
  });
  return `https://${config.domain}/v2/logout?${params.toString()}`;
}
