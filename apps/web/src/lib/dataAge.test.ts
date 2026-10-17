import { describe, expect, it } from "vitest";
import { isDataOlderThan } from "./dataAge";

describe("data age", () => {
  const now = Date.parse("2026-10-17T12:00:00Z");

  it("marks data old based on its source timestamp and domain threshold", () => {
    expect(isDataOlderThan("2026-10-17T09:59:59Z", 2 * 60 * 60 * 1000, now)).toBe(true);
    expect(isDataOlderThan("2026-10-17T10:00:01Z", 2 * 60 * 60 * 1000, now)).toBe(false);
  });

  it("does not infer stale data from a missing, invalid, or future timestamp", () => {
    expect(isDataOlderThan(null, 1000, now)).toBe(false);
    expect(isDataOlderThan("invalid", 1000, now)).toBe(false);
    expect(isDataOlderThan("2026-10-17T12:00:01Z", 1000, now)).toBe(false);
  });
});
