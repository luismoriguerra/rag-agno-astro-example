import type {
  WhatsAppAllowlistAdd,
  WhatsAppSettings,
  WhatsAppSettingsUpdate,
} from "./whatsappTypes";
import {
  AuthApiError,
  authErrorKind,
  getAccessToken,
  getAuthorizationHeader,
} from "../lib/auth0";

const API_BASE = import.meta.env.PUBLIC_AGENTOS_API_BASE_URL ?? "http://localhost:8000";

async function parseError(response: Response): Promise<Error> {
  try {
    const body = await response.json();
    const message = body.message ?? `Request failed (${response.status})`;
    if (response.status === 401 || response.status === 403) {
      return new AuthApiError(message, authErrorKind(message));
    }
    return new Error(message);
  } catch {
    return new Error(`Request failed (${response.status})`);
  }
}

async function authFetch(
  input: string,
  init: RequestInit = {},
  allowRetry = true,
): Promise<Response> {
  const authHeaders = await getAuthorizationHeader();
  const res = await fetch(input, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...authHeaders,
      ...(init.headers ?? {}),
    },
  });

  if (res.status === 401 && allowRetry) {
    await getAccessToken();
    return authFetch(input, init, false);
  }

  return res;
}

export async function getWhatsAppSettings(): Promise<WhatsAppSettings> {
  const res = await authFetch(`${API_BASE}/api/whatsapp/settings`);
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<WhatsAppSettings>;
}

export async function updateWhatsAppSettings(
  body: WhatsAppSettingsUpdate,
): Promise<WhatsAppSettings> {
  const res = await authFetch(`${API_BASE}/api/whatsapp/settings`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<WhatsAppSettings>;
}

export async function addAllowlistPhone(body: WhatsAppAllowlistAdd): Promise<WhatsAppSettings> {
  const res = await authFetch(`${API_BASE}/api/whatsapp/settings/allowlist`, {
    method: "POST",
    body: JSON.stringify(body),
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<WhatsAppSettings>;
}

export async function removeAllowlistPhone(phoneNumber: string): Promise<WhatsAppSettings> {
  const encoded = encodeURIComponent(phoneNumber);
  const res = await authFetch(`${API_BASE}/api/whatsapp/settings/allowlist/${encoded}`, {
    method: "DELETE",
  });
  if (!res.ok) throw await parseError(res);
  return res.json() as Promise<WhatsAppSettings>;
}

export function isValidE164(phone: string): boolean {
  return /^\+[1-9]\d{1,14}$/.test(phone.trim());
}
