/// <reference types="astro/client" />

interface ImportMetaEnv {
  readonly PUBLIC_AGENTOS_API_BASE_URL: string;
  readonly PUBLIC_MOCK_IDENTITY: string;
}

interface ImportMetaEnv {
  readonly env: ImportMetaEnv;
}
