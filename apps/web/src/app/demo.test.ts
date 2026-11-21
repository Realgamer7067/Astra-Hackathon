import { afterEach, expect, test, vi } from "vitest";
import { loadDemo, utcLabel } from "./demo";

afterEach(() => vi.unstubAllGlobals());

test("an unavailable API cannot supply a demo snapshot", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue(new Response(null, { status: 503 })),
  );
  await expect(loadDemo(new AbortController().signal)).rejects.toThrow(
    "Demo API unavailable",
  );
});

test("viewer labels a fixed instant in UTC regardless of local timezone", () => {
  expect(utcLabel("2026-11-21T12:00:00Z")).toBe("2026-11-21 12:00 UTC");
});
