import { describe, expect, it } from "vitest";
import demoFixture from "../../../../data/fixtures/demo.json";
import type { DemoBundle } from "../app/demo";
import { createReplaySessionDriver } from "../app/useReplaySession";
import { fpsFromFrames, renderScale } from "../globe/quality";
import {
  classifyFramePage,
  detectImpact,
  fetchAllFrames,
  type FramePage,
} from "./frameSource";
import type { FrameSample } from "./interpolation";
import { syntheticFrames } from "./syntheticFrames";

const provenance: FramePage["provenance"] = {
  kind: "HYPOTHETICAL_SIMULATION",
  mode: "DEMO",
  source: "test",
  assumptions: [],
  limitations: [],
  coordinateFrame: "ITRS",
};
const page = (
  samples: FrameSample[],
  next: string | null = null,
): FramePage => ({
  schema_version: "1.0",
  generated_at_utc: "2026-01-01T00:00:00Z",
  scenario_id: "s",
  frame: "ITRS",
  position_unit: "m",
  sample_step_seconds: 5,
  next_cursor: next,
  samples,
  provenance,
});
const sample = (t: number, ids: string[]): FrameSample => ({
  at_utc: new Date(t).toISOString(),
  positions: ids.map((id, i) => ({ object_id: id, position: [i, 0, 0] })),
});

describe("classifyFramePage", () => {
  it("is empty for a single sample or no positions", () => {
    expect(classifyFramePage(page([sample(0, [])])).status).toBe("empty");
    expect(
      classifyFramePage(page([sample(0, []), sample(1000, [])])).status,
    ).toBe("empty");
  });
  it("is ready with two populated samples", () => {
    expect(
      classifyFramePage(page([sample(0, ["a"]), sample(1000, ["a"])])).status,
    ).toBe("ready");
  });
});

describe("detectImpact", () => {
  it("returns null when samples are empty or fewer than minBirths objects exist", () => {
    expect(detectImpact([])).toBeNull();
    expect(
      detectImpact([sample(0, ["only-one"]), sample(1000, ["only-one"])]),
    ).toBeNull();
  });
  it("detects first-frame impact when the collision runner starts with all fragments in sample 0", () => {
    const firstFrameSamples: FrameSample[] = [
      {
        at_utc: "2026-11-21T12:00:00Z",
        positions: [
          { object_id: "FRAG-001", position: [6_871_000, 100, -200] },
          { object_id: "FRAG-002", position: [6_871_000, 300, 200] },
          { object_id: "FRAG-003", position: [6_871_000, 500, 0] },
        ],
      },
      {
        at_utc: "2026-11-21T12:01:00Z",
        positions: [
          { object_id: "FRAG-001", position: [6_850_000, 12_000, -5_000] },
          { object_id: "FRAG-002", position: [6_890_000, -8_000, 4_000] },
          { object_id: "FRAG-003", position: [6_870_000, 20_000, 1_000] },
        ],
      },
    ];
    const hit = detectImpact(firstFrameSamples);
    expect(hit).toEqual({
      timeMs: Date.parse("2026-11-21T12:00:00Z"),
      position: [6_871_000, 300, 0],
    });
  });
  it("prefers authoritative impact epoch and ITRS-meter position when coordinated from TASK-003", () => {
    const firstFrameSamples: FrameSample[] = [
      sample(Date.parse("2026-11-21T12:00:00Z"), ["FRAG-1", "FRAG-2"]),
      sample(Date.parse("2026-11-21T12:01:00Z"), ["FRAG-1", "FRAG-2"]),
    ];
    const hit = detectImpact(firstFrameSamples, 2, {
      atUtc: "2026-11-21T12:00:00Z",
      position: [6_900_000, -150_000, 420_000],
    });
    expect(hit).toEqual({
      timeMs: Date.parse("2026-11-21T12:00:00Z"),
      position: [6_900_000, -150_000, 420_000],
    });
  });
  it("finds mid-timeline fragment births and their centroid", () => {
    const hit = detectImpact([
      sample(0, ["a", "b"]),
      sample(1000, ["a", "f1", "f2"]),
    ]);
    expect(hit?.timeMs).toBe(1000);
    expect(hit?.position).toEqual([1.5, 0, 0]);
  });
  it("finds the impact in the synthetic fixture", () => {
    expect(detectImpact(syntheticFrames())).not.toBeNull();
  });
});

describe("fetchAllFrames", () => {
  it("follows cursors and joins pages", async () => {
    const pages = [
      page([sample(0, ["a"])], "c1"),
      page([sample(1000, ["a"])], null),
    ];
    const urls: string[] = [];
    const fake = (async (url: string) => {
      urls.push(url);
      return new Response(JSON.stringify(pages[urls.length - 1]));
    }) as unknown as typeof fetch;
    const result = await fetchAllFrames(
      "s 1",
      new AbortController().signal,
      fake,
    );
    expect(result.samples).toHaveLength(2);
    expect(urls[0]).toBe("/api/v1/scenarios/s%201/frames");
    expect(urls[1]).toContain("cursor=c1");
  });
  it("rejects on HTTP errors", async () => {
    const fake = (async () =>
      new Response("no", { status: 404 })) as unknown as typeof fetch;
    await expect(
      fetchAllFrames("s", new AbortController().signal, fake),
    ).rejects.toThrow("404");
  });
});

describe("completed-run replay session integration", () => {
  it("fetches two paginated frame pages for a completed run and drives play, scrub, reset, impact focus, and separate synthetic preview", async () => {
    const t0 = Date.parse("2026-11-21T12:00:00Z");
    const t1 = Date.parse("2026-11-21T12:01:00Z");
    const t2 = Date.parse("2026-11-21T12:02:00Z");

    const page1: FramePage = {
      ...page(
        [
          {
            at_utc: "2026-11-21T12:00:00Z",
            positions: [
              { object_id: "FRAG-A", position: [7_000_000, 0, 0] },
              { object_id: "FRAG-B", position: [7_000_000, 2_000, 0] },
            ],
          },
          {
            at_utc: "2026-11-21T12:01:00Z",
            positions: [
              { object_id: "FRAG-A", position: [7_060_000, 0, 0] },
              { object_id: "FRAG-B", position: [7_000_000, 62_000, 0] },
            ],
          },
        ],
        "cursor-page-2",
      ),
      scenario_id: "demo-preset-01",
      sample_step_seconds: 60,
    };

    const page2: FramePage = {
      ...page(
        [
          {
            at_utc: "2026-11-21T12:02:00Z",
            positions: [
              { object_id: "FRAG-A", position: [7_120_000, 0, 0] },
              { object_id: "FRAG-B", position: [7_000_000, 122_000, 0] },
            ],
          },
        ],
        null,
      ),
      scenario_id: "demo-preset-01",
      sample_step_seconds: 60,
    };

    const requestedUrls: string[] = [];
    const fakeFetch = (async (input: string | URL | Request) => {
      const url = String(input);
      requestedUrls.push(url);
      if (url === "/api/v1/scenarios/demo-preset-01/frames") {
        return new Response(JSON.stringify(page1), { status: 200 });
      }
      if (
        url === "/api/v1/scenarios/demo-preset-01/frames?cursor=cursor-page-2"
      ) {
        return new Response(JSON.stringify(page2), { status: 200 });
      }
      return new Response("not found", { status: 404 });
    }) as typeof fetch;

    // Foundation demo bundle still has 1 empty sample in demo.frames, while job is completed.
    const completedDemo: DemoBundle = {
      ...(demoFixture as unknown as DemoBundle),
      job: {
        ...(demoFixture.job as unknown as DemoBundle["job"]),
        state: "completed",
      },
    };

    const driver = await createReplaySessionDriver({
      loadStatus: "ready",
      demo: completedDemo,
      previewing: false,
      options: { fetchImpl: fakeFetch },
    });

    expect(requestedUrls).toEqual([
      "/api/v1/scenarios/demo-preset-01/frames",
      "/api/v1/scenarios/demo-preset-01/frames?cursor=cursor-page-2",
    ]);

    const initial = driver.snapshot();
    expect(initial.framesState.status).toBe("ready");
    expect(initial.replayable).toBe(true);
    expect(initial.clock.startMs).toBe(t0);
    expect(initial.clock.endMs).toBe(t2);
    expect(initial.positions.get("FRAG-A")).toEqual([7_000_000, 0, 0]);
    expect(initial.positions.get("FRAG-B")).toEqual([7_000_000, 2_000, 0]);
    // First-frame impact detected and camera auto-focused at t0.
    expect(initial.hasImpact).toBe(true);
    expect(initial.impact?.position).toEqual([7_000_000, 1_000, 0]);
    expect(initial.focusToken).toBe(1);

    // Play and advance 30s (halfway between sample 0 and sample 1 on page 1).
    driver.play();
    const afterPlayTick = driver.tick(30_000);
    expect(afterPlayTick.clock.timeMs).toBe(t0 + 30_000);
    expect(afterPlayTick.positions.get("FRAG-A")).toEqual([7_030_000, 0, 0]);
    expect(afterPlayTick.positions.get("FRAG-B")).toEqual([
      7_000_000, 32_000, 0,
    ]);

    // Scrub into page 2 (t2) and verify returned page 2 positions are used.
    const afterScrub = driver.seek(t2);
    expect(afterScrub.clock.timeMs).toBe(t2);
    expect(afterScrub.positions.get("FRAG-A")).toEqual([7_120_000, 0, 0]);
    expect(afterScrub.positions.get("FRAG-B")).toEqual([7_000_000, 122_000, 0]);
    // Halfway between t1 (page 1) and t2 (page 2).
    const betweenPages = driver.seek(t1 + 30_000);
    expect(betweenPages.positions.get("FRAG-A")).toEqual([7_090_000, 0, 0]);
    expect(betweenPages.positions.get("FRAG-B")).toEqual([
      7_000_000, 92_000, 0,
    ]);

    // Reset returns to sample 0 on page 1.
    const afterReset = driver.reset();
    expect(afterReset.clock.timeMs).toBe(t0);
    expect(afterReset.clock.playing).toBe(false);
    expect(afterReset.positions.get("FRAG-A")).toEqual([7_000_000, 0, 0]);
    expect(afterReset.positions.get("FRAG-B")).toEqual([7_000_000, 2_000, 0]);

    // Synthetic preview remains an explicit separate mode and does not overwrite completed-run frames.
    const inPreview = driver.setPreviewing(true);
    expect(inPreview.provenance?.kind).toBe("SYNTHETIC_DEMO");
    expect(inPreview.positions.has("SYN-A")).toBe(true);
    expect(inPreview.positions.has("FRAG-A")).toBe(false);

    const restored = driver.setPreviewing(false);
    expect(restored.provenance?.kind).toBe("HYPOTHETICAL_SIMULATION");
    expect(restored.positions.get("FRAG-A")).toEqual([7_000_000, 0, 0]);
  });
});

describe("render quality helpers", () => {
  it("targets device pixel ratio capped at 2, 1 on low graphics", () => {
    expect(renderScale(false, 1)).toBe(1);
    expect(renderScale(false, 1.25)).toBe(1);
    expect(renderScale(false, 3)).toBeCloseTo(2 / 3);
    expect(renderScale(true, 2)).toBe(0.5);
    expect(renderScale(true, 1)).toBe(1);
  });
  it("computes fps from frame timestamps", () => {
    expect(fpsFromFrames([0, 100, 200, 300])).toBe(10);
    expect(fpsFromFrames([5])).toBeNull();
  });
});
