/**
 * Horizontal bar chart for altitude-shell fragment occupancy.
 * Pure CSS — no chart library dependency.
 */
import type { OccupancyBin } from "./api";

interface OccupancyChartProps {
  bins: OccupancyBin[];
}

export function OccupancyChart({ bins }: OccupancyChartProps) {
  const maxCount = Math.max(...bins.map((b) => b.resolved_count), 1);

  return (
    <div className="occupancy-chart" aria-label="Altitude shell occupancy">
      <h3>Orbital Shell Occupancy</h3>
      <p className="chart-note">
        Fragment counts per 100-km altitude shell (derived from simulated
        states)
      </p>
      <div className="chart-bars" role="img" aria-label="Occupancy bar chart">
        {bins.map((bin) => (
          <div
            className="chart-row"
            key={`${bin.altitude_min_km}-${bin.altitude_max_km}`}
          >
            <span className="chart-label">
              {bin.altitude_min_km}–{bin.altitude_max_km} km
            </span>
            <div className="chart-bar-container">
              <div
                className="chart-bar"
                style={{
                  width: `${(bin.resolved_count / maxCount) * 100}%`,
                }}
                aria-label={`${bin.resolved_count} fragments`}
              />
            </div>
            <span className="chart-value">{bin.resolved_count}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
