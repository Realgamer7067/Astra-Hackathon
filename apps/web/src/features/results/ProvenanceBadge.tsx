/**
 * Provenance badge — shows source, kind, and data lineage.
 */
import type { Provenance } from "./api";

interface ProvenanceBadgeProps {
  provenance: Provenance;
}

export function ProvenanceBadge({ provenance }: ProvenanceBadgeProps) {
  return (
    <details className="provenance-badge">
      <summary>
        <span className="prov-kind">{provenance.kind}</span>
        <span className="prov-source">{provenance.source}</span>
        {provenance.isStale && <span className="prov-stale">⚠ STALE</span>}
      </summary>
      <div className="prov-details">
        <dl>
          <dt>Mode</dt>
          <dd>{provenance.mode}</dd>
          {provenance.coordinateFrame && (
            <>
              <dt>Frame</dt>
              <dd>{provenance.coordinateFrame}</dd>
            </>
          )}
          {provenance.modelVersion && (
            <>
              <dt>Model</dt>
              <dd>{provenance.modelVersion}</dd>
            </>
          )}
          {provenance.catalogSnapshotId && (
            <>
              <dt>Snapshot</dt>
              <dd className="mono">{provenance.catalogSnapshotId}</dd>
            </>
          )}
        </dl>
        {provenance.assumptions && provenance.assumptions.length > 0 && (
          <div className="prov-section">
            <h4>Assumptions</h4>
            <ul>
              {provenance.assumptions.map((a: string, i: number) => (
                <li key={i}>{a}</li>
              ))}
            </ul>
          </div>
        )}
        {provenance.limitations && provenance.limitations.length > 0 && (
          <div className="prov-section">
            <h4>Limitations</h4>
            <ul>
              {provenance.limitations.map((l: string, i: number) => (
                <li key={i}>{l}</li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </details>
  );
}
