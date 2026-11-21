import { useEffect, useMemo, useRef, useState } from "react";
import {
  classifyFramePage,
  detectImpact,
  type FramesState,
  type Provenance,
} from "../timeline/frameSource";
import type { FrameSample } from "../timeline/interpolation";
import { syntheticFrames } from "../timeline/syntheticFrames";
import { useReplay } from "../timeline/useReplay";
import type { DemoBundle } from "./demo";

const NO_FRAMES: FrameSample[] = [];
const SYNTHETIC_SEED = 20260101;
/** Decorative-burst rebuild interval; avoids reallocating points every frame. */
const BURST_STEP_MS = 66;

export const syntheticProvenance: Provenance = {
  kind: "SYNTHETIC_DEMO",
  mode: "DEMO",
  source: "ASTRA in-browser preview generator",
  assumptions: [],
  limitations: ["Illustrative motion only; not a simulation result."],
  coordinateFrame: "ITRS",
};

/**
 * Chooses the frames to replay (real FRAMES-v1 from the API bundle, or the
 * explicitly labelled synthetic preview), derives the impact event from them
 * and focuses the camera when playback first reaches it.
 */
export function useReplaySession(
  loadStatus: "loading" | "error" | "ready",
  demo: DemoBundle | undefined,
  previewing: boolean,
) {
  const synthetic = useMemo(() => syntheticFrames(), []);
  const framesState: FramesState = demo
    ? classifyFramePage(demo.frames)
    : loadStatus === "error"
      ? { status: "error", message: "The local API is unavailable." }
      : { status: "loading" };
  const samples = previewing
    ? synthetic
    : framesState.status === "ready"
      ? framesState.samples
      : NO_FRAMES;
  const replay = useReplay(samples);
  const site = useMemo(() => detectImpact(samples), [samples]);

  const rawAge =
    site && replay.clock.timeMs >= site.timeMs
      ? replay.clock.timeMs - site.timeMs
      : null;
  const ageMs =
    rawAge === null ? null : Math.floor(rawAge / BURST_STEP_MS) * BURST_STEP_MS;
  const seed = previewing ? SYNTHETIC_SEED : (demo?.job.seed ?? 0);
  const impact = useMemo(
    () => (site ? { position: site.position, seed, ageMs } : undefined),
    [site, seed, ageMs],
  );

  const [focusToken, setFocusToken] = useState(0);
  const focused = useRef(false);
  useEffect(() => {
    focused.current = false;
  }, [site]);
  useEffect(() => {
    if (!site) return;
    if (ageMs === null) focused.current = false;
    else if (!focused.current) {
      focused.current = true;
      setFocusToken((n) => n + 1);
    }
  }, [site, ageMs]);

  const provenance = previewing
    ? syntheticProvenance
    : framesState.status === "ready" || framesState.status === "empty"
      ? framesState.provenance
      : undefined;

  return {
    replay,
    framesState,
    impact,
    hasImpact: site !== null,
    focusToken,
    focusImpact: () => setFocusToken((n) => n + 1),
    provenance,
    replayable: previewing || framesState.status === "ready",
  };
}
