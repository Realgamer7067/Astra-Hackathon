import { afterEach, describe, expect, it, vi } from "vitest";
import {
  type CatalogObject,
  type ObjectDetail,
  type RenderStates,
  fetchRenderStates,
  formatSourceAge,
  loadSelectedObjectWithState,
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

  it("loads an outside-batch object at the globe batch timestamp and rejects snapshot/epoch mismatches", async () => {
    const snapA = "sha256:" + "a".repeat(64);
    const snapB = "sha256:" + "b".repeat(64);
    const olderEpoch = "2026-11-22T00:00:00Z";

    const existingObj: CatalogObject = {
      id: "NORAD:25544",
      name: "ISS (ZARYA)",
      kind: "PAYLOAD",
      operational_status: "ACTIVE",
      state_source: "CELESTRAK_GP",
      element_epoch_utc: "2026-11-21T23:00:00Z",
      catalog_snapshot_id: snapA,
      mass_kg: null,
      effective_radius_m: null,
      physical_properties_basis: "UNAVAILABLE",
      orbit: { format: "OMM_CSV", theory: "SGP4", frame: "TEME" },
    };

    const outsideObj: CatalogObject = {
      ...existingObj,
      id: "NORAD:100500",
      name: "OUTSIDE-BATCH",
    };

    const olderBatch: RenderStates = {
      at_utc: olderEpoch,
      frame: "ITRS",
      position_unit: "m",
      velocity_unit: "m/s",
      states: [
        {
          object_id: "NORAD:25544",
          position: [6778000, 0, 0],
          velocity: [0, 7660, 0],
        },
      ],
      provenance: {
        kind: "PROPAGATED_ESTIMATE",
        mode: "LIVE",
        source: "CelesTrak GP",
        catalogSnapshotId: snapA,
        coordinateFrame: "ITRS",
        assumptions: [],
        limitations: [],
      },
    };

    const outsideDetail: ObjectDetail = {
      schema_version: "1.0",
      generated_at_utc: "2026-11-22T00:02:00Z",
      object: outsideObj,
      satcat: null,
      staleness_hours: 1.0,
      is_stale: false,
      provenance: olderBatch.provenance,
    };

    // 1. Matching snapshot & batch epoch appends selected object state at olderEpoch.
    const fetchMatch = vi.fn(async (url: string) => {
      if (url.startsWith("/api/v1/objects/")) {
        return { ok: true, json: async () => outsideDetail };
      }
      return {
        ok: true,
        json: async () => ({
          ...olderBatch,
          states: [
            {
              object_id: "NORAD:100500",
              position: [-6800000, 100000, 0],
              velocity: [0, -7600, 0],
            },
          ],
        }),
      };
    });
    vi.stubGlobal("fetch", fetchMatch);

    const matched = await loadSelectedObjectWithState({
      selectedId: "NORAD:100500",
      currentBatch: olderBatch,
      existingObjects: [existingObj],
    });
    expect(fetchMatch).toHaveBeenCalledWith(
      `/api/v1/states?at=${encodeURIComponent(olderEpoch)}&scope=selected&ids=NORAD%3A100500&limit=1`,
      { signal: undefined },
    );
    expect(matched.action).toBe("append");
    if (matched.action === "append") {
      expect(matched.mergedBatch.at_utc).toBe(olderEpoch);
      expect(matched.mergedBatch.states.map((s) => s.object_id)).toEqual([
        "NORAD:25544",
        "NORAD:100500",
      ]);
      expect(matched.mergedObjects.map((o) => o.id)).toEqual([
        "NORAD:25544",
        "NORAD:100500",
      ]);
    }

    // 2. Snapshot mismatch triggers batch reload without appending.
    const fetchNewSnapshot = vi.fn(async (url: string) => {
      if (url.startsWith("/api/v1/objects/")) {
        return {
          ok: true,
          json: async () => ({
            ...outsideDetail,
            object: { ...outsideObj, catalog_snapshot_id: snapB },
          }),
        };
      }
      return {
        ok: true,
        json: async () => ({
          ...olderBatch,
          provenance: { ...olderBatch.provenance, catalogSnapshotId: snapB },
        }),
      };
    });
    vi.stubGlobal("fetch", fetchNewSnapshot);

    const reloaded = await loadSelectedObjectWithState({
      selectedId: "NORAD:100500",
      currentBatch: olderBatch,
      existingObjects: [existingObj],
    });
    expect(reloaded.action).toBe("reload_batch");

    // 3. Epoch mismatch refuses to append mismatched position.
    const fetchWrongEpoch = vi.fn(async (url: string) => {
      if (url.startsWith("/api/v1/objects/")) {
        return { ok: true, json: async () => outsideDetail };
      }
      return {
        ok: true,
        json: async () => ({
          ...olderBatch,
          at_utc: "2026-11-22T00:02:00Z",
          states: [
            {
              object_id: "NORAD:100500",
              position: [-6000000, 900000, 0],
              velocity: [0, -7600, 0],
            },
          ],
        }),
      };
    });
    vi.stubGlobal("fetch", fetchWrongEpoch);

    const rejected = await loadSelectedObjectWithState({
      selectedId: "NORAD:100500",
      currentBatch: olderBatch,
      existingObjects: [existingObj],
    });
    expect(rejected.action).toBe("none");
  });
});
