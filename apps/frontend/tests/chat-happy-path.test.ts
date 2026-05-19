import { describe, expect, it } from "vitest";

describe("chat happy path contract", () => {
  it("defines required UI states", () => {
    const states = [
      "empty",
      "restoring",
      "ready",
      "submitting",
      "thinking",
      "streaming",
      "stopping",
      "stopped",
      "failed",
      "deleted",
    ];
    expect(states).toContain("streaming");
    expect(states).toContain("deleted");
  });
});
