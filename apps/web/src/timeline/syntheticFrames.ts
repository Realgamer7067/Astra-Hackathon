import type { FrameSample } from "./interpolation";

const EARTH_RADIUS_M = 6_371_000;

/**
 * SYNTHETIC_DEMO frames for developing and checking replay UI before real
 * TASK-003 output exists. Two bodies approach, then fragments disperse on
 * circular arcs. These are decorative test data, not a simulation result and
 * must never be presented as one.
 */
export function syntheticFrames(
  startIso = "2026-01-01T00:00:00Z",
  steps = 120,
  stepSeconds = 5,
): FrameSample[] {
  const start = Date.parse(startIso);
  const samples: FrameSample[] = [];
  const impactStep = Math.floor(steps / 3);
  for (let i = 0; i <= steps; i++) {
    const positions: FrameSample["positions"] = [];
    const arc = (phase: number, radius: number, tilt: number) => {
      const r = EARTH_RADIUS_M + radius;
      return [
        r * Math.cos(phase),
        r * Math.sin(phase) * Math.cos(tilt),
        r * Math.sin(phase) * Math.sin(tilt),
      ] as [number, number, number];
    };
    const t = i * 0.006;
    if (i < impactStep) {
      positions.push(
        { object_id: "SYN-A", position: arc(t, 550_000, 0.9) },
        {
          object_id: "SYN-B",
          position: arc(
            t + ((0.008 * (impactStep - i)) / impactStep) * 10,
            550_000,
            0.9,
          ),
        },
      );
    } else {
      const age = i - impactStep;
      for (let k = 0; k < 40; k++) {
        const spread = (k / 40) * Math.PI * 2;
        positions.push({
          object_id: `SYN-FRAG-${k}`,
          position: arc(
            impactStep * 0.006 + age * (0.006 + 0.0004 * Math.cos(spread)),
            550_000 + age * 6_000 * Math.sin(spread),
            0.9 + age * 0.002 * Math.cos(spread),
          ),
        });
      }
    }
    samples.push({
      at_utc: new Date(start + i * stepSeconds * 1000).toISOString(),
      positions,
    });
  }
  return samples;
}

/** First-fragment time and centroid for the synthetic fixture (SYNTHETIC_DEMO). */
export function syntheticImpact(
  samples: readonly FrameSample[],
): { timeMs: number; position: [number, number, number] } | null {
  const hit = samples.find((s) => s.positions.length > 2);
  if (!hit) return null;
  const sum: [number, number, number] = [0, 0, 0];
  for (const p of hit.positions)
    for (let i = 0; i < 3; i++) sum[i]! += p.position[i]!;
  const n = hit.positions.length;
  return {
    timeMs: Date.parse(hit.at_utc),
    position: [sum[0] / n, sum[1] / n, sum[2] / n],
  };
}
