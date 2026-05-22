import type { APIRoute } from "astro";
import { SESSION_COOKIE, verifySignedPayload } from "../../../lib/auth/session";

export const GET: APIRoute = async ({ cookies }) => {
  const secret = process.env.AUTH0_SECRET ?? import.meta.env.AUTH0_SECRET;
  if (!secret) {
    return new Response(JSON.stringify({ error: "Not configured" }), { status: 500 });
  }

  const session = verifySignedPayload(cookies.get(SESSION_COOKIE)?.value, secret);
  if (!session) {
    return new Response(JSON.stringify({ error: "Not authenticated" }), { status: 401 });
  }

  return new Response(
    JSON.stringify({
      sub: session.sub,
      name: session.name ?? null,
      email: session.email ?? null,
      picture: session.picture ?? null,
    }),
    {
      status: 200,
      headers: { "Content-Type": "application/json" },
    },
  );
};
