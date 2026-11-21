import type { components } from "../../../../packages/contracts/api";

export type FrameSample = components["schemas"]["FrameSample"];
export type Vec3 = [number, number, number];

/** Index of the last sample with time <= t (clamped to the valid range). */
export function findSegment(times: readonly number[], t: number): number {
  if (times.length === 0) return -1;
  let low = 0;
  let high = times.length - 1;
  while (low < high) {
    const mid = (low + high + 1) >> 1;
    if ((times[mid] as number) <= t) low = mid;
    else high = mid - 1;
  }
  return low;
}

export const sampleTimes = (samples: readonly FrameSample[]): number[] =>
  samples.map((sample) => Date.parse(sample.at_utc));

const lerp = (a: Vec3, b: Vec3, f: number): Vec3 => [
  a[0] + (b[0] - a[0]) * f,
  a[1] + (b[1] - a[1]) * f,
  a[2] + (b[2] - a[2]) * f,
];

/**
 * Positions (ITRS, metres) at time t by linear interpolation between the two
 * bracketing server samples. An object absent from the next sample (for example
 * a terminated fragment) holds its last sampled position until that sample and
 * is then no longer shown. Replay never extrapolates beyond server samples.
 */
export function interpolateFrames(
  samples: readonly FrameSample[],
  times: readonly number[],
  t: number,
): Map<string, Vec3> {
  const result = new Map<string, Vec3>();
  const index = findSegment(times, t);
  if (index < 0) return result;
  const current = samples[index];
  const t0 = times[index];
  if (!current || t0 === undefined) return result;
  const next = samples[index + 1];
  const t1 = times[index + 1];
  if (!next || t1 === undefined || t <= t0) {
    for (const p of current.positions) result.set(p.object_id, [...p.position]);
    return result;
  }
  const fraction = (t - t0) / (t1 - t0);
  const upcoming = new Map(next.positions.map((p) => [p.object_id, p]));
  for (const p of current.positions) {
    const target = upcoming.get(p.object_id);
    result.set(
      p.object_id,
      target ? lerp(p.position, target.position, fraction) : [...p.position],
    );
  }
  return result;
}
