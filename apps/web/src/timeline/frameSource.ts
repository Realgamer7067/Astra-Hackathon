import type { components } from "../../../../packages/contracts/api";
import type { FrameSample, Vec3 } from "./interpolation";

export type FramePage = components["schemas"]["FramePage"];
export type Provenance = components["schemas"]["Provenance"];

export type FramesState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "empty"; provenance: Provenance }
  | {
      status: "ready";
      samples: FrameSample[];
      provenance: Provenance;
    };

export type ImpactSite = { timeMs: number; position: Vec3 };

/**
 * Authoritative collision impact metadata coordinated with TASK-003.
 * All positions exposed to the globe/timeline must be in ITRS meters.
 */
export type AuthoritativeImpact = {
  /** Authoritative impact UTC timestamp (e.g. scenario.epoch_utc). */
  atUtc?: string | null;
  /** Pre-parsed impact timestamp in epoch milliseconds. */
  timeMs?: number | null;
  /** Authoritative impact coordinates in ITRS meters. */
  position?: Vec3 | null;
};

/** A page is replayable only with at least two samples that contain positions. */
export function classifyFramePage(page: FramePage): FramesState {
  const populated = page.samples.filter((s) => s.positions.length > 0);
  if (page.samples.length < 2 || populated.length === 0)
    return { status: "empty", provenance: page.provenance };
  return {
    status: "ready",
    samples: page.samples,
    provenance: page.provenance,
  };
}

const MAX_PAGES = 200;

/**
 * Follows FRAMES-v1 cursors (GET /api/v1/scenarios/{id}/frames) and joins the
 * pages. Bounded by MAX_PAGES so a misbehaving server cannot loop forever.
 */
export async function fetchAllFrames(
  scenarioId: string,
  signal: AbortSignal,
  fetchImpl: typeof fetch = fetch,
): Promise<FramePage> {
  let cursor: string | null = null;
  let first: FramePage | null = null;
  const samples: FrameSample[] = [];
  for (let page = 0; page < MAX_PAGES; page++) {
    const query: string = cursor ? `?cursor=${encodeURIComponent(cursor)}` : "";
    const response = await fetchImpl(
      `/api/v1/scenarios/${encodeURIComponent(scenarioId)}/frames${query}`,
      { signal },
    );
    if (!response.ok)
      throw new Error(`Frames unavailable (${response.status})`);
    const body = (await response.json()) as FramePage;
    first ??= body;
    samples.push(...body.samples);
    cursor = body.next_cursor;
    if (!cursor) return { ...first, samples, next_cursor: null };
  }
  throw new Error("Frames exceeded the page limit");
}

function centroid(positions: readonly { position: Vec3 }[]): Vec3 {
  const sum: Vec3 = [0, 0, 0];
  for (const p of positions) {
    for (let k = 0; k < 3; k++) sum[k]! += p.position[k]!;
  }
  const n = positions.length;
  return [sum[0] / n, sum[1] / n, sum[2] / n];
}

function resolveAuthoritativeTimeMs(
  authoritative: AuthoritativeImpact | null | undefined,
  fallbackSample: FrameSample | undefined,
): number | null {
  if (
    authoritative?.timeMs !== undefined &&
    authoritative.timeMs !== null &&
    Number.isFinite(authoritative.timeMs)
  ) {
    return authoritative.timeMs;
  }
  if (authoritative?.atUtc) {
    const parsed = Date.parse(authoritative.atUtc);
    if (Number.isFinite(parsed)) return parsed;
  }
  if (fallbackSample) {
    const parsed = Date.parse(fallbackSample.at_utc);
    if (Number.isFinite(parsed)) return parsed;
  }
  return null;
}

/**
 * Resolves the collision impact time and ITRS-meter position:
 * 1. If authoritative ITRS-meter impact coordinates are supplied, uses them
 *    directly at the authoritative impact epoch (or sample 0).
 * 2. If fragments are born mid-timeline (sample i >= 1 has >= minBirths new IDs
 *    not present in sample i - 1, as in the synthetic preview), uses that
 *    birth sample's epoch and centroid.
 * 3. If an authoritative impact epoch matches a sample with >= minBirths
 *    positions, uses that sample's epoch and ITRS-meter centroid.
 * 4. First-frame impact case: TASK-003's collision runner starts propagation at
 *    impact with every fragment already present in sample 0. When sample 0 has
 *    >= minBirths objects, uses sample 0's epoch and ITRS-meter centroid.
 */
export function detectImpact(
  samples: readonly FrameSample[],
  minBirths = 2,
  authoritative?: AuthoritativeImpact | null,
): ImpactSite | null {
  if (authoritative?.position) {
    const timeMs = resolveAuthoritativeTimeMs(authoritative, samples[0]);
    if (timeMs !== null) {
      return { timeMs, position: [...authoritative.position] };
    }
  }

  if (samples.length === 0) return null;

  for (let i = 1; i < samples.length; i++) {
    const previous = new Set(samples[i - 1]!.positions.map((p) => p.object_id));
    const births = samples[i]!.positions.filter(
      (p) => !previous.has(p.object_id),
    );
    if (births.length < minBirths) continue;
    return {
      timeMs: Date.parse(samples[i]!.at_utc),
      position: centroid(births),
    };
  }

  const authTimeMs = resolveAuthoritativeTimeMs(authoritative, undefined);
  if (authTimeMs !== null) {
    const matched = samples.find(
      (s) =>
        Date.parse(s.at_utc) === authTimeMs && s.positions.length >= minBirths,
    );
    if (matched) {
      return {
        timeMs: authTimeMs,
        position: centroid(matched.positions),
      };
    }
  }

  const first = samples[0]!;
  if (first.positions.length >= minBirths) {
    return {
      timeMs: Date.parse(first.at_utc),
      position: centroid(first.positions),
    };
  }

  return null;
}
