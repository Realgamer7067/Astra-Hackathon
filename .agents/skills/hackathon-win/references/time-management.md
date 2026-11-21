# Time Management

Use whenever the clock changes materially, scope is disputed, or a major feature is proposed.

## Critical path

Write the shortest dependency chain required for the Golden Path, for example:

`data -> core logic -> API -> UI integration -> demo workflow -> deployment`

Protect it from optional work. A task off the critical path must justify the time it steals from P0 integration and verification.

Track separate code-freeze, submission, video-upload, sponsor, and presentation deadlines. Work from the earliest binding cutoff, not the most convenient one. Reserve delivery/rehearsal time before allocating feature time; use actual upload/render times and a buffer. Budget person-hours from real availability, including rest and handoffs; four people do not make every dependency four times faster. Never reopen prohibited development after code freeze.

## Mode rules

### More than 24 hours

Allow bounded research, proof spikes, architecture improvements, and design exploration. Still establish the MVP, deployment skeleton, Golden Path, and visual direction early. Resolve the riskiest assumption before scaling the build.

### 12-24 hours

Concentrate on MVP, primary workflow, integration, technical proof, and UI identity. Cut speculative experiments and broad feature sets. Deploy a thin working path.

### 6-12 hours

Freeze architecture unless broken. Finish end-to-end behavior, realistic seed data, failure fallbacks, deployment, visual review, and demo scripting. Do not migrate frameworks.

### 3-6 hours

Begin feature freeze. Prioritize Golden Path bugs, weighted rubric evidence, screenshots, README/submission, demo rehearsal, and pitch. Hide incomplete routes.

### 1-3 hours

No major new features. Secure a valid submission, public or local demo path, video/screenshots, fallback assets, pitch timing, and likely judge answers. Preserve the known-good commit.

### Under 1 hour

Emergency only: save or submit a valid entry, verify the app opens, capture evidence, fix catastrophic blockers, and stop risky changes. A submitted imperfect project beats an unsubmitted ambitious one.

## P0-P3 plan

- **P0 — MUST WORK:** Golden Path and required submission.
- **P1 — JUDGE IMPACT:** high-weight evidence, wow, and high-leverage visual clarity.
- **P2 — POLISH:** perceived completeness and recovery quality.
- **P3 — NICE TO HAVE:** only after P0/P1 and demo stability.

Each task records objective, owner, dependency, estimate, rubric impact, demo impact, status, and proof of completion. Reclassify tasks when time mode changes.

## Stop rules

Reject optional or displacing work when:

- it cannot be verified before the next checkpoint;
- it risks the stable demo without a rollback;
- it is production-only and no rubric rewards it;
- a smaller change earns similar visible value;
- it depends on an unresolved service with no fallback;
- it begins a migration during freeze;
- P0, pitch, deployment, or submission remains incomplete.

These rules do not forbid work needed to complete P0 or submission itself. Under one hour, internal documentation is optional unless required by the event. At a cutoff, treat the deadline as reached; verify any grace period rather than assuming it.

When rejecting, name the displaced higher-value action. Be decisive rather than motivational.

## Checkpoint cadence

Use event-relative checkpoints rather than constant status chatter:

- after core risk proof;
- first end-to-end Golden Path;
- first deployment;
- feature freeze;
- first timed rehearsal;
- submission-safe version;
- final win audit.

At each checkpoint run product, rubric, technical, visual, demo, time, and submission audits at a depth appropriate to the remaining time.
