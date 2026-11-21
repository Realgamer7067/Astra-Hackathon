import {
  lazy,
  type ReactNode,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import ReplayBar from "../timeline/ReplayBar";
import { ReplayHandoffContext } from "../timeline/ReplayHandoffContext";
import { CatalogExplorer } from "../features/catalog/CatalogExplorer";
import {
  type CatalogObject,
  type CatalogStatus,
  type RenderStates,
  modeBadgeLabel,
} from "../features/catalog/catalogApi";
import { ResultsPanel } from "../features/results";
import type { EntryCrossing, ScenarioResult } from "../features/results/api";
import {
  countEntryCells,
  presentationSpeed,
  recentTracks,
} from "../timeline/entryReplay";
import { findSegment, sampleTimes } from "../timeline/interpolation";
import { ScenarioLab } from "../features/scenarios/ScenarioLab";
import "../features/results/results.css";
import { type DemoBundle, loadDemo, utcLabel } from "./demo";
import {
  type ReplaySessionOptions,
  type ScenarioCompletionCallback,
  useReplaySession,
} from "./useReplaySession";

const Globe = lazy(() => import("../globe/EarthView"));
const stageTitles = {
  approach: "Before collision",
  contact: "Contact",
  debris: "Debris dispersal",
  entry: "Atmospheric entries from above",
};
type Stage = keyof typeof stageTitles;
type LoadState =
  { status: "loading" | "error" } | { status: "ready"; demo: DemoBundle };

export function App(
  props: {
    activeScenarioId?: string | null;
    replayOptions?: ReplaySessionOptions;
    renderScenarioPanel?: (
      onScenarioCompleted: ScenarioCompletionCallback,
    ) => ReactNode;
  } = {},
) {
  const [previewing, setPreviewing] = useState(false);
  const [lowGraphics, setLowGraphics] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<ScenarioResult | null>(
    null,
  );
  const [showEntryMap, setShowEntryMap] = useState(true);
  const [presentation, setPresentation] = useState<{
    scenarioId: string;
    stage: Stage;
  }>();
  const lastStarted = useRef<string | null>(null);
  const viewport = useRef<HTMLElement>(null);
  const [demoActionHost, setDemoActionHost] = useState<HTMLDivElement | null>(
    null,
  );
  const [entryFocus, setEntryFocus] = useState<{
    scenarioId: string;
    entry: EntryCrossing;
  }>();
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatus | null>(
    null,
  );
  const [catalogObjects, setCatalogObjects] = useState<CatalogObject[]>([]);
  const [renderStates, setRenderStates] = useState<RenderStates | null>(null);
  const demo = state.status === "ready" ? state.demo : undefined;

  const handleCatalogStateChange = useCallback(
    (payload: {
      status: CatalogStatus | null;
      objects: CatalogObject[];
      renderStates: RenderStates | null;
    }) => {
      setCatalogStatus(payload.status);
      setCatalogObjects(payload.objects);
      setRenderStates(payload.renderStates);
    },
    [],
  );

  const onScenarioActivated = useCallback(() => {
    setPreviewing(false);
  }, []);

  const replayOptions = useMemo<ReplaySessionOptions>(
    () => ({
      ...props.replayOptions,
      onScenarioActivated: (run) => {
        onScenarioActivated();
        props.replayOptions?.onScenarioActivated?.(run);
      },
    }),
    [props.replayOptions, onScenarioActivated],
  );

  const session = useReplaySession(
    state.status,
    demo,
    previewing,
    replayOptions,
  );

  const legacyScenarioId =
    typeof window === "undefined"
      ? null
      : new URLSearchParams(window.location.search).get("scenarioId")?.trim() ||
        null;
  const currentScenarioId =
    props.activeScenarioId ??
    session.completedScenarioId ??
    legacyScenarioId ??
    demo?.result.scenario_id ??
    null;

  const computedFrames =
    !previewing &&
    session.completedScenarioId &&
    session.framesState.status === "ready"
      ? session.framesState.samples
      : null;
  const frameTimes = useMemo(
    () => sampleTimes(computedFrames ?? []),
    [computedFrames],
  );
  const frameIndex = findSegment(frameTimes, session.replay.clock.timeMs);
  const tracks = useMemo(
    () =>
      computedFrames
        ? recentTracks(computedFrames, frameIndex, 12, lowGraphics ? 12 : 48)
        : undefined,
    [computedFrames, frameIndex, lowGraphics],
  );
  const activeResult =
    !previewing &&
    session.completedScenarioId &&
    scenarioResult?.scenario_id === session.completedScenarioId
      ? scenarioResult
      : null;
  const entries = activeResult?.entry_crossings;
  const entryCells = useMemo(() => countEntryCells(entries ?? []), [entries]);
  const entryFocusForRun =
    activeResult && entryFocus?.scenarioId === activeResult.scenario_id
      ? entryFocus.entry
      : undefined;

  const approach = activeResult?.contact_approach_itrs_m;
  const activeId = activeResult?.scenario_id;
  const stage =
    activeId && presentation?.scenarioId === activeId
      ? presentation.stage
      : undefined;
  const prelude = stage === "approach" || stage === "contact";
  const firstEntry = useMemo(
    () =>
      entries?.length
        ? entries.reduce((earliest, entry) =>
            Date.parse(entry.at_utc) < Date.parse(earliest.at_utc)
              ? entry
              : earliest,
          )
        : undefined,
    [entries],
  );
  const firstEntryMs = firstEntry ? Date.parse(firstEntry.at_utc) : null;
  const { clock, reset, pause, seek, play, setSpeed } = session.replay;
  const entryStill =
    stage === "entry" &&
    showEntryMap &&
    !clock.playing &&
    clock.timeMs === firstEntryMs;

  const watchCollision = useCallback(
    (scenarioId: string) => {
      reset();
      setEntryFocus(undefined);
      setShowEntryMap(true);
      setPresentation({ scenarioId, stage: "approach" });
      const bounds = viewport.current?.getBoundingClientRect();
      if (bounds && (bounds.top < 0 || bounds.top >= window.innerHeight))
        viewport.current?.scrollIntoView({ block: "start" });
    },
    [reset],
  );

  useEffect(() => {
    if (
      !activeId ||
      !approach ||
      !computedFrames ||
      !session.hasImpact ||
      lastStarted.current === activeId
    )
      return;
    lastStarted.current = activeId;
    watchCollision(activeId);
  }, [activeId, approach, computedFrames, session.hasImpact, watchCollision]);

  const arriveAtContact = useCallback(() => {
    setPresentation((current) =>
      current?.stage === "approach"
        ? { ...current, stage: "contact" }
        : current,
    );
  }, []);

  const startDebris = useCallback(() => {
    if (!activeId) return;
    setPresentation({ scenarioId: activeId, stage: "debris" });
    setSpeed(presentationSpeed(clock.startMs, firstEntryMs));
    play();
  }, [activeId, clock.startMs, firstEntryMs, play, setSpeed]);

  useEffect(() => {
    if (stage !== "contact") return;
    const timer = window.setTimeout(startDebris, 800);
    return () => window.clearTimeout(timer);
  }, [stage, startDebris]);

  const focusFirstEntry = useCallback(() => {
    if (!activeId || !firstEntry || firstEntryMs === null) return;
    pause();
    seek(firstEntryMs);
    setShowEntryMap(true);
    setPresentation({ scenarioId: activeId, stage: "entry" });
    setEntryFocus({ scenarioId: activeId, entry: { ...firstEntry } });
  }, [activeId, firstEntry, firstEntryMs, pause, seek]);

  useEffect(() => {
    if (
      stage === "debris" &&
      firstEntryMs !== null &&
      clock.timeMs >= firstEntryMs
    ) {
      focusFirstEntry();
    }
  }, [stage, firstEntryMs, clock.timeMs, focusFirstEntry]);

  useEffect(() => {
    const controller = new AbortController();
    loadDemo(AbortSignal.any([controller.signal, AbortSignal.timeout(5000)]))
      .then((demo) => setState({ status: "ready", demo }))
      .catch(() => {
        if (!controller.signal.aborted) setState({ status: "error" });
      });
    return () => controller.abort();
  }, [attempt]);

  function retry() {
    setState({ status: "loading" });
    setAttempt((previous) => previous + 1);
  }

  return (
    <div className="workspace" data-ui>
      <header className="masthead">
        <div className="wordmark">
          <span className="orbit-mark" aria-hidden="true" />
          ASTRA
        </div>
        <span className="product-name">Orbital Collision Lab</span>
        {demo && !props.renderScenarioPanel && (
          <a className="scenario-jump" href="#collision-lab">
            Collision lab
          </a>
        )}
        <span className="source-status" role="status">
          {catalogStatus
            ? modeBadgeLabel(catalogStatus.mode)
            : state.status === "error"
              ? "API unavailable"
              : "Connecting to API"}
        </span>
      </header>
      <ReplayHandoffContext.Provider value={session.onScenarioCompleted}>
        <main className="console">
          <section
            ref={viewport}
            className="viewport"
            aria-labelledby="scene-title"
          >
            <div className="scene-pane">
              <Suspense
                fallback={
                  <p className="globe-state" role="status">
                    Loading Earth…
                  </p>
                }
              >
                <Globe
                  states={renderStates?.states}
                  objects={catalogObjects}
                  selectedId={selectedId}
                  replayPositions={
                    session.replayable && !prelude && !entryStill
                      ? session.replay.positions
                      : undefined
                  }
                  impact={
                    stage === "approach" && session.impact
                      ? { ...session.impact, ageMs: null }
                      : session.impact
                  }
                  tracks={prelude || entryStill ? undefined : tracks}
                  approach={
                    stage === "approach" ? (approach ?? undefined) : undefined
                  }
                  onApproachComplete={arriveAtContact}
                  collisionCue={stage === "contact"}
                  followDebris={stage === "debris" && clock.playing}
                  entryCells={
                    showEntryMap && (!stage || stage === "entry")
                      ? entryCells
                      : undefined
                  }
                  entryFocus={entryFocusForRun}
                  entryOverview={stage === "entry" ? entryCells : undefined}
                  focusToken={session.focusToken}
                  lowGraphics={lowGraphics}
                />
              </Suspense>
              <div className="scene-label">
                <h1 id="scene-title">Earth orbit</h1>
                <p>
                  {renderStates
                    ? `Snapshot · ${utcLabel(renderStates.at_utc)}`
                    : "Awaiting orbital snapshot"}
                </p>
                {demo && !props.renderScenarioPanel && (
                  <div ref={setDemoActionHost} className="scene-actions" />
                )}
                {stage && (
                  <div
                    className="replay-stage"
                    role="status"
                    data-replay-stage={stage}
                  >
                    <strong>{stageTitles[stage]}</strong>
                    {stage === "approach" && (
                      <span>
                        Illustrative approach · models enlarged for visibility
                      </span>
                    )}
                    {stage === "contact" && (
                      <span>Forced contact · simulated breakup begins</span>
                    )}
                    {stage === "debris" && (
                      <span>Computed 3D fragment paths</span>
                    )}
                    {stage === "entry" && (
                      <span>Modeled crossings at 120 km</span>
                    )}
                  </div>
                )}
              </div>
            </div>
            <ReplayBar
              session={session}
              previewing={previewing}
              onPreviewChange={setPreviewing}
              lowGraphics={lowGraphics}
              onLowGraphicsChange={setLowGraphics}
              onRetry={retry}
              timelineLocked={prelude}
              onRestart={
                activeId && approach
                  ? () => watchCollision(activeId)
                  : undefined
              }
            >
              {activeResult && (
                <div className="entry-controls">
                  {approach && (
                    <button
                      onClick={() => watchCollision(activeResult.scenario_id)}
                      disabled={!session.hasImpact || prelude}
                    >
                      Replay from approach
                    </button>
                  )}
                  {prelude && (
                    <button onClick={startDebris}>Skip to debris</button>
                  )}
                  {entryCells.length > 0 ? (
                    <>
                      {(!stage || stage === "entry") && (
                        <label>
                          <input
                            type="checkbox"
                            checked={showEntryMap}
                            onChange={(event) =>
                              setShowEntryMap(event.target.checked)
                            }
                          />
                          Entry heatmap
                        </label>
                      )}
                      <button
                        onClick={focusFirstEntry}
                        disabled={!computedFrames || prelude}
                      >
                        View entry zone
                      </button>
                      <small>
                        {entries?.length} modeled entries at 120 km. Peak{" "}
                        {Math.max(...entryCells.map((cell) => cell.count))} per
                        5° cell. Marker size reflects count.
                      </small>
                    </>
                  ) : (
                    <small>
                      No fragments crossed the modeled atmosphere boundary.
                    </small>
                  )}
                </div>
              )}
            </ReplayBar>
          </section>
          <CatalogExplorer
            selectedId={selectedId}
            onSelectId={setSelectedId}
            onCatalogStateChange={handleCatalogStateChange}
          >
            <ResultsPanel
              key={currentScenarioId}
              scenarioId={currentScenarioId}
              onResult={setScenarioResult}
            />
          </CatalogExplorer>
        </main>
        {props.renderScenarioPanel
          ? props.renderScenarioPanel(session.onScenarioCompleted)
          : demo && (
              <ScenarioLab
                demo={demo}
                demoActionHost={stage ? null : demoActionHost}
              />
            )}
      </ReplayHandoffContext.Provider>
      <footer>
        Educational research simulation. Catalog positions are estimates;
        collision scenarios and impact trajectories are hypothetical unless
        explicitly stated otherwise. Not for spacecraft operations or emergency
        decisions.
      </footer>
    </div>
  );
}
