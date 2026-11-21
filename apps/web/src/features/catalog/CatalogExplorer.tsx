import { useEffect, useState } from "react";
import { kindColors, kindLabels, utcLabel } from "../../app/demo";
import {
  type CatalogObject,
  type CatalogStatus,
  type ObjectDetail,
  type ObjectKind,
  type OperationalStatus,
  type RenderStates,
  fetchCatalogStatus,
  fetchObjectDetail,
  fetchRenderStates,
  formatSourceAge,
  modeBadgeLabel,
  refreshCatalog,
  searchObjects,
} from "./catalogApi";

type Props = {
  selectedId: string | null;
  onSelectId: (id: string | null) => void;
  onCatalogStateChange?: (payload: {
    status: CatalogStatus | null;
    objects: CatalogObject[];
    renderStates: RenderStates | null;
  }) => void;
};

const WARNING_LABELS: Record<string, string> = {
  SYNTHETIC_ONLY: "Synthetic offline demo fixture",
  CACHED_SNAPSHOT: "Using persisted local cache",
  PROVIDER_UNAVAILABLE: "CelesTrak unavailable; fallback active",
  STALE_ELEMENTS: "Orbital elements older than 24h",
  PARTIAL_CATALOG_COVERAGE: "Subset of documented CelesTrak groups",
  DECAYED_OBJECTS_FILTERED: "Decayed objects excluded",
  DUPLICATE_EPOCH_CONFLICT: "Duplicate records resolved by newest epoch",
  SATCAT_UNAVAILABLE: "SATCAT metadata unavailable",
};

export function CatalogExplorer({
  selectedId,
  onSelectId,
  onCatalogStateChange,
}: Props) {
  const [status, setStatus] = useState<CatalogStatus | null>(null);
  const [items, setItems] = useState<CatalogObject[]>([]);
  const [total, setTotal] = useState(0);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [renderStates, setRenderStates] = useState<RenderStates | null>(null);
  const [detail, setDetail] = useState<ObjectDetail | null>(null);

  const [query, setQuery] = useState("");
  const [kind, setKind] = useState<ObjectKind | "">("");
  const [opStatus, setOpStatus] = useState<OperationalStatus | "">("");

  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [refreshNote, setRefreshNote] = useState<string | null>(null);
  const [reloadNonce, setReloadNonce] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError(null);

    Promise.all([
      fetchCatalogStatus(controller.signal),
      searchObjects(
        { query, kind, operationalStatus: opStatus, limit: 50 },
        controller.signal,
      ),
      fetchRenderStates({ scope: "visible", limit: 200 }, controller.signal),
    ])
      .then(([catStatus, page, states]) => {
        setStatus(catStatus);
        setItems(page.items);
        setTotal(page.total);
        setNextCursor(page.next_cursor);
        setRenderStates(states);
        onCatalogStateChange?.({
          status: catStatus,
          objects: page.items,
          renderStates: states,
        });
      })
      .catch((err: unknown) => {
        if (!controller.signal.aborted) {
          setError(
            err instanceof Error ? err.message : "Catalog API unavailable",
          );
          onCatalogStateChange?.({
            status: null,
            objects: [],
            renderStates: null,
          });
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [query, kind, opStatus, reloadNonce]);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    const controller = new AbortController();
    fetchObjectDetail(selectedId, controller.signal)
      .then(setDetail)
      .catch(() => {
        if (!controller.signal.aborted) setDetail(null);
      });
    return () => controller.abort();
  }, [selectedId]);

  async function handleLoadMore() {
    if (!nextCursor || loadingMore) return;
    setLoadingMore(true);
    try {
      const page = await searchObjects({
        query,
        kind,
        operationalStatus: opStatus,
        limit: 50,
        cursor: nextCursor,
      });
      setItems((prev) => [...prev, ...page.items]);
      setNextCursor(page.next_cursor);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Could not load more objects",
      );
    } finally {
      setLoadingMore(false);
    }
  }

  async function handleRefresh() {
    if (refreshing) return;
    setRefreshing(true);
    setRefreshNote(null);
    try {
      const result = await refreshCatalog();
      setStatus(result.status);
      setRefreshNote(result.message);
      setReloadNonce((n) => n + 1);
    } catch (err: unknown) {
      setRefreshNote(err instanceof Error ? err.message : "Refresh failed");
    } finally {
      setRefreshing(false);
    }
  }

  const selectedState = renderStates?.states.find(
    (s) => s.object_id === selectedId,
  );
  const selectedObj = detail?.object ?? items.find((o) => o.id === selectedId);

  return (
    <aside className="catalog" aria-labelledby="catalog-title">
      <div className="catalog-header">
        <h2 id="catalog-title">Catalog explorer</h2>
        {status && (
          <span>
            {total} / {status.records} objects
          </span>
        )}
      </div>

      {status && (
        <div className="catalog-source-bar">
          <div className="catalog-source-row">
            <span className={`mode-pill mode-${status.mode.toLowerCase()}`}>
              {modeBadgeLabel(status.mode)}
            </span>
            <span className="source-age">
              {status.fetched_at
                ? `Fetched ${formatSourceAge(status.fetched_at)}`
                : "Offline fixture"}
            </span>
          </div>
          {status.element_epoch_max && (
            <p className="source-meta">
              Latest element epoch: {utcLabel(status.element_epoch_max)}
            </p>
          )}
          {status.warning_codes.length > 0 && (
            <ul className="warning-list" aria-label="Catalog warnings">
              {status.warning_codes.map((code) => (
                <li key={code}>{WARNING_LABELS[code] ?? code}</li>
              ))}
            </ul>
          )}
          <div className="refresh-row">
            <button
              type="button"
              className="refresh-button"
              onClick={handleRefresh}
              disabled={refreshing}
            >
              {refreshing ? "Refreshing…" : "Refresh CelesTrak"}
            </button>
          </div>
          {refreshNote && (
            <p className="refresh-note" role="status">
              {refreshNote}
            </p>
          )}
        </div>
      )}

      <div className="catalog-filters">
        <label className="sr-only" htmlFor="catalog-search">
          Search by name or NORAD ID
        </label>
        <input
          id="catalog-search"
          type="search"
          className="catalog-search-input"
          placeholder="Search name or NORAD ID (e.g. 25544)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="filter-row">
          <select
            aria-label="Filter by object kind"
            value={kind}
            onChange={(e) => setKind(e.target.value as ObjectKind | "")}
          >
            <option value="">All kinds</option>
            <option value="PAYLOAD">Satellite</option>
            <option value="DEBRIS">Debris</option>
            <option value="ROCKET_BODY">Rocket body</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
          <select
            aria-label="Filter by operational status"
            value={opStatus}
            onChange={(e) =>
              setOpStatus(e.target.value as OperationalStatus | "")
            }
          >
            <option value="">All status</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="UNKNOWN">Unknown</option>
          </select>
        </div>
      </div>

      {loading && <p role="status">Loading catalog…</p>}

      {error && (
        <div className="failure">
          <p role="alert">{error}</p>
          <button type="button" onClick={() => setReloadNonce((n) => n + 1)}>
            Retry
          </button>
        </div>
      )}

      {!loading &&
        !error &&
        (items.length ? (
          <>
            <ul className="objects">
              {items.map((object) => (
                <li key={object.id}>
                  <button
                    type="button"
                    aria-pressed={selectedId === object.id}
                    onClick={() =>
                      onSelectId(selectedId === object.id ? null : object.id)
                    }
                  >
                    <span
                      className="object-dot"
                      style={{ backgroundColor: kindColors[object.kind] }}
                    />
                    <span className="object-name-col">
                      <span>{object.name}</span>
                      <small className="object-id-sub">{object.id}</small>
                    </span>
                    <span className="object-kind">
                      {kindLabels[object.kind]}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
            {nextCursor && (
              <button
                type="button"
                className="load-more-button"
                onClick={handleLoadMore}
                disabled={loadingMore}
              >
                {loadingMore ? "Loading…" : "Load more"}
              </button>
            )}
          </>
        ) : (
          <p className="empty-state">
            No objects match the current search or filters.
          </p>
        ))}

      <div className="object-detail" aria-live="polite">
        <h3>{selectedObj?.name ?? "Object details"}</h3>
        {selectedObj ? (
          <dl>
            <dt>Catalog ID</dt>
            <dd>{selectedObj.id}</dd>
            <dt>Status</dt>
            <dd>{selectedObj.operational_status}</dd>
            <dt>Source</dt>
            <dd>{selectedObj.state_source}</dd>
            <dt>Element epoch</dt>
            <dd>
              {selectedObj.element_epoch_utc
                ? `${utcLabel(selectedObj.element_epoch_utc)}${detail?.is_stale ? " (stale)" : ""}`
                : "Synthetic"}
            </dd>
            <dt>Orbit model</dt>
            <dd>
              {selectedObj.orbit
                ? `${selectedObj.orbit.theory} (${selectedObj.orbit.frame})`
                : "Static fixture"}
            </dd>
            <dt>Mass / radius</dt>
            <dd>{selectedObj.physical_properties_basis}</dd>
            {detail?.satcat?.rcs_m2 !== null &&
              detail?.satcat?.rcs_m2 !== undefined && (
                <>
                  <dt>SATCAT RCS</dt>
                  <dd>{detail.satcat.rcs_m2} m² (not mass/radius)</dd>
                </>
              )}
            <dt>Position ({renderStates?.frame ?? "ITRS"})</dt>
            <dd>
              {selectedState?.position
                .map((coordinate) => (coordinate / 1000).toFixed(1))
                .join(", ") ?? "Not in visible batch"}
              {selectedState && " km"}
            </dd>
          </dl>
        ) : (
          <p>
            Select an object to inspect its source, epoch, and propagated state.
          </p>
        )}
      </div>
    </aside>
  );
}
