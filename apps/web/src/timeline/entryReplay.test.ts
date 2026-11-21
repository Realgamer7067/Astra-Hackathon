import { expect, it } from "vitest";
import { countEntryCells, recentTracks } from "./entryReplay";
import type { FrameSample } from "./interpolation";

it("counts only unique modeled entries and keeps the date line in one column", () => {
  const entry = (id: string, longitude: number) => ({
    fragment_id: id,
    longitude_deg: longitude,
    latitude_deg: 90,
    threshold_altitude_km: 120,
    at_utc: "2026-11-21T12:00:00Z",
  });
  expect(
    countEntryCells([entry("a", 180), entry("a", 180), entry("b", -180)]),
  ).toEqual([{ west: -180, south: 85, count: 2 }]);
});

it("builds bounded, chronological trails only for currently visible fragments", () => {
  const frames: FrameSample[] = [0, 1, 2].map((i) => ({
    at_utc: new Date(i * 1000).toISOString(),
    positions:
      i === 2
        ? [{ object_id: "active", position: [i, 0, 0] }]
        : [
            { object_id: "active", position: [i, 0, 0] },
            { object_id: "ended", position: [i, 1, 0] },
          ],
  }));
  expect(recentTracks(frames, 2, 2, 1)).toEqual([
    {
      id: "active",
      points: [
        [1, 0, 0],
        [2, 0, 0],
      ],
    },
  ]);
});
