/**
 * Results panel — TASK-005 Lane D.
 *
 * Shows collision results with occupancy chart, encounters table,
 * entry crossings, and provenance.  Handles loading/error/empty states.
 */
import { useEffect, useState } from "react";
import type { ScenarioResult } from "./api";
import { fetchResults, fetchReport } from "./api";
import { OccupancyChart } from "./OccupancyChart";
import { EncountersTable } from "./EncountersTable";
import { EntryCrossingsList } from "./EntryCrossingsList";
import { ProvenanceBadge } from "./ProvenanceBadge";

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; result: ScenarioResult };

interface ResultsPanelProps {
  scenarioId: string | null;
  onResult?: (result: ScenarioResult) => void;
}

export function ResultsPanel({ scenarioId, onResult }: ResultsPanelProps) {
  const [state, setState] = useState<LoadState>({ status: "idle" });
  const [reportMd, setReportMd] = useState<string | null>(null);
  const [showReport, setShowReport] = useState(false);

  useEffect(() => {
    if (!scenarioId) {
      setState({ status: "idle" });
      return;
    }
    setState({ status: "loading" });
    const ctrl = new AbortController();
    fetchResults(scenarioId, ctrl.signal)
      .then((result) => {
        if (ctrl.signal.aborted) return;
        setState({ status: "ready", result });
        onResult?.(result);
      })
      .catch((err) => {
        if (!ctrl.signal.aborted)
          setState({ status: "error", message: err.message });
      });
    return () => ctrl.abort();
  }, [scenarioId, onResult]);

  async function handleExport() {
    if (!scenarioId) return;
    try {
      const md = await fetchReport(scenarioId, "markdown");
      setReportMd(md as string);
      setShowReport(true);
    } catch {
      setReportMd("Failed to load report.");
      setShowReport(true);
    }
  }

  if (state.status === "idle") {
    return (
      <section className="results-panel results--empty" aria-label="Results">
        <h2>Impact Intelligence</h2>
        <p className="results-hint">
          Run a collision scenario to see exposure results here.
        </p>
      </section>
    );
  }

  if (state.status === "loading") {
    return (
      <section className="results-panel results--loading" aria-label="Results">
        <h2>Impact Intelligence</h2>
        <p role="status" className="results-loading">
          Loading results…
        </p>
      </section>
    );
  }

  if (state.status === "error") {
    return (
      <section className="results-panel results--error" aria-label="Results">
        <h2>Impact Intelligence</h2>
        <p role="alert" className="results-error">
          ⚠ {state.message}
        </p>
      </section>
    );
  }

  const { result } = state;
  const isEmpty =
    result.occupancy.length === 0 &&
    result.encounters.length === 0 &&
    result.entry_crossings.length === 0;

  return (
    <section className="results-panel results--ready" aria-label="Results">
      <div className="results-header">
        <h2>Impact Intelligence</h2>
        <span className="results-scenario-badge">
          ⚠ HYPOTHETICAL SIMULATION
        </span>
      </div>

      <ProvenanceBadge provenance={result.provenance} />

      {isEmpty ? (
        <p className="results-empty">
          No occupancy, encounters, or entry crossings in this scenario result.
        </p>
      ) : (
        <>
          {/* Fragment summary */}
          <div className="results-summary">
            <dl>
              <dt>Resolved fragments</dt>
              <dd>{result.resolved_fragment_count}</dd>
              <dt>Unresolved mass</dt>
              <dd>
                {result.unresolved_mass_kg != null
                  ? `${result.unresolved_mass_kg.toFixed(1)} kg`
                  : "—"}
              </dd>
              <dt>Encounters</dt>
              <dd>{result.encounters.length}</dd>
              <dt>Entry crossings</dt>
              <dd>{result.entry_crossings.length}</dd>
            </dl>
          </div>

          {/* Occupancy chart */}
          {result.occupancy.length > 0 && (
            <OccupancyChart bins={result.occupancy} />
          )}

          {/* Encounters table */}
          {result.encounters.length > 0 && (
            <EncountersTable encounters={result.encounters} />
          )}

          {/* Entry crossings */}
          {result.entry_crossings.length > 0 && (
            <EntryCrossingsList crossings={result.entry_crossings} />
          )}
        </>
      )}

      {/* Export button */}
      <div className="results-actions">
        <button onClick={handleExport} className="btn-export">
          Export Report
        </button>
      </div>

      {/* Report overlay */}
      {showReport && reportMd && (
        <div
          className="report-overlay"
          role="dialog"
          aria-label="Scenario Report"
        >
          <div className="report-content">
            <div className="report-toolbar">
              <h3>Scenario Report</h3>
              <button onClick={() => setShowReport(false)}>Close</button>
            </div>
            <pre className="report-md">{reportMd}</pre>
          </div>
        </div>
      )}
    </section>
  );
}
