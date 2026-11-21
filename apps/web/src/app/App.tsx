import { lazy, Suspense, useEffect, useState } from "react";
import {
  type DemoBundle,
  kindColors,
  kindLabels,
  loadDemo,
  utcLabel,
} from "./demo";

const Globe = lazy(() => import("../globe/EarthView"));
type LoadState =
  { status: "loading" | "error" } | { status: "ready"; demo: DemoBundle };

export function App() {
  const [state, setState] = useState<LoadState>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const demo = state.status === "ready" ? state.demo : undefined;
  const selected = demo?.objects.find((object) => object.id === selectedId);
  const selectedState = demo?.states.states.find(
    (sample) => sample.object_id === selectedId,
  );

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
        <span className="source-status" role="status">
          {demo
            ? "Synthetic demo"
            : state.status === "error"
              ? "API unavailable"
              : "Connecting to API"}
        </span>
      </header>
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
              states={demo?.states.states}
              objects={demo?.objects}
              selectedId={selectedId}
            />
          </Suspense>
          <div className="scene-label">
            <h1 id="scene-title">Earth orbit</h1>
            <p>{demo ? utcLabel(demo.states.at_utc) : "Awaiting a snapshot"}</p>
          </div>
          <small className="credit">Natural Earth</small>
        </section>
        <aside className="catalog" aria-labelledby="catalog-title">
          <div className="catalog-header">
            <h2 id="catalog-title">Demo catalog</h2>
            {demo && <span>{demo.catalog.records} objects</span>}
          </div>
          {state.status === "loading" && (
            <p role="status">Loading the local snapshot…</p>
          )}
          {state.status === "error" && (
            <div className="failure">
              <p role="alert">
                The local API is unavailable. Start the API and try again.
              </p>
              <button onClick={retry}>Retry</button>
            </div>
          )}
          {demo &&
            (demo.objects.length ? (
              <ul className="objects">
                {demo.objects.map((object) => (
                  <li key={object.id}>
                    <button
                      aria-pressed={selectedId === object.id}
                      onClick={() =>
                        setSelectedId((current) =>
                          current === object.id ? null : object.id,
                        )
                      }
                    >
                      <span
                        className="object-dot"
                        style={{ backgroundColor: kindColors[object.kind] }}
                      />
                      <span>{object.name}</span>
                      <span className="object-kind">
                        {kindLabels[object.kind]}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>No objects in this snapshot.</p>
            ))}
          <div className="object-detail" aria-live="polite">
            <h3>{selected?.name ?? "Object details"}</h3>
            {selected ? (
              <dl>
                <dt>Object ID</dt>
                <dd>{selected.id}</dd>
                <dt>Frame</dt>
                <dd>{demo?.states.frame}</dd>
                <dt>Position</dt>
                <dd>
                  {selectedState?.position
                    .map((coordinate) => (coordinate / 1000).toFixed(1))
                    .join(", ") ?? "Unavailable"}
                  {selectedState && " km"}
                </dd>
              </dl>
            ) : (
              <p>Select an object to see its example position.</p>
            )}
          </div>
        </aside>
      </main>
      <footer>
        Educational simulation. This snapshot uses fictional objects and example
        coordinates.
      </footer>
    </div>
  );
}
