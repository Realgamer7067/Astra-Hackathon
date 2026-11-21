/**
 * Entry crossings list — fragments that crossed the atmospheric threshold.
 */
import type { EntryCrossing } from "./api";

interface EntryCrossingsListProps {
  crossings: EntryCrossing[];
}

export function EntryCrossingsList({ crossings }: EntryCrossingsListProps) {
  return (
    <div className="entry-crossings" aria-label="Atmospheric entry crossings">
      <h3>Atmospheric Entry Crossings</h3>
      <p className="crossings-note">
        Fragments crossing the {crossings[0]?.threshold_altitude_km ?? 120} km
        altitude threshold. Approximate geolocation only —{" "}
        <strong>no ground-impact or casualty assessment is implied.</strong>
      </p>
      <ul className="crossings-list">
        {crossings.map((c, i) => (
          <li key={i} className="crossing-item">
            <span className="crossing-id">{c.fragment_id}</span>
            <span className="crossing-geo">
              {c.latitude_deg.toFixed(2)}° N, {c.longitude_deg.toFixed(2)}° E
            </span>
            <span className="crossing-time mono">
              {new Date(c.at_utc).toISOString().slice(0, 19)}Z
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}
