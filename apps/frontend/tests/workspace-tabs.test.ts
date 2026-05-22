import { describe, expect, it } from "vitest";
import {
  shouldSetArticleBadge,
  shouldShowArticleBadge,
} from "../src/lib/workspaceTabState";

describe("workspaceTabState", () => {
  it("sets badge only when user is on thread tab", () => {
    expect(shouldSetArticleBadge("thread")).toBe(true);
    expect(shouldSetArticleBadge("article")).toBe(false);
  });

  it("shows badge only on thread tab when update pending", () => {
    expect(shouldShowArticleBadge("thread", true)).toBe(true);
    expect(shouldShowArticleBadge("thread", false)).toBe(false);
    expect(shouldShowArticleBadge("article", true)).toBe(false);
    expect(shouldShowArticleBadge("article", false)).toBe(false);
  });
});
