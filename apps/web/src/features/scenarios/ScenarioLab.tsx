import { type FormEvent, useEffect, useRef, useState } from "react";
import { type DemoBundle, kindLabels } from "../../app/demo";
import {
  cancelJob,
  type FramePage,
  loadFrames,
  loadSummary,
  monitorJob,
  type ScenarioJob,
  type ScenarioRequest,
  type SimulationSummary,
  startScenario,
} from "./client";
import "./scenarios.css";

function message(error: unknown) {
  return error instanceof Error
    ? error.message
    : "The simulation request failed.";
}

export function ScenarioLab({ demo }: { demo: DemoBundle }) {
  const objects = demo.objects.filter((object) =>
    demo.states.states.some((state) => state.object_id === object.id),
  );
  const initial = demo.scenario.participants;
  const operation = useRef<AbortController | null>(null);
  const [job, setJob] = useState<ScenarioJob | null>(null);
  const [summary, setSummary] = useState<SimulationSummary | null>(null);
  const [page, setPage] = useState<FramePage | null>(null);
  const [sampleIndex, setSampleIndex] = useState(0);
  const [pageCursor, setPageCursor] = useState<string | undefined>();
  const [busy, setBusy] = useState(false);
  const [cancelPending, setCancelPending] = useState(false);
  const [loadingPage, setLoadingPage] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const selectedSample = page?.samples[sampleIndex];
  const firstFragment = selectedSample?.positions[0];

  useEffect(() => () => operation.current?.abort(), []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const participant = (index: number) => ({
      object_id: String(fields.get(`object${index}`)),
      assumed_mass_kg: Number(fields.get(`mass${index}`)),
      assumed_radius_m: Number(fields.get(`radius${index}`)),
    });
    const participants: ScenarioRequest["participants"] = [
      participant(0),
      participant(1),
    ];
    if (participants[0].object_id === participants[1].object_id) {
      setError("Choose two distinct objects.");
      return;
    }
    setBusy(true);
    setError(null);
    setSummary(null);
    setPage(null);
    setJob(null);
    setPageCursor(undefined);
    operation.current?.abort();
    const controller = new AbortController();
    operation.current = controller;
    const signal = AbortSignal.any([
      controller.signal,
      AbortSignal.timeout(130000),
    ]);
    const scenario: ScenarioRequest = {
      schema_version: "1.0",
      type: "FORCED_HYPOTHETICAL",
      epoch_utc: demo.states.at_utc,
      participants,
      forced_contact: {
        move_participant_index: 1,
        impact_geometry: "CENTERED",
      },
      simulation: {
        seed: Number(fields.get("seed")),
        duration_hours: Number(fields.get("duration")),
        max_resolved_fragments: Number(fields.get("fragments")),
        output_step_seconds: 30,
        max_cascade_generations: 0,
      },
      requested_products: ["TRAJECTORIES", "ENTRY_CROSSINGS"],
    };
    try {
      const initialJob = await startScenario(scenario, signal);
      const finished = await monitorJob(initialJob, signal, setJob);
      if (finished.state === "completed") {
        const [metrics, frames] = await Promise.all([
          loadSummary(finished.scenario_id, signal),
          loadFrames(finished.scenario_id, signal),
        ]);
        setSummary(metrics);
        setSampleIndex(0);
        setPage(frames);
      } else if (finished.state === "failed") {
        setError(finished.error?.message ?? "The simulation failed.");
      }
    } catch (error) {
      if (!controller.signal.aborted) setError(message(error));
    } finally {
      if (!controller.signal.aborted) {
        setBusy(false);
        setCancelPending(false);
      }
    }
  }

  async function cancel() {
    if (!job || !operation.current) return;
    setCancelPending(true);
    try {
      await cancelJob(job.job_id, operation.current.signal);
    } catch (error) {
      setError(message(error));
      setCancelPending(false);
    }
  }

  async function showPage(cursor?: string) {
    if (!summary || !operation.current) return;
    setLoadingPage(true);
    setError(null);
    const controller = operation.current;
    try {
      const frames = await loadFrames(
        summary.scenario_id,
        controller.signal,
        cursor,
      );
      setPage(frames);
      setPageCursor(cursor);
      setSampleIndex(0);
    } catch (error) {
      if (!controller.signal.aborted) setError(message(error));
    } finally {
      if (!controller.signal.aborted) setLoadingPage(false);
    }
  }

  return (
    <section
      className="scenario-lab"
      id="collision-lab"
      aria-labelledby="collision-heading"
    >
      <div className="scenario-heading">
        <h2 id="collision-heading">Collision lab</h2>
        <span>Hypothetical · Synthetic demo</span>
      </div>
      <p>
        Place the second object at the first object’s position at the snapshot
        epoch. Both keep their original velocities.
      </p>
      <form onSubmit={submit}>
        <fieldset
          disabled={busy || loadingPage || objects.length < 2}
          className="scenario-inputs"
        >
          {initial.map((item, index) => (
            <div className="scenario-participant" key={index}>
              <label>
                {index === 0 ? "Target object" : "Moved object"}
                <select
                  name={`object${index}`}
                  defaultValue={item.object_id}
                  required
                >
                  {objects.map((object) => (
                    <option key={object.id} value={object.id}>
                      {object.name} · {kindLabels[object.kind]}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Assumed mass (kg)
                <input
                  name={`mass${index}`}
                  type="number"
                  min="0.01"
                  max="10000000"
                  step="any"
                  defaultValue={item.assumed_mass_kg ?? 5}
                  required
                />
              </label>
              <label>
                Assumed radius (m)
                <input
                  name={`radius${index}`}
                  type="number"
                  min="0.01"
                  max="500"
                  step="any"
                  defaultValue={item.assumed_radius_m ?? 0.2}
                  required
                />
              </label>
            </div>
          ))}
          <div className="scenario-settings">
            <label>
              Seed
              <input
                name="seed"
                type="number"
                min="0"
                max="4294967295"
                defaultValue="42"
                required
              />
            </label>
            <label>
              Fragments
              <input
                name="fragments"
                type="number"
                min="1"
                max="1500"
                defaultValue="96"
                required
              />
            </label>
            <label>
              Duration (hours)
              <input
                name="duration"
                type="number"
                min="0.05"
                max="24"
                step="any"
                defaultValue="1"
                required
              />
            </label>
          </div>
          <label className="scenario-confirm">
            <input type="checkbox" required /> I accept the assumed sizes and
            masses for this hypothetical run.
          </label>
          <button type="submit">Run collision</button>
        </fieldset>
      </form>
      {busy && (
        <div className="scenario-progress" role="status">
          <span>
            {cancelPending
              ? "Cancelling…"
              : job
                ? `Simulation ${job.state}`
                : "Submitting scenario…"}
          </span>
          <progress
            aria-label="Simulation progress"
            max={1}
            value={job?.progress ?? undefined}
          />
          {job && (job.state === "queued" || job.state === "running") && (
            <button
              type="button"
              onClick={() => void cancel()}
              disabled={cancelPending}
            >
              Cancel run
            </button>
          )}
        </div>
      )}
      {!busy && job?.state === "cancelled" && (
        <p role="status">Simulation cancelled.</p>
      )}
      {error && (
        <p role="alert" className="scenario-error">
          {error}
        </p>
      )}
      {summary && page && (
        <div className="scenario-output" aria-labelledby="collision-result">
          <h3 id="collision-result">Hypothetical simulation result</h3>
          <p>
            Seed {summary.seed} · {summary.provenance.modelVersion}
          </p>
          <dl>
            <dt>Relative speed</dt>
            <dd>{summary.relative_speed_km_s.toFixed(3)} km/s</dd>
            <dt>Modeled impact energy</dt>
            <dd>{summary.impact_energy_j.toExponential(3)} J</dd>
            <dt>Resolved fragments</dt>
            <dd>{summary.resolved_fragment_count}</dd>
            <dt>Unresolved mass</dt>
            <dd>{summary.unresolved_mass_kg?.toFixed(2)} kg</dd>
            <dt>Entry threshold crossings</dt>
            <dd>{summary.entry_crossings.length}</dd>
            <dt>Original separation</dt>
            <dd>
              {summary.modification?.original_separation_km.toFixed(2)} km
            </dd>
          </dl>
          <h4>Saved frame samples</h4>
          {selectedSample && (
            <>
              <label>
                Frame {sampleIndex + 1} of {page.samples.length}
                <input
                  type="range"
                  min={0}
                  max={page.samples.length - 1}
                  value={sampleIndex}
                  onChange={(event) =>
                    setSampleIndex(Number(event.target.value))
                  }
                />
              </label>
              <p>
                {new Date(selectedSample.at_utc).toISOString().slice(11, 19)}{" "}
                UTC · {selectedSample.positions.length} positions in{" "}
                {page.frame}
              </p>
              {firstFragment && (
                <p>
                  <code>{firstFragment.object_id}</code> ·{" "}
                  {firstFragment.position
                    .map((coordinate) => (coordinate / 1000).toFixed(2))
                    .join(", ")}{" "}
                  km
                </p>
              )}
              {!selectedSample.positions.length && (
                <p>All resolved trajectories have terminated in this sample.</p>
              )}
            </>
          )}
          <div className="scenario-pagination">
            {pageCursor && (
              <button
                type="button"
                disabled={loadingPage}
                onClick={() => void showPage()}
              >
                First page
              </button>
            )}
            {page.next_cursor && (
              <button
                type="button"
                disabled={loadingPage}
                onClick={() => void showPage(page.next_cursor ?? undefined)}
              >
                Next page
              </button>
            )}
          </div>
          {summary.modification && (
            <details>
              <summary>Forced contact audit</summary>
              <dl>
                <dt>Moved object</dt>
                <dd>{summary.modification.original_state.state.object_id}</dd>
                <dt>Original GCRS position</dt>
                <dd>
                  {summary.modification.original_state.state.position
                    .map((coordinate) => coordinate.toFixed(2))
                    .join(", ")}{" "}
                  km
                </dd>
                <dt>Injected GCRS position</dt>
                <dd>
                  {summary.modification.modified_state.state.position
                    .map((coordinate) => coordinate.toFixed(2))
                    .join(", ")}{" "}
                  km
                </dd>
              </dl>
            </details>
          )}
          <details>
            <summary>Model assumptions and limitations</summary>
            <ul>
              {[
                ...summary.provenance.assumptions,
                ...summary.provenance.limitations,
              ].map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </section>
  );
}
