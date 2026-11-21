import { describe, expect, it } from "vitest";
import {
  atEnd,
  createClock,
  pause,
  play,
  progress,
  reset,
  seek,
  setSpeed,
  tick,
} from "./clock";
import {
  findSegment,
  interpolateFrames,
  sampleTimes,
  type FrameSample,
} from "./interpolation";

const samples: FrameSample[] = [
  {
    at_utc: "2026-01-01T00:00:00Z",
    positions: [
      { object_id: "A", position: [0, 0, 0] },
      { object_id: "F", position: [10, 0, 0] },
    ],
  },
  {
    at_utc: "2026-01-01T00:00:10Z",
    positions: [{ object_id: "A", position: [100, 200, 300] }],
  },
];
const times = sampleTimes(samples) as [number, number];

describe("clock", () => {
  const base = createClock(0, 1000);
  it("rejects invalid intervals", () => {
    expect(() => createClock(5, 1)).toThrow(RangeError);
  });
  it("only advances while playing, scaled by speed", () => {
    expect(tick(base, 100).timeMs).toBe(0);
    const running = setSpeed(play(base), 5);
    expect(tick(running, 100).timeMs).toBe(500);
  });
  it("is deterministic regardless of tick subdivision", () => {
    const running = play(base);
    const one = tick(running, 200);
    const two = tick(tick(running, 100), 100);
    expect(two.timeMs).toBe(one.timeMs);
  });
  it("pauses at the end and restarts on play", () => {
    const done = tick(play(base), 5000);
    expect(done.timeMs).toBe(1000);
    expect(done.playing).toBe(false);
    expect(atEnd(done)).toBe(true);
    expect(play(done).timeMs).toBe(0);
  });
  it("clamps scrubbing and ignores bad input", () => {
    expect(seek(base, -5).timeMs).toBe(0);
    expect(seek(base, 9999).timeMs).toBe(1000);
    expect(seek(base, NaN)).toBe(base);
    expect(setSpeed(base, 0)).toBe(base);
  });
  it("pauses and resets", () => {
    const running = tick(play(base), 400);
    expect(pause(running).playing).toBe(false);
    expect(reset(running).timeMs).toBe(0);
    expect(progress(running)).toBeCloseTo(0.4);
  });
});

describe("interpolation", () => {
  it("finds segments by binary search", () => {
    expect(findSegment([0, 10, 20], 15)).toBe(1);
    expect(findSegment([0, 10, 20], -1)).toBe(0);
    expect(findSegment([0, 10, 20], 99)).toBe(2);
    expect(findSegment([], 1)).toBe(-1);
  });
  it("matches samples exactly at boundaries", () => {
    const at = interpolateFrames(samples, times, times[0]);
    expect(at.get("A")).toEqual([0, 0, 0]);
    expect(at.get("F")).toEqual([10, 0, 0]);
  });
  it("interpolates linearly between samples", () => {
    const mid = interpolateFrames(samples, times, times[0] + 5000);
    expect(mid.get("A")).toEqual([50, 100, 150]);
  });
  it("holds a terminated object until its last sample, then hides it", () => {
    expect(interpolateFrames(samples, times, times[0] + 9000).get("F")).toEqual(
      [10, 0, 0],
    );
    expect(interpolateFrames(samples, times, times[1]).has("F")).toBe(false);
  });
  it("does not extrapolate past the last sample", () => {
    const after = interpolateFrames(samples, times, times[1] + 99999);
    expect(after.get("A")).toEqual([100, 200, 300]);
  });
});
