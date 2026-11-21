import type { components } from "../../../../../packages/contracts/api";

type Models = components["schemas"];
export type ScenarioRequest = Models["ScenarioRequest"];
export type ScenarioJob = Models["Job"];
export type SimulationSummary = Models["SimulationSummary"];
export type FramePage = Models["FramePage"];

async function request<T>(
  path: string,
  signal: AbortSignal,
  init?: RequestInit,
): Promise<T> {
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    signal: AbortSignal.any([signal, AbortSignal.timeout(10000)]),
  });
  if (!response.ok) {
    const failure = (await response.json().catch(() => null)) as
      Models["ErrorEnvelope"] | null;
    throw new Error(
      failure?.error.message ?? "The simulation API is unavailable.",
    );
  }
  return (await response.json()) as T;
}

export async function startScenario(
  scenario: ScenarioRequest,
  signal: AbortSignal,
) {
  const created = await request<Models["ScenarioCreated"]>(
    "/scenarios",
    signal,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(scenario),
    },
  );
  return request<ScenarioJob>(`/scenarios/${created.scenario_id}/run`, signal, {
    method: "POST",
  });
}

export async function monitorJob(
  initial: ScenarioJob,
  signal: AbortSignal,
  onState: (job: ScenarioJob) => void,
) {
  let job = initial;
  onState(job);
  while (job.state === "queued" || job.state === "running") {
    await new Promise<void>((resolve) => setTimeout(resolve, 200));
    signal.throwIfAborted();
    job = await request<ScenarioJob>(`/jobs/${job.job_id}`, signal);
    onState(job);
  }
  return job;
}

export function cancelJob(jobId: string, signal: AbortSignal) {
  return request<ScenarioJob>(`/jobs/${jobId}/cancel`, signal, {
    method: "POST",
  });
}

export function loadSummary(scenarioId: string, signal: AbortSignal) {
  return request<SimulationSummary>(
    `/scenarios/${scenarioId}/simulation`,
    signal,
  );
}

export function loadFrames(
  scenarioId: string,
  signal: AbortSignal,
  cursor?: string,
) {
  const query = cursor ? `?${new URLSearchParams({ cursor })}` : "";
  return request<FramePage>(`/scenarios/${scenarioId}/frames${query}`, signal);
}
