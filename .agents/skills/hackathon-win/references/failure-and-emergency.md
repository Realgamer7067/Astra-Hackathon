# Failure Modes and Emergency Mode

Use under six hours, when the demo is unstable, or when scope pressure threatens submission.

All recovery examples below are conditional on official event and selected-track rules. A cache, recording, localhost demo, or alternate API is not a substitute when the required format forbids it. Below one hour, do not generate the internal document suite; complete only mandatory deliverables and a minimal recovery note if useful.

## Common losing patterns and correction

| Failure | Immediate correction |
| --- | --- |
| Overbuilt backend, weak product | Stop infrastructure; connect one end-to-end Golden Path. |
| Beautiful fake prototype | Make the central claim real; cut secondary polish if needed. |
| Generic AI wrapper | Add a nontrivial workflow, unique data, verification, action, or reject the idea. |
| Unclear problem | Rewrite the 15-second user moment and one-sentence solution. |
| Too many features | Freeze scope; hide incomplete routes; finish P0/P1. |
| UI looks unfinished | Seed realistic data and fix the few judge-visible screens. |
| Dependency fails intermittently | Add deterministic cached/replay fallback and rehearse recovery. |
| Deployment not working | Timebox diagnosis; preserve localhost plus video while attempting the smallest fix. |
| Forced sponsor API | Remove it unless eligibility/value exceeds integration cost. |
| Framework/schema migration proposed late | Reject it; restore the stable path. |
| Pitch not started | Stop feature work and write/timestamp `PITCH.md` plus `DEMO.md`. |
| Submission incomplete | Save a valid entry immediately, then improve editable fields. |
| Single giant commit or unclear provenance | Commit current state and document event-time work honestly; never rewrite history to mislead. |
| Live coding in presentation | Replace with prepared demo and architecture evidence. |
| Demo login or setup friction | Use preauthenticated/demo state and a clean recovery account. |

## Emergency triage

Rank only:

1. eligibility and valid submission;
2. app/demo opens;
3. central claim works or has honest proof;
4. Golden Path and wow recovery;
5. screenshots/video;
6. pitch within time;
7. catastrophic credibility issue.

Everything else is frozen.

## Adversarial decisions

- "Rewrite the backend with three hours left." **No.** Preserve the stable implementation and fix the failing demo surface.
- "We need production Kubernetes." **No**, unless the rubric explicitly requires orchestration and a working cluster is already on the critical path.
- "Add seven more features." **No.** Finish one story, workflow, and wow moment.
- "The API fails 30% of the time." Add and rehearse a permitted fallback now. If live-only rules apply, stabilize/narrow the real path with bounded retries/timeouts; disclose any remaining failure risk.
- "The judges do not understand the product." Stop building; repair the product sentence, hero, workflow cues, and demo order.
- "UI is worth zero points." Make weighted evidence clear and usable, then stop cosmetic polish before it displaces core work.

## Last-hour checklist

- Submit or save a valid version and record confirmation.
- Tag or note the known-good commit.
- Verify deployed and local launch paths.
- Capture the primary screenshots and a short fallback recording.
- Preload accounts/data and disable incomplete features.
- Rehearse one timed demo and its top recovery.
- Check repository/video/link permissions.
- Stop all non-catastrophic edits.

Do not spend the last minutes perfecting this checklist; execute the highest-risk missing item.
