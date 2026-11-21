/**
 * Close-approach encounters table.
 * Shows fragment-to-catalog-object screened separations.
 */
import type { CloseApproach } from "./api";

interface EncountersTableProps {
  encounters: CloseApproach[];
}

export function EncountersTable({ encounters }: EncountersTableProps) {
  return (
    <div className="encounters-section" aria-label="Secondary encounters">
      <h3>Secondary Encounters</h3>
      <p className="table-note">
        Screened encounters within model threshold — distances are modeled
        separations, <strong>not collision probabilities</strong>.
      </p>
      <div className="table-scroll">
        <table className="encounters-table">
          <thead>
            <tr>
              <th scope="col">Catalog Object</th>
              <th scope="col">Fragment</th>
              <th scope="col">Epoch (UTC)</th>
              <th scope="col">Separation (km)</th>
            </tr>
          </thead>
          <tbody>
            {encounters.map((enc, i) => (
              <tr key={i}>
                <td>{enc.catalog_object_id}</td>
                <td>{enc.fragment_id}</td>
                <td className="mono">
                  {new Date(enc.at_utc).toISOString().slice(0, 19)}Z
                </td>
                <td className="mono">{enc.separation_km.toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
