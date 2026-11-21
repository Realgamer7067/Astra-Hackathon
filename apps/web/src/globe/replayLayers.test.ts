import { PolylineCollection } from "cesium";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import { drawTracks } from "./replayLayers";

beforeEach(() => {
  // Cesium checks browser texture constructors before recognizing Color uniforms.
  for (const name of [
    "HTMLCanvasElement",
    "HTMLImageElement",
    "ImageBitmap",
    "OffscreenCanvas",
  ]) {
    vi.stubGlobal(name, class {});
  }
});
afterEach(() => vi.unstubAllGlobals());

it("reuses trail slots while Cesium retains independent material ownership", () => {
  const lines = new PolylineCollection();
  drawTracks(lines, [
    {
      id: "a",
      points: [
        [7_000_000, 0, 0],
        [7_000_000, 10, 0],
      ],
    },
    {
      id: "b",
      points: [
        [7_000_000, 0, 0],
        [7_000_000, 0, 10],
      ],
    },
  ]);
  expect(lines.get(0).material).not.toBe(lines.get(1).material);
  const retained = lines.get(0);
  drawTracks(lines, [
    {
      id: "b",
      points: [
        [7_000_000, 0, 0],
        [7_000_000, 0, 20],
      ],
    },
  ]);
  expect(lines.get(0)).toBe(retained);
  expect(lines.get(1).show).toBe(false);
  drawTracks(lines, []);
  expect(lines.get(0).show).toBe(false);
  expect(() => lines.destroy()).not.toThrow();
});
