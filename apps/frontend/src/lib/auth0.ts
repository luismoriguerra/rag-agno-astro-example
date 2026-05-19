import { createAuth0Client, type Auth0Client } from "@auth0/auth0-spa-js";

let clientPromise: Promise<Auth0Client> | null = null;

function getDomain(): string {
  return import.meta.env.PUBLIC_AUTH0_DOMAIN ?? "";
}

function getClientId(): string {
  return import.meta.env.PUBLIC_AUTH0_CLIENT_ID ?? "";
}

function getAudience(): string {
  return import.meta.env.PUBLIC_AUTH0_AUDIENCE ?? "";
}

export async function getAuth0Client(): Promise<Auth0Client> {
  if (!clientPromise) {
    clientPromise = createAuth0Client({
      domain: getDomain(),
      clientId: getClientId(),
      authorizationParams: {
        audience: getAudience(),
        scope: "access:api openid profile email",
      },
      cacheLocation: "localstorage",
      useRefreshTokens: true,
    });
  }
  return clientPromise;
}

export async function getAccessToken(): Promise<string> {
  const response = await fetch("/api/auth/access-token", { credentials: "include" });
  if (!response.ok) {
    throw new AuthApiError(await readAuthError(response));
  }
  const data = (await response.json()) as { access_token: string };
  return data.access_token;
}

export async function getAuthorizationHeader(): Promise<HeadersInit> {
  const token = await getAccessToken();
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

export function loginRedirectUrl(returnTo = "/chat"): string {
  const params = new URLSearchParams({ returnTo });
  return `/api/auth/login?${params.toString()}`;
}

export function logoutRedirectUrl(): string {
  return "/api/auth/logout";
}

export type AuthErrorKind = "session_expired" | "idp_unavailable" | "api_auth_failed";

export class AuthApiError extends Error {
  constructor(
    message: string,
    readonly kind: AuthErrorKind = "api_auth_failed",
  ) {
    super(message);
    this.name = "AuthApiError";
  }
}

async function readAuthError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { message?: string };
    return body.message ?? "Authentication failed.";
  } catch {
    if (response.status === 503) return "Sign-in is temporarily unavailable. Try again in a few minutes.";
    if (response.status === 401) return "Your session expired. Sign in again to continue.";
    return "Unable to access your data. Sign in again or contact support.";
  }
}

export function authErrorKind(message: string): AuthErrorKind {
  if (message.toLowerCase().includes("expired")) return "session_expired";
  if (message.toLowerCase().includes("unavailable")) return "idp_unavailable";
  return "api_auth_failed";
}
