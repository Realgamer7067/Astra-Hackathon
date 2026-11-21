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

export type ImpactSite = { timeMs: number; position: Vec3 };

/**
 * Impact event from frame data: the first sample where several objects appear
 * that were absent from the previous sample (a fragment cloud being born). The
 * site is the centroid of those new objects. This relies on FRAMES-v1 emitting
 * fragments only from the collision onward; the contract has no explicit
 * impact time/position yet, so this is a derived value and null when no such
 * event exists.
 */
export function detectImpact(
  samples: readonly FrameSample[],
  minBirths = 2,
): ImpactSite | null {
  for (let i = 1; i < samples.length; i++) {
    const previous = new Set(samples[i - 1]!.positions.map((p) => p.object_id));
    const births = samples[i]!.positions.filter(
      (p) => !previous.has(p.object_id),
    );
    if (births.length < minBirths) continue;
    const sum: Vec3 = [0, 0, 0];
    for (const p of births)
      for (let k = 0; k < 3; k++) sum[k]! += p.position[k]!;
    return {
      timeMs: Date.parse(samples[i]!.at_utc),
      position: [
        sum[0] / births.length,
        sum[1] / births.length,
        sum[2] / births.length,
      ],
    };
  }
  return null;
}
