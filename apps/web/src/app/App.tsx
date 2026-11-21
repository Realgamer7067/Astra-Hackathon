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
            />
          </section>
          <CatalogExplorer
            selectedId={selectedId}
            onSelectId={setSelectedId}
            onCatalogStateChange={handleCatalogStateChange}
          >
            <ResultsPanel
              key={currentScenarioId}
              scenarioId={currentScenarioId}
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
