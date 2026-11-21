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
import {
  type CompletedScenarioHandoff,
  emitScenarioCompleted,
  normalizeScenarioHandoff,
  SCENARIO_COMPLETED_EVENT,
  type ScenarioCompletionCallback,
  type ScenarioCompletionInput,
} from "../timeline/scenarioHandoff";
import { syntheticFrames } from "../timeline/syntheticFrames";
import { useReplay } from "../timeline/useReplay";
import type { DemoBundle } from "./demo";

export {
  emitScenarioCompleted,
  normalizeScenarioHandoff,
  SCENARIO_COMPLETED_EVENT,
  type CompletedScenarioHandoff,
  type ScenarioCompletionCallback,
  type ScenarioCompletionInput,
};

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

export type CompletedRunInput = CompletedScenarioHandoff;

export type ReplaySessionOptions = {
  scenarioId?: string | null;
  seed?: number;
  impact?: AuthoritativeImpact | null;
  fetchImpl?: typeof fetch;
  /** Invoked when a completed collision handoff activates replay (e.g. to exit preview). */
  onScenarioActivated?: (run: CompletedScenarioHandoff) => void;
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
  eventRun?: CompletedScenarioHandoff | null,
  urlScenarioId?: string | null,
): string | null {
  return (
    eventRun?.scenarioId ??
    options?.scenarioId ??
    urlScenarioId ??
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

/** Neutral seed used when the active run supplies none (decorative only). */
export const NEUTRAL_SEED = 0;

export type RunMetadata = {
  seed: number | undefined;
  impact: AuthoritativeImpact | null | undefined;
  /** Scenario epoch from the same run, used as a fallback impact epoch. */
  epochUtc: string | null | undefined;
};

/**
 * Seed, impact and epoch belonging to the run whose frames are active. Metadata
 * from another scenario (an earlier handoff, replay options for a different
 * scenario, or the demo bundle's job) is never reused for this run.
 */
export function resolveRunMetadata(
  completedScenarioId: string | null,
  demo: DemoBundle | undefined,
  options?: ReplaySessionOptions,
  eventRun?: CompletedScenarioHandoff | null,
  urlScenarioId?: string | null,
): RunMetadata {
  const none: RunMetadata = {
    seed: undefined,
    impact: undefined,
    epochUtc: undefined,
  };
  if (!completedScenarioId) return none;
  if (eventRun?.scenarioId === completedScenarioId) {
    return { seed: eventRun.seed, impact: eventRun.impact, epochUtc: null };
  }
  const optionsOwnRun =
    options?.scenarioId === completedScenarioId ||
    (options?.scenarioId == null &&
      !eventRun &&
      !urlScenarioId &&
      demo?.job.scenario_id === completedScenarioId);
  if (optionsOwnRun && (options?.seed !== undefined || options?.impact)) {
    return { seed: options?.seed, impact: options?.impact, epochUtc: null };
  }
  if (demo?.job.scenario_id === completedScenarioId) {
    return {
      seed: demo.job.seed,
      impact: undefined,
      epochUtc: demo.scenario.epoch_utc,
    };
  }
  return none;
}

export function resolveAuthoritativeImpact(
  previewing: boolean,
  demo: DemoBundle | undefined,
  completedScenarioId: string | null,
  fetchedPage: FramePage | undefined,
  options?: ReplaySessionOptions,
  eventRun?: CompletedScenarioHandoff | null,
  urlScenarioId?: string | null,
): AuthoritativeImpact | null {
  if (previewing) return null;
  const pageForRun =
    fetchedPage && fetchedPage.scenario_id === completedScenarioId
      ? fetchedPage
      : undefined;
  const confirmed =
    Boolean(completedScenarioId) ||
    pageForRun?.provenance.kind === "HYPOTHETICAL_SIMULATION";
  const meta = resolveRunMetadata(
    completedScenarioId,
    demo,
    options,
    eventRun,
    urlScenarioId,
  );
  if (meta.impact) {
    return { confirmed, ...meta.impact };
  }
  // No impact metadata for this run: derive it from this run's own frames,
  // optionally anchored to an epoch from the same run.
  const atUtc =
    meta.epochUtc ??
    pageForRun?.provenance.sourceEpochUtc ??
    (!completedScenarioId ? demo?.frames.provenance.sourceEpochUtc : null) ??
    null;
  if (!atUtc && !confirmed) return null;
  return { atUtc, confirmed };
}

export function resolveRunSeed(
  previewing: boolean,
  completedScenarioId: string | null,
  demo: DemoBundle | undefined,
  options?: ReplaySessionOptions,
  eventRun?: CompletedScenarioHandoff | null,
  urlScenarioId?: string | null,
): number {
  if (previewing) return SYNTHETIC_SEED;
  const meta = resolveRunMetadata(
    completedScenarioId,
    demo,
    options,
    eventRun,
    urlScenarioId,
  );
  return meta.seed ?? NEUTRAL_SEED;
}

/**
 * Headless integration driver for a replay session. Shares the exact frame
 * loader, completion handoff, clock, interpolation, impact detector, and
 * mode-switching logic used by the useReplaySession React hook.
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
  let eventRun: CompletedScenarioHandoff | null = null;
  let completedScenarioId = resolveCompletedScenarioId(demo, options, eventRun);
  let fetchedFrames: LoadedScenarioFrames | null = null;

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

  let samples: FrameSample[] = [];
  let times: number[] = [];
  let clock: ClockState = createClock(0, 0);
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
        eventRun,
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

  const resetTimelineForSamples = () => {
    samples = currentSamples();
    times = sampleTimes(samples);
    clock = createClock(times[0] ?? 0, times[times.length - 1] ?? 0);
    focused = false;
    syncFocus();
  };

  if (completedScenarioId) {
    fetchedFrames = await loadScenarioFrames(
      completedScenarioId,
      new AbortController().signal,
      options?.fetchImpl ?? fetch,
    );
  }
  resetTimelineForSamples();

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
    const seed = resolveRunSeed(
      previewing,
      completedScenarioId,
      demo,
      options,
      eventRun,
    );
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
      seed,
      site,
      impact: site ? { position: site.position, seed, ageMs } : undefined,
      hasImpact: site !== null,
      focusToken,
      provenance,
      previewing,
      replayable: previewing || framesState.status === "ready",
    };
  };

  const completeScenario = async (input: ScenarioCompletionInput) => {
    const handoff = normalizeScenarioHandoff(input);
    if (!handoff) return snapshot();
    eventRun = handoff;
    completedScenarioId = resolveCompletedScenarioId(demo, options, eventRun);
    previewing = false;
    options?.onScenarioActivated?.(handoff);
    fetchedFrames = await loadScenarioFrames(
      handoff.scenarioId,
      new AbortController().signal,
      options?.fetchImpl ?? fetch,
    );
    resetTimelineForSamples();
    return snapshot();
  };

  return {
    snapshot,
    completeScenario,
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
      resetTimelineForSamples();
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
 * mode. Accepts completed runs via:
 * - `onScenarioCompleted` callback returned by this hook (for direct React wiring),
 * - `emitScenarioCompleted(...)` / `astra:scenario-completed` window event,
 * - `options.scenarioId` prop updates,
 * - `?scenario_id=...` URL parameter, or
 * - `demo.job.state === "completed"`.
 */
export function useReplaySession(
  loadStatus: "loading" | "error" | "ready",
  demo: DemoBundle | undefined,
  previewing: boolean,
  options?: ReplaySessionOptions,
) {
  const synthetic = useMemo(() => syntheticFrames(), []);
  const [urlScenarioId] = useState<string | null>(() => initialUrlScenarioId());
  const [eventRun, setEventRun] = useState<CompletedScenarioHandoff | null>(
    null,
  );
  const [fetchAttempt, setFetchAttempt] = useState(0);
  const [fetchedFrames, setFetchedFrames] =
    useState<LoadedScenarioFrames | null>(null);

  const onActivatedRef = useRef(options?.onScenarioActivated);
  onActivatedRef.current = options?.onScenarioActivated;

  const optionScenarioId = options?.scenarioId ?? null;
  const previousOptionScenarioId = useRef<string | null>(optionScenarioId);
  useEffect(() => {
    if (optionScenarioId === previousOptionScenarioId.current) return;
    previousOptionScenarioId.current = optionScenarioId;
    if (optionScenarioId) {
      setEventRun(null);
      onActivatedRef.current?.({
        scenarioId: optionScenarioId,
        seed: options?.seed,
        impact: options?.impact,
      });
    }
  }, [optionScenarioId, options?.seed, options?.impact]);

  const onScenarioCompleted = useCallback<ScenarioCompletionCallback>(
    (input) => {
      const handoff = normalizeScenarioHandoff(input);
      if (!handoff) return;
      setEventRun(handoff);
      onActivatedRef.current?.(handoff);
    },
    [],
  );

  useEffect(() => {
    if (typeof window === "undefined") return;
    const onCompleted = (event: Event) => {
      const detail = (event as CustomEvent<ScenarioCompletionInput | undefined>)
        .detail;
      if (detail) onScenarioCompleted(detail);
    };
    window.addEventListener(SCENARIO_COMPLETED_EVENT, onCompleted);
    return () =>
      window.removeEventListener(SCENARIO_COMPLETED_EVENT, onCompleted);
  }, [onScenarioCompleted]);

  const completedScenarioId = resolveCompletedScenarioId(
    demo,
    options,
    eventRun,
    urlScenarioId,
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

  const loadScenario = useCallback(
    (run: ScenarioCompletionInput | null) => {
      if (!run) {
        setEventRun(null);
        return;
      }
      onScenarioCompleted(run);
    },
    [onScenarioCompleted],
  );

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
        urlScenarioId,
      ),
    [
      previewing,
      demo,
      completedScenarioId,
      fetchedFrames?.page,
      options,
      eventRun,
      urlScenarioId,
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
  const seed = resolveRunSeed(
    previewing,
    completedScenarioId,
    demo,
    options,
    eventRun,
    urlScenarioId,
  );
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
    onScenarioCompleted,
    provenance,
    replayable: previewing || framesState.status === "ready",
  };
}
