import type { AuthoritativeImpact } from "./frameSource";
import type { Vec3 } from "./interpolation";

/**
 * Window CustomEvent name coordinated between TASK-003 (collision runner UI)
 * and TASK-004 (globe replay session). Dispatched when a collision job reaches
 * state === "completed".
 */
export const SCENARIO_COMPLETED_EVENT = "astra:scenario-completed" as const;

/**
 * Canonical completion payload passed from TASK-003 to TASK-004 via either:
 * - the React completion callback (`onScenarioCompleted`), or
 * - `emitScenarioCompleted(...)` (dispatches `SCENARIO_COMPLETED_EVENT`).
 */
export type CompletedScenarioHandoff = {
  /** Completed scenario ID used to fetch GET /api/v1/scenarios/{id}/frames. */
  scenarioId: string;
  /** Deterministic simulation seed from Job.seed. */
  seed?: number;
  /** Authoritative impact epoch (UTC ISO-8601) and ITRS-meter position. */
  impact?: AuthoritativeImpact | null;
};

/**
 * Accepts camelCase `CompletedScenarioHandoff` or snake_case wire fields
 * (`scenario_id`, `epoch_utc`, `impact_position_itrs_m`) or a `job` envelope
 * so TASK-003 callers cannot silently drop fields due to naming differences.
 */
export type ScenarioCompletionInput =
  | CompletedScenarioHandoff
  | {
      scenario_id: string;
      seed?: number;
      epoch_utc?: string | null;
      impact_position_itrs_m?: Vec3 | null;
      impact?: AuthoritativeImpact | null;
    }
  | {
      job: {
        scenario_id: string;
        seed?: number;
        state?: string;
      };
      epoch_utc?: string | null;
      impact_position_itrs_m?: Vec3 | null;
      impact?: AuthoritativeImpact | null;
    };

export type ScenarioCompletionCallback = (
  input: ScenarioCompletionInput,
) => void;

function isValidVec3(value: unknown): value is Vec3 {
  return (
    Array.isArray(value) &&
    value.length === 3 &&
    value.every((n) => typeof n === "number" && Number.isFinite(n))
  );
}

/**
 * Normalizes any supported TASK-003 completion payload into a
 * `CompletedScenarioHandoff`, or returns null if `scenarioId` is missing or a
 * supplied `job.state` is not `"completed"`.
 */
export function normalizeScenarioHandoff(
  input: ScenarioCompletionInput | null | undefined,
): CompletedScenarioHandoff | null {
  if (!input || typeof input !== "object") return null;

  let scenarioId: string | undefined;
  let seed: number | undefined;
  let impact: AuthoritativeImpact | null | undefined = input.impact;

  if ("job" in input && input.job) {
    if (input.job.state && input.job.state !== "completed") return null;
    scenarioId = input.job.scenario_id;
    seed = input.job.seed;
    if (!impact && (input.epoch_utc || input.impact_position_itrs_m)) {
      impact = {
        atUtc: input.epoch_utc ?? null,
        position: isValidVec3(input.impact_position_itrs_m)
          ? [...input.impact_position_itrs_m]
          : null,
        confirmed: true,
      };
    }
  } else if ("scenario_id" in input) {
    scenarioId = input.scenario_id;
    seed = input.seed;
    if (!impact && (input.epoch_utc || input.impact_position_itrs_m)) {
      impact = {
        atUtc: input.epoch_utc ?? null,
        position: isValidVec3(input.impact_position_itrs_m)
          ? [...input.impact_position_itrs_m]
          : null,
        confirmed: true,
      };
    }
  } else if ("scenarioId" in input) {
    scenarioId = input.scenarioId;
    seed = input.seed;
  }

  const trimmed = scenarioId?.trim();
  if (!trimmed) return null;

  const normalizedImpact: AuthoritativeImpact | null | undefined = impact
    ? {
        ...impact,
        position: isValidVec3(impact.position) ? [...impact.position] : null,
        confirmed: impact.confirmed ?? true,
      }
    : impact;

  const handoff: CompletedScenarioHandoff = { scenarioId: trimmed };
  if (typeof seed === "number" && Number.isFinite(seed)) {
    handoff.seed = seed;
  }
  if (normalizedImpact !== undefined) {
    handoff.impact = normalizedImpact;
  }
  return handoff;
}

/**
 * Emits `SCENARIO_COMPLETED_EVENT` on `window` (or a supplied EventTarget) so
 * TASK-004's replay session automatically switches to the completed run, loads
 * its paginated `/frames`, applies its seed and impact metadata, and exits the
 * separate synthetic preview mode.
 */
export function emitScenarioCompleted(
  input: ScenarioCompletionInput,
  target: Pick<EventTarget, "dispatchEvent"> | undefined = typeof window !==
  "undefined"
    ? window
    : undefined,
): CompletedScenarioHandoff | null {
  const handoff = normalizeScenarioHandoff(input);
  if (!handoff) return null;
  if (target && typeof CustomEvent !== "undefined") {
    target.dispatchEvent(
      new CustomEvent<CompletedScenarioHandoff>(SCENARIO_COMPLETED_EVENT, {
        detail: handoff,
      }),
    );
  }
  return handoff;
}
