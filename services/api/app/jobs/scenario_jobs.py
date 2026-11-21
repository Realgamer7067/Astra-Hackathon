"""Bounded local scenario registry and cooperative worker cancellation."""

import logging
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from threading import Event, Lock
from time import monotonic
from uuid import uuid4

from ..models.scenarios import ScenarioCreated
from ..models.wire import Job, JobFailure
from ..physics.scenario import CompletedRun, PreparedScenario, ScenarioError, simulate

MAX_ACTIVE_JOBS = 2
MAX_SCENARIOS = 10
TIMEOUT_SECONDS = 120
ACTIVE = ("queued", "running")
logger = logging.getLogger(__name__)


class Cancelled(Exception):
    """The worker reached a requested cancellation checkpoint."""


@dataclass
class Run:
    prepared: PreparedScenario
    cancel: Event = field(default_factory=Event)
    job: Job | None = None
    completed: CompletedRun | None = None


class ScenarioJobs:
    def __init__(self) -> None:
        self._lock = Lock()
        self._pool = ThreadPoolExecutor(
            max_workers=MAX_ACTIVE_JOBS, thread_name_prefix="astra-simulation"
        )
        self._scenarios: dict[str, Run] = {}

    def close(self) -> None:
        with self._lock:
            for scenario in self._scenarios.values():
                scenario.cancel.set()
        self._pool.shutdown(wait=True, cancel_futures=True)

    def create(self, prepared: PreparedScenario) -> ScenarioCreated:
        with self._lock:
            if len(self._scenarios) >= MAX_SCENARIOS:
                removable = next(
                    (
                        key
                        for key, entry in self._scenarios.items()
                        if entry.job is None or entry.job.state not in ACTIVE
                    ),
                    None,
                )
                if removable is None:
                    raise ScenarioError(429, "SCENARIO_CAPACITY", "Scenario capacity is full.")
                del self._scenarios[removable]
            scenario_id = uuid4().hex
            self._scenarios[scenario_id] = Run(prepared)
        return ScenarioCreated(
            scenario_id=scenario_id,
            scenario_type=prepared.request.type,
            catalog_snapshot_id=prepared.snapshot,
            assumptions=list(prepared.assumptions),
        )

    def start(self, scenario_id: str) -> Job:
        with self._lock:
            entry = self._scenario(scenario_id)
            if entry.job is not None:
                return entry.job
            if (
                sum(
                    run.job is not None and run.job.state in ACTIVE
                    for run in self._scenarios.values()
                )
                >= MAX_ACTIVE_JOBS
            ):
                raise ScenarioError(429, "JOB_CAPACITY", "Two simulation jobs are already active.")
            job = Job(
                job_id=uuid4().hex,
                scenario_id=scenario_id,
                seed=entry.prepared.request.simulation.seed,
                state="queued",
                progress=0,
                error=None,
            )
            entry.job = job
            self._pool.submit(self._execute, entry, job)
            return job

    def status(self, job_id: str) -> Job:
        with self._lock:
            _, job = self._job(job_id)
            return job

    def cancel(self, job_id: str) -> Job:
        with self._lock:
            run, job = self._job(job_id)
            if job.state in ACTIVE:
                run.cancel.set()
            return job

    def result(self, scenario_id: str) -> CompletedRun:
        with self._lock:
            run = self._scenario(scenario_id)
            if run.completed is None:
                raise ScenarioError(409, "RUN_INCOMPLETE", "This scenario has no completed run.")
            return run.completed

    def _scenario(self, scenario_id: str) -> Run:
        run = self._scenarios.get(scenario_id)
        if run is None:
            raise ScenarioError(404, "SCENARIO_NOT_FOUND", "Scenario is unknown or has expired.")
        return run

    def _job(self, job_id: str) -> tuple[Run, Job]:
        for run in self._scenarios.values():
            if run.job is not None and run.job.job_id == job_id:
                return run, run.job
        raise ScenarioError(404, "JOB_NOT_FOUND", "Job is unknown or has expired.")

    def _execute(self, entry: Run, job: Job) -> None:
        deadline = monotonic() + TIMEOUT_SECONDS
        latest = 0.0
        completed = None

        def check(progress: float) -> None:
            nonlocal latest
            if entry.cancel.is_set():
                raise Cancelled
            if monotonic() >= deadline:
                raise TimeoutError
            if progress - latest >= 0.02:
                latest = progress
                with self._lock:
                    entry.job = job.model_copy(
                        update={"state": "running", "progress": min(progress, 0.99)}
                    )

        with self._lock:
            entry.job = job.model_copy(update={"state": "running"})
        try:
            completed = simulate(entry.prepared, job.scenario_id, check)
            check(1)
            terminal = job.model_copy(update={"state": "completed", "progress": 1.0})
        except Cancelled:
            terminal = job.model_copy(update={"state": "cancelled", "progress": latest})
        except TimeoutError:
            terminal = job.model_copy(
                update={
                    "state": "failed",
                    "progress": latest,
                    "error": JobFailure(
                        code="JOB_TIMEOUT", message="Simulation exceeded its time limit."
                    ),
                }
            )
        except Exception:
            logger.exception("Collision simulation failed")
            terminal = job.model_copy(
                update={
                    "state": "failed",
                    "progress": latest,
                    "error": JobFailure(
                        code="SIMULATION_FAILED", message="The simulation could not finish."
                    ),
                }
            )
        with self._lock:
            if entry.cancel.is_set() and terminal.state == "completed":
                terminal = job.model_copy(update={"state": "cancelled", "progress": latest})
            entry.job = terminal
            if terminal.state == "completed":
                entry.completed = completed
