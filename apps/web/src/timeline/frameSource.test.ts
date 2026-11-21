import { describe, expect, it } from "vitest";
import {
  classifyFramePage,
  detectImpact,
  fetchAllFrames,
  type FramePage,
} from "./frameSource";
import type { FrameSample } from "./interpolation";
import { syntheticFrames } from "./syntheticFrames";
import { fpsFromFrames, renderScale } from "../globe/quality";

const provenance: FramePage["provenance"] = {
  kind: "SYNTHETIC_DEMO",
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
  it("returns null without a fragment birth", () => {
    expect(
      detectImpact([sample(0, ["a", "b"]), sample(1000, ["a", "b"])]),
    ).toBeNull();
  });
  it("finds the first fragment-birth sample and its centroid", () => {
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
