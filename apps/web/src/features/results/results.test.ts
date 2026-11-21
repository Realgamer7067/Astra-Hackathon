import { afterEach, describe, expect, it, vi } from "vitest";
import { fetchResults, fetchReport } from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("Results feature api", () => {
  it("fetches results successfully", async () => {
    const mockResult = {
      schema_version: "1.0",
      scenario_id: "test-scenario",
      resolved_fragment_count: 10,
      unresolved_mass_kg: null,
      modification: null,
      occupancy: [],
      encounters: [],
      entry_crossings: [],
      provenance: {
        kind: "SYNTHETIC_DEMO",
        mode: "DEMO",
        source: "test",
        assumptions: [],
        limitations: [],
      },
    };

    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify(mockResult), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      ),
    );

    const res = await fetchResults("test-scenario");
    expect(res.scenario_id).toBe("test-scenario");
    expect(res.resolved_fragment_count).toBe(10);
  });

  it("handles results fetch error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 404 })),
    );

    await expect(fetchResults("nonexistent")).rejects.toThrow(
      "Results unavailable (404)",
    );
  });

  it("fetches report in markdown format", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("# ASTRA Report\nHYPOTHETICAL SIMULATION", {
          status: 200,
          headers: { "Content-Type": "text/markdown" },
        }),
      ),
    );

    const md = await fetchReport("test-scenario", "markdown");
    expect(md).toContain("ASTRA Report");
    expect(md).toContain("HYPOTHETICAL SIMULATION");
  });
});
