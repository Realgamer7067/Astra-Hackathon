/**
 * API client for results and report endpoints (TASK-005 Lane D).
 */
import type { components } from "../../../../../packages/contracts/api";

export type ScenarioResult = components["schemas"]["ScenarioResult"];
export type OccupancyBin = components["schemas"]["OccupancyBin"];
export type CloseApproach = components["schemas"]["CloseApproach"];
export type EntryCrossing = components["schemas"]["EntryCrossing"];
export type Provenance = components["schemas"]["Provenance"];

export interface ReportSection {
  title: string;
  content: Record<string, unknown>;
  provenance: {
    kind: string;
    source: string;
    catalog_snapshot_id?: string | null;
    model_version?: string | null;
    assumptions: string[];
    limitations: string[];
  };
}

export interface ScenarioReport {
  schema_version: string;
  generated_at_utc: string;
  scenario_id: string;
  scenario_type: string;
  seed: number;
  sections: ReportSection[];
  global_limitations: string[];
}

export async function fetchResults(
  scenarioId: string,
  signal?: AbortSignal,
): Promise<ScenarioResult> {
  const resp = await fetch(`/api/v1/scenarios/${scenarioId}/results`, {
    signal,
  });
  if (!resp.ok) throw new Error(`Results unavailable (${resp.status})`);
  return (await resp.json()) as ScenarioResult;
}

export async function fetchReport(
  scenarioId: string,
  format: "json" | "markdown" = "json",
  signal?: AbortSignal,
): Promise<ScenarioReport | string> {
  const resp = await fetch(
    `/api/v1/scenarios/${scenarioId}/report?format=${format}`,
    { signal },
  );
  if (!resp.ok) throw new Error(`Report unavailable (${resp.status})`);
  if (format === "markdown") return resp.text();
  return (await resp.json()) as ScenarioReport;
}
