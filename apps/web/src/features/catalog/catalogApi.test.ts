import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchRenderStates,
  formatSourceAge,
  modeBadgeLabel,
  searchObjects,
} from "./catalogApi";

describe("catalogApi helpers", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("formats source mode badges honestly", () => {
    expect(modeBadgeLabel("LIVE")).toBe("LIVE CATALOG");
    expect(modeBadgeLabel("CACHED")).toBe("CACHED");
    expect(modeBadgeLabel("DEMO")).toBe("OFFLINE DEMO");
  });

  it("formats source age in minutes, hours, or offline fallback", () => {
    const now = Date.parse("2026-11-22T00:00:00Z");
    expect(formatSourceAge(null, now)).toBe("No live fetch");
    expect(formatSourceAge("2026-11-21T23:45:00Z", now)).toBe("15m ago");
    expect(formatSourceAge("2026-11-21T20:00:00Z", now)).toBe("4h ago");
  });

  it("preserves six-digit NORAD query parameters in searchObjects", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        schema_version: "1.0",
        generated_at_utc: "2026-11-22T00:00:00Z",
        items: [],
        next_cursor: null,
        total: 0,
        catalog_snapshot_id: "sha256:" + "0".repeat(64),
        provenance: {
          kind: "CATALOG_OBSERVATION",
          mode: "LIVE",
          source: "CelesTrak",
          assumptions: [],
          limitations: [],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await searchObjects({ query: "123456", kind: "DEBRIS", limit: 25 });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/objects?query=123456&kind=DEBRIS&limit=25",
      { signal: undefined },
    );
  });

  it("requests selected object states when ids are provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        at_utc: "2026-11-22T00:00:00Z",
        frame: "ITRS",
        position_unit: "m",
        velocity_unit: "m/s",
        states: [],
        provenance: {
          kind: "PROPAGATED_ESTIMATE",
          mode: "LIVE",
          source: "CelesTrak",
          assumptions: [],
          limitations: [],
        },
      }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchRenderStates({
      scope: "selected",
      ids: ["NORAD:100500"],
      limit: 1,
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/states?scope=selected&ids=NORAD%3A100500&limit=1",
      { signal: undefined },
    );
  });
});
