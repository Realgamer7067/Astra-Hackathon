import {
  lazy,
  type ReactNode,
  Suspense,
  useCallback,
  useEffect,
  useMemo,
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
import { countEntryCells, recentTracks } from "../timeline/entryReplay";
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
  const [approachRun, setApproachRun] = useState<{ scenarioId: string }>();
  const finishApproach = useCallback(() => setApproachRun(undefined), []);
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
  const watchingApproach = Boolean(
    approachRun &&
    activeResult?.scenario_id === approachRun.scenarioId &&
    approach,
  );

  function watchCollision() {
    if (!activeResult) return;
    session.replay.reset();
    session.replay.setSpeed(15);
    session.focusImpact();
    setEntryFocus(undefined);
    setApproachRun({ scenarioId: activeResult.scenario_id });
  }

  function focusFirstEntry() {
    setApproachRun(undefined);
    if (!activeResult || !entries?.length) return;
    const first = entries.reduce((earliest, entry) =>
      Date.parse(entry.at_utc) < Date.parse(earliest.at_utc) ? entry : earliest,
    );
    session.replay.pause();
    session.replay.seek(Date.parse(first.at_utc));
    setShowEntryMap(true);
    setEntryFocus({
      scenarioId: activeResult.scenario_id,
      entry: { ...first },
    });
  }

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
          <section className="viewport" aria-labelledby="scene-title">
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
                  session.replayable ? session.replay.positions : undefined
                }
                impact={session.impact}
                tracks={tracks}
                approach={
                  watchingApproach ? (approach ?? undefined) : undefined
                }
                onApproachComplete={() => {
                  finishApproach();
                  session.replay.play();
                }}
                entryCells={showEntryMap ? entryCells : undefined}
                entryFocus={entryFocusForRun}
                focusToken={session.focusToken}
                lowGraphics={lowGraphics}
              />
            </Suspense>
            <div className="scene-label">
              <h1 id="scene-title">Earth orbit</h1>
              <p>
                {renderStates
                  ? `${utcLabel(renderStates.at_utc)} · visual sizes exaggerated`
                  : "Awaiting orbital snapshot"}
              </p>
            </div>
            <ReplayBar
              session={session}
              previewing={previewing}
              onPreviewChange={setPreviewing}
              lowGraphics={lowGraphics}
              onLowGraphicsChange={setLowGraphics}
              onRetry={retry}
            >
              {activeResult && (
                <div className="entry-controls">
                  {approach && (
                    <button
                      onClick={watchCollision}
                      disabled={!session.hasImpact || watchingApproach}
                    >
                      Watch asteroid collision
                    </button>
                  )}
                  {watchingApproach && (
                    <small role="status">
                      Cyan satellite · amber asteroid · illustrative approach
                    </small>
                  )}
                  {entryCells.length > 0 ? (
                    <>
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
                      <button
                        onClick={focusFirstEntry}
                        disabled={!computedFrames}
                      >
                        Focus first entry
                      </button>
                      <small>
                        {entries?.length} modeled entries at 120 km. Peak{" "}
                        {Math.max(...entryCells.map((cell) => cell.count))} per
                        5° cell. Surface arrivals unmodeled.
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
          : demo && <ScenarioLab demo={demo} />}
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
