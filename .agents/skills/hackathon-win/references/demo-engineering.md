# Demo Engineering

Use as soon as an end-to-end path exists. The demo is a product surface, not an improvised tour.

## Golden Path

Define the one experience every judge must see:

`open -> enter or select realistic data -> real core processing -> impressive result -> action or impact`

Minimize navigation, typing, setup, signup, and latency. Put the core action on an obvious path. Protect it above secondary features.

## Wow moment

Name the exact second intended to make the judge think, "That's cool." It may be a transformation, insight, realtime interaction, map, generated artifact, automation, physical response, or dramatic before/after.

A wow moment must:

- support the core story and rubric;
- be visible without explanation;
- be reliable and timed;
- have a backup;
- not depend on fake central behavior.

## `DEMO.md`

Write a second-by-second script sized to the official duration. For each step capture:

| Time | Page | Action | Talking point | Expected result | Backup |
| --- | --- | --- | --- | --- | --- |

Default three-minute shape, adapted to the event:

- `0:00-0:20` problem and memory hook;
- `0:20-0:40` product reveal;
- `0:40-1:20` core workflow;
- `1:20-2:00` wow moment;
- `2:00-2:30` technical contribution and proof;
- `2:30-3:00` impact, differentiation, close.

Show instead of tell. Perform the analysis, generate the result, reveal the dashboard, or trigger the hardware instead of listing capabilities.

## Demo mode

Implement `?demo=true`, a demo route, CLI flag, or equivalent when helpful. It may preload known-good realistic data, bypass nonessential onboarding, shorten waits, surface P1 screens, and select deterministic inputs. Clearly separate it from production assumptions.

## Failure matrix

Check current rules before choosing a recovery: live-only, fresh-input, mandatory API, and public-deployment requirements override cached/replayed/video alternatives. A forbidden fallback may preserve explanatory evidence but cannot establish eligibility. Prefer bounded timeouts/retries, a smaller valid input, or another permitted real path. State a switch to cached, simulated, precomputed, or recorded behavior when it occurs; do not wait to be challenged.

Every luck-dependent component needs a plan:

| Dependency | Live path | Detection | Immediate recovery | Prepared asset |
| --- | --- | --- | --- | --- |
| LLM/API | Normal request | timeout/error | load cached known-good result | cached response |
| Internet | Deployed app | connectivity check | localhost | local build |
| Deployment | Public URL | health check | local app | offline instructions |
| Realtime feed | Live event | stale/error | replay saved event | fixture |
| Slow model | Live inference | time budget | precomputed example | result artifact |
| Whole app | Live demo | catastrophic failure | play concise recording | demo video |

Use prerecorded material as a fallback, not as an undisclosed replacement for a nonexistent central feature.

## Rehearsal

Run the exact Golden Path at least three times from a clean state. Verify login/session, seed data, waits, projector resolution, network, audio/video, and transitions. Time the narration. Rehearse recoveries so a failure does not cause live debugging.

Three successful runs are a smoke check, not a reliability statistic. Include at least one fresh valid input and a forced failure/recovery where time permits. After a material change, rerun the affected path. Keep a single short full rehearsal in an emergency rather than missing submission for a fixed run count.

Keep the architecture diagram and known-good screenshots ready for unexpected questions. Never live-code during the judged presentation.
