import { describe, expect, it } from "vitest";

import { isValidE164 } from "../src/services/whatsappApi";

describe("whatsappApi validation", () => {
  it("accepts valid E.164 numbers", () => {
    expect(isValidE164("+14155552671")).toBe(true);
  });

  it("rejects numbers without plus prefix", () => {
    expect(isValidE164("14155552671")).toBe(false);
  });
});
