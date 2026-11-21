import type { EntryCrossing } from "../features/results/api";
import type { FrameSample, Vec3 } from "./interpolation";

export const CELL_DEGREES = 5;
export type EntryCell = { west: number; south: number; count: number };
export type FragmentTrack = { id: string; points: Vec3[] };

export function countEntryCells(
  entries: readonly EntryCrossing[],
): EntryCell[] {
  const cells = new Map<string, EntryCell>();
  const seen = new Set<string>();
  for (const entry of entries) {
    if (seen.has(entry.fragment_id)) continue;
    seen.add(entry.fragment_id);
    const longitude = entry.longitude_deg === 180 ? -180 : entry.longitude_deg;
    const west = Math.floor(longitude / CELL_DEGREES) * CELL_DEGREES;
    const south = Math.min(
      85,
      Math.floor(entry.latitude_deg / CELL_DEGREES) * CELL_DEGREES,
    );
    const key = `${west}:${south}`;
    const cell = cells.get(key);
    if (cell) cell.count += 1;
    else cells.set(key, { west, south, count: 1 });
  }
  return [...cells.values()];
}

export function recentTracks(
  frames: readonly FrameSample[],
  index: number,
  tailSamples: number,
  limit: number,
): FragmentTrack[] {
  const visible = frames[index]?.positions ?? [];
  const tracks = new Map<string, Vec3[]>();
  const stride = Math.max(1, Math.ceil(visible.length / limit));
  for (let i = 0; i < visible.length; i += stride) {
    const point = visible[i];
    if (point) tracks.set(point.object_id, []);
  }
  for (const frame of frames.slice(
    Math.max(0, index - tailSamples + 1),
    index + 1,
  )) {
    for (const point of frame.positions) {
      tracks.get(point.object_id)?.push(point.position);
    }
  }
  return [...tracks]
    .filter(([, points]) => points.length >= 2)
    .map(([id, points]) => ({ id, points }));
}
