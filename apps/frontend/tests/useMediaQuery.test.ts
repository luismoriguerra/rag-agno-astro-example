import { describe, expect, it } from "vitest";
import { MOBILE_MAX_WIDTH_PX, MOBILE_MEDIA_QUERY } from "../src/lib/breakpoints";

describe("breakpoints", () => {
  it("defines 767px as mobile max width for md breakpoint alignment", () => {
    expect(MOBILE_MAX_WIDTH_PX).toBe(767);
    expect(MOBILE_MEDIA_QUERY).toBe("(max-width: 767px)");
  });
});

describe("useMediaQuery module", () => {
  it("exports a hook function", async () => {
    const mod = await import("../src/hooks/useMediaQuery");
    expect(typeof mod.useMediaQuery).toBe("function");
  });
});
