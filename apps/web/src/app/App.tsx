import { lazy, Suspense, useCallback, useState } from "react";
import { utcLabel } from "./demo";
import { CatalogExplorer } from "../features/catalog/CatalogExplorer";
import {
  type CatalogObject,
  type CatalogStatus,
  type RenderStates,
  modeBadgeLabel,
} from "../features/catalog/catalogApi";

const Globe = lazy(() => import("../globe/EarthView"));

export function App() {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [catalogStatus, setCatalogStatus] = useState<CatalogStatus | null>(
    null,
  );
  const [catalogObjects, setCatalogObjects] = useState<CatalogObject[]>([]);
  const [renderStates, setRenderStates] = useState<RenderStates | null>(null);

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

  return (
    <div className="workspace" data-ui>
      <header className="masthead">
        <div className="wordmark">
          <span className="orbit-mark" aria-hidden="true" />
          ASTRA
        </div>
        <span className="product-name">Orbital Collision Lab</span>
        <span className="source-status" role="status">
          {catalogStatus
            ? modeBadgeLabel(catalogStatus.mode)
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
              states={renderStates?.states}
              objects={catalogObjects}
              selectedId={selectedId}
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
          <small className="credit">Natural Earth</small>
        </section>
        <CatalogExplorer
          selectedId={selectedId}
          onSelectId={setSelectedId}
          onCatalogStateChange={handleCatalogStateChange}
        />
      </main>
      <footer>
        Educational research simulation. Catalog positions are estimates;
        collision scenarios and impact trajectories are hypothetical unless
        explicitly stated otherwise. Not for spacecraft operations or emergency
        decisions.
      </footer>
    </div>
  );
}
