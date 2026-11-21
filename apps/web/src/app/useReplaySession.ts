import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  createClock,
  pause as pauseClock,
  play as playClock,
  reset as resetClock,
  seek as seekClock,
  setSpeed as setClockSpeed,
  tick as tickClock,
  type ClockState,
} from "../timeline/clock";
import {
  type AuthoritativeImpact,
  classifyFramePage,
  detectImpact,
  fetchAllFrames,
  type FramePage,
  type FramesState,
  type Provenance,
} from "../timeline/frameSource";
import {
  interpolateFrames,
  sampleTimes,
  type FrameSample,
  type Vec3,
} from "../timeline/interpolation";
import { syntheticFrames } from "../timeline/syntheticFrames";
import { useReplay } from "../timeline/useReplay";
import type { DemoBundle } from "./demo";

const NO_FRAMES: FrameSample[] = [];
export const SYNTHETIC_SEED = 20260101;
/** Decorative-burst rebuild interval; avoids reallocating points every frame. */
export const BURST_STEP_MS = 66;

export const syntheticProvenance: Provenance = {
  kind: "SYNTHETIC_DEMO",
  mode: "DEMO",
  source: "ASTRA in-browser preview generator",
  assumptions: [],
  limitations: ["Illustrative motion only; not a simulation result."],
  coordinateFrame: "ITRS",
};

export type CompletedRunInput = {
  scenarioId: string;
  seed?: number;
  impact?: AuthoritativeImpact | null;
};

export type ReplaySessionOptions = {
  scenarioId?: string | null;
  seed?: number;
  impact?: AuthoritativeImpact | null;
  fetchImpl?: typeof fetch;
};

export type LoadedScenarioFrames = {
  scenarioId: string;
  state: FramesState;
  page?: FramePage;
};

function initialUrlScenarioId(): string | null {
  if (typeof window === "undefined") return null;
  const value = new URLSearchParams(window.location.search)
    .get("scenario_id")
    ?.trim();
  return value ? value : null;
}

export function resolveCompletedScenarioId(
  demo: DemoBundle | undefined,
  options?: ReplaySessionOptions,
  eventRun?: CompletedRunInput | null,
): string | null {
  return (
    options?.scenarioId ??
    eventRun?.scenarioId ??
    (demo?.job.state === "completed" ? demo.job.scenario_id : null)
  );
}

export async function loadScenarioFrames(
  scenarioId: string,
  signal: AbortSignal,
  fetchImpl: typeof fetch = fetch,
): Promise<LoadedScenarioFrames> {
  try {
    const page = await fetchAllFrames(scenarioId, signal, fetchImpl);
    return {
      scenarioId,
      state: classifyFramePage(page),
      page,
    };
  } catch (err: unknown) {
    const message =
      err instanceof Error ? err.message : "Replay frames unavailable.";
    return {
      scenarioId,
      state: { status: "error", message },
    };
  }
}

export function resolveFramesState(
  loadStatus: "loading" | "error" | "ready",
  demo: DemoBundle | undefined,
  completedScenarioId: string | null,
  fetchedFrames: LoadedScenarioFrames | null,
): FramesState {
  if (completedScenarioId) {
    return fetchedFrames?.scenarioId === completedScenarioId
      ? fetchedFrames.state
      : { status: "loading" };
  }
  if (demo) return classifyFramePage(demo.frames);
  if (loadStatus === "error") {
    return { status: "error", message: "The local API is unavailable." };
  }
  return { status: "loading" };
}

export function resolveAuthoritativeImpact(
  previewing: boolean,
  demo: DemoBundle | undefined,
  completedScenarioId: string | null,
  fetchedPage: FramePage | undefined,
  options?: ReplaySessionOptions,
  eventRun?: CompletedRunInput | null,
): AuthoritativeImpact | null {
  if (previewing) return null;
  const explicit = options?.impact ?? eventRun?.impact;
  if (explicit) return explicit;
  const atUtc =
    (demo?.job.scenario_id === completedScenarioId
      ? demo?.scenario.epoch_utc
      : undefined) ??
    fetchedPage?.provenance.sourceEpochUtc ??
    demo?.frames.provenance.sourceEpochUtc ??
    null;
  return atUtc ? { atUtc } : null;
}

/**
 * Headless integration driver for a replay session. Shares the exact frame
 * loader, clock, interpolation, impact detector, and mode-switching logic used
 * by the useReplaySession React hook.
 */
export async function createReplaySessionDriver(params: {
  loadStatus?: "loading" | "error" | "ready";
  demo?: DemoBundle;
  previewing?: boolean;
  options?: ReplaySessionOptions;
}) {
  const synthetic = syntheticFrames();
  let previewing = params.previewing ?? false;
  const loadStatus = params.loadStatus ?? "ready";
  const demo = params.demo;
  const options = params.options;
  const completedScenarioId = resolveCompletedScenarioId(demo, options, null);
  let fetchedFrames: LoadedScenarioFrames | null = null;

  if (completedScenarioId) {
    fetchedFrames = await loadScenarioFrames(
      completedScenarioId,
      new AbortController().signal,
      options?.fetchImpl ?? fetch,
    );
  }

  const currentSamples = (): FrameSample[] => {
    if (previewing) return synthetic;
    const state = resolveFramesState(
      loadStatus,
      demo,
      completedScenarioId,
      fetchedFrames,
    );
    return state.status === "ready" ? state.samples : NO_FRAMES;
  };

  let samples = currentSamples();
  let times = sampleTimes(samples);
  let clock: ClockState = createClock(
    times[0] ?? 0,
    times[times.length - 1] ?? 0,
  );
  let focusToken = 0;
  let focused = false;

  const computeSite = () =>
    detectImpact(
      samples,
      2,
      resolveAuthoritativeImpact(
        previewing,
        demo,
        completedScenarioId,
        fetchedFrames?.page,
        options,
        null,
      ),
    );

  const syncFocus = () => {
    const site = computeSite();
    if (!site) return;
    if (clock.timeMs < site.timeMs) {
      focused = false;
    } else if (!focused) {
      focused = true;
      focusToken += 1;
    }
  };
  syncFocus();

  const snapshot = () => {
    const framesState = resolveFramesState(
      loadStatus,
      demo,
      completedScenarioId,
      fetchedFrames,
    );
    const site = computeSite();
    const rawAge =
      site && clock.timeMs >= site.timeMs ? clock.timeMs - site.timeMs : null;
    const ageMs =
      rawAge === null
        ? null
        : Math.floor(rawAge / BURST_STEP_MS) * BURST_STEP_MS;
    const seed = previewing
      ? SYNTHETIC_SEED
      : (options?.seed ?? demo?.job.seed ?? 0);
    const positions: Map<string, Vec3> = interpolateFrames(
      samples,
      times,
      clock.timeMs,
    );
    const provenance = previewing
      ? syntheticProvenance
      : framesState.status === "ready" || framesState.status === "empty"
        ? framesState.provenance
        : undefined;
    return {
      clock,
      positions,
      framesState,
      completedScenarioId,
      site,
      impact: site ? { position: site.position, seed, ageMs } : undefined,
      hasImpact: site !== null,
      focusToken,
      provenance,
      previewing,
      replayable: previewing || framesState.status === "ready",
    };
  };

  return {
    snapshot,
    play: () => {
      clock = playClock(clock);
      syncFocus();
      return snapshot();
    },
    pause: () => {
      clock = pauseClock(clock);
      return snapshot();
    },
    tick: (wallDeltaMs: number) => {
      clock = tickClock(clock, wallDeltaMs);
      syncFocus();
      return snapshot();
    },
    seek: (timeMs: number) => {
      clock = seekClock(clock, timeMs);
      syncFocus();
      return snapshot();
    },
    reset: () => {
      clock = resetClock(clock);
      syncFocus();
      return snapshot();
    },
    setSpeed: (speed: number) => {
      clock = setClockSpeed(clock, speed);
      return snapshot();
    },
    setPreviewing: (next: boolean) => {
      previewing = next;
      samples = currentSamples();
      times = sampleTimes(samples);
      clock = createClock(times[0] ?? 0, times[times.length - 1] ?? 0);
      focused = false;
      syncFocus();
      return snapshot();
    },
    focusImpact: () => {
      focusToken += 1;
      return snapshot();
    },
  };
}

/**
 * Connects completed collision runs to GET /api/v1/scenarios/{id}/frames via
 * fetchAllFrames(), while keeping the synthetic preview as an explicit separate
 * mode. Coordinates authoritative impact epoch/position with TASK-003 (including
 * first-frame impact where sample 0 already contains all fragments) and focuses
 * the camera when playback reaches impact.
 */
export function useReplaySession(
  loadStatus: "loading" | "error" | "ready",
  demo: DemoBundle | undefined,
  previewing: boolean,
  options?: ReplaySessionOptions,
) {
  const synthetic = useMemo(() => syntheticFrames(), []);
  const [eventRun, setEventRun] = useState<CompletedRunInput | null>(() => {
    const fromUrl = initialUrlScenarioId();
    return fromUrl ? { scenarioId: fromUrl } : null;
  });
  const [fetchAttempt, setFetchAttempt] = useState(0);
  const [fetchedFrames, setFetchedFrames] =
    useState<LoadedScenarioFrames | null>(null);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onCompleted = (event: Event) => {
      const detail = (event as CustomEvent<CompletedRunInput | undefined>)
        .detail;
      if (detail?.scenarioId) {
        setEventRun(detail);
      }
    };
    window.addEventListener("astra:scenario-completed", onCompleted);
    return () =>
      window.removeEventListener("astra:scenario-completed", onCompleted);
  }, []);

  const completedScenarioId = resolveCompletedScenarioId(
    demo,
    options,
    eventRun,
  );
  const fetchImpl = options?.fetchImpl ?? fetch;

  useEffect(() => {
    if (!completedScenarioId) {
      setFetchedFrames(null);
      return;
    }
    const controller = new AbortController();
    setFetchedFrames({
      scenarioId: completedScenarioId,
      state: { status: "loading" },
    });
    loadScenarioFrames(completedScenarioId, controller.signal, fetchImpl).then(
      (loaded) => {
        if (!controller.signal.aborted) setFetchedFrames(loaded);
      },
    );
    return () => controller.abort();
  }, [completedScenarioId, fetchAttempt, fetchImpl]);

  const retryFrames = useCallback(() => {
    setFetchAttempt((n) => n + 1);
  }, []);

  const loadScenario = useCallback((run: CompletedRunInput | null) => {
    setEventRun(run);
  }, []);

  const framesState = resolveFramesState(
    loadStatus,
    demo,
    completedScenarioId,
    fetchedFrames,
  );

  const samples = previewing
    ? synthetic
    : framesState.status === "ready"
      ? framesState.samples
      : NO_FRAMES;

  const replay = useReplay(samples);

  const authoritativeImpact = useMemo(
    () =>
      resolveAuthoritativeImpact(
        previewing,
        demo,
        completedScenarioId,
        fetchedFrames?.page,
        options,
        eventRun,
      ),
    [
      previewing,
      demo,
      completedScenarioId,
      fetchedFrames?.page,
      options,
      eventRun,
    ],
  );

  const site = useMemo(
    () => detectImpact(samples, 2, authoritativeImpact),
    [samples, authoritativeImpact],
  );

  const rawAge =
    site && replay.clock.timeMs >= site.timeMs
      ? replay.clock.timeMs - site.timeMs
      : null;
  const ageMs =
    rawAge === null ? null : Math.floor(rawAge / BURST_STEP_MS) * BURST_STEP_MS;
  const seed = previewing
    ? SYNTHETIC_SEED
    : (options?.seed ?? eventRun?.seed ?? demo?.job.seed ?? 0);
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
    completedScenarioId,
    impact,
    hasImpact: site !== null,
    focusToken,
    focusImpact: () => setFocusToken((n) => n + 1),
    retryFrames,
    loadScenario,
    provenance,
    replayable: previewing || framesState.status === "ready",
  };
}
