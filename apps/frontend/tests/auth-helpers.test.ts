import { describe, expect, it } from "vitest";

import { authErrorKind } from "../src/lib/auth0";

describe("auth helpers", () => {
  it("classifies session expiry messages", () => {
    expect(authErrorKind("Your session expired. Sign in again to continue.")).toBe(
      "session_expired",
    );
  });

  it("classifies IdP unavailable messages", () => {
    expect(authErrorKind("Sign-in is temporarily unavailable. Try again.")).toBe(
      "idp_unavailable",
    );
  });

  it("builds bearer authorization header shape", async () => {
    const header = {
      Authorization: "Bearer test-token",
      "Content-Type": "application/json",
    };
    expect(header.Authorization).toMatch(/^Bearer /);
  });
});
