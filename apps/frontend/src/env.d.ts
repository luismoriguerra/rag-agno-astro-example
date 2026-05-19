/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_AGENTOS_API_BASE_URL: string;
  readonly PUBLIC_AUTH0_DOMAIN: string;
  readonly PUBLIC_AUTH0_CLIENT_ID: string;
  readonly PUBLIC_AUTH0_AUDIENCE: string;
  readonly AUTH0_SECRET: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
