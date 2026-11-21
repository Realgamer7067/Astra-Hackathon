---
name: hackathon-win
description: Maximize a hackathon project's expected judging score per unit of development time. Use for hackathon research, idea selection, rubric strategy, rapid prototype planning or implementation, UI polish, demo and pitch engineering, sponsor-track decisions, recovery, and submission. It is not a production-hardening or generic event-participation guide.
metadata:
  version: "1.1.0"
---

# Hackathon Win

This skill works with coding or reasoning agents that can inspect project files. Web, browser, Git, terminal, deployment, and multi-agent capabilities are optional and must be discovered before use.

Bundled helpers require Python 3.10+. Run them from the skill directory or use absolute script paths; project inputs are explicit. For schemas, examples, exit codes, and limitations read [script-contracts.md](references/script-contracts.md).

## Mission

Maximize:

`Expected judging score / development time`

Do not optimize for production engineering perfection unless the rubric rewards it. Build the smallest convincing real product, make its important surfaces exceptional, and make the judging evidence impossible to miss.

This is not permission to mislead, leak secrets, expose sensitive data, or create avoidable dangerous vulnerabilities. The standard is: **safe enough for a controlled prototype, polished enough for a convincing demo, fast enough to finish**.

## Non-negotiable operating model

Precedence: safety, authorization, and actual event/selected-track eligibility are hard constraints; protect the real core claim and submission next; optimize marginal rubric gain within those constraints. A numerical score never overrides a hard gate. Preserve the user's locked idea and requested scope unless concrete new evidence requires discussing a change. Winning is an objective, not a guarantee.

Classify work before doing it:

- **Demo-critical:** must work reliably in the presentation.
- **Judge-visible:** directly improves what judges see, understand, or remember.
- **Credibility-critical:** substantiates the main claim or prevents the build from looking fake.
- **Production-only:** valuable after the event but normally deferred.

Protect one **GOLDEN PATH** and one deliberately designed **WOW MOMENT**. The central innovation must be real. Secondary paths may be simplified, simulated, cached, or mocked when honest and appropriate. Hide unfinished nonessential features rather than displaying broken completeness.

Label shortcuts in code or `POST_HACKATHON.md`:

`HACKATHON SHORTCUT: <what is simplified>. Replace with <production requirement> before production deployment.`

Never publish secrets, weaken provider controls to get around an access blocker, expose sensitive data, or leave a trivial injection risk in a judge-facing or dangerous input. A public prototype still needs controls against privileged access and runaway spend. Defer production-only infrastructure, not the simplest safeguards against actual exposure. Read [prototype-engineering.md](references/prototype-engineering.md) for the full boundary.

## Start or resume

Do not begin with a generic checklist or twenty questions.

Triage first: for a narrow review, answer, or bug fix, perform only the relevant steps; do not create project files or reopen ideation automatically. Under one hour, skip the normal intake/document sequence: verify cutoff and mandatory deliverables, preserve the working demo, and submit. Record only a brief state note if it helps recovery.

1. **Establish the clock.** Resolve the authoritative deadline and timezone, calculate time remaining, and select the time mode. If the deadline cannot be verified, mark it `UNKNOWN` and ask only when it changes the next decision. Run `scripts/deadline-audit.py --help` when useful.
2. **Inspect reality.** In an existing repository, inspect instructions, tree, manifests, README, routes, data layer, environment examples, deployment config, Git status/history, TODOs, and current runnable state before recommending architecture. Do not overwrite user changes. Do not trust stale status files over code or a running build.
3. **Discover capabilities.** Inspect available native tools, skills, MCP servers, connectors, CLIs, configured authentication status, and permissions without dumping credential values. Record `AVAILABLE`, `PARTIAL`, `UNAVAILABLE`, or `UNKNOWN`; do not assume a named tool exists. Read [agent-and-tooling.md](references/agent-and-tooling.md).
4. **Research the event.** Prefer official event, organizer, sponsor, platform, and API sources. Investigate rules, weights, tracks, required technology, judges, past winners, submission fields, pitch/demo length, and deployment/repository/video constraints. Use `research -> actionable advantage -> build`; timebox open-ended discovery. Read [research-playbook.md](references/research-playbook.md).
5. **Create or update state.** For an authorized full build with enough time, use the files under `templates/` as schemas, not immutable boilerplate. Preserve useful existing content. Normally maintain `HACKATHON.md`, `HACKATHON_STATE.md`, `RUBRIC.md`, and `BUILD_PLAN.md`; combine brief sections or defer internal documents in emergencies. Event-required deliverables remain mandatory.
6. **Choose one action.** Ask: `What single task gives the most expected judging value right now?` Use the priority model below, state the next verification checkpoint, then act when the request authorizes implementation.

For an unknown idea, route through [idea-generation.md](references/idea-generation.md), [idea-tournament.md](references/idea-tournament.md), and [competitive-analysis.md](references/competitive-analysis.md). Do not lock the first plausible idea.

## Decision loop

Repeat at each meaningful checkpoint:

1. Refresh time remaining and actual project state.
2. Identify the largest Golden Path blocker or weighted rubric gap.
3. Rank candidates roughly as:

   `Priority = RubricImpact x DemoImpact x ProbabilityOfSuccess / TimeCost`

   Elevate eligibility, submission, critical-path, and demo-failure risks. Discount invisible refactors, speculative infrastructure, and production-only concerns.

   Rank hard blockers first outside this formula. Use expected *incremental* rubric gain, not the total criterion weight, and include integration, verification, and rollback in time cost. A visually invisible prerequisite can still be P0.
4. Implement the smallest coherent change.
5. Verify observable behavior. For UI, open the actual app and inspect screenshots; code review alone is insufficient.
6. Update `HACKATHON_STATE.md`, relevant evidence in `RUBRIC.md`, known risks, and the last verified working state.
7. Preserve a known-good Git milestone before risky polish. Do not rewrite working systems without measurable judging value.

Read [rubric-and-prioritization.md](references/rubric-and-prioritization.md) for rubric translation and audits, and [time-management.md](references/time-management.md) for feature-freeze decisions.

## Time modes

| Remaining | Default posture |
| --- | --- |
| `>24h` | Explore selectively, establish MVP and visual direction early, deploy a thin path. |
| `12-24h` | Drive MVP, integration, primary workflow, and UI identity; reduce experiments. |
| `6-12h` | Freeze architecture unless broken; finish flows, seeded data, deployment, demo, and polish. |
| `3-6h` | Begin feature freeze; fix reliability, screenshots, pitch, and weighted evidence gaps. |
| `1-3h` | No major features; secure deployment/fallback, README, video, pitch, and submission. |
| `<1h` | Emergency: submit a valid version, make demo open, capture fallbacks, fix only catastrophic blockers. |

Say plainly: **Stop building this feature. It is no longer worth the remaining time.** Read [failure-and-emergency.md](references/failure-and-emergency.md) when under six hours, the demo is unstable, or submission is at risk.

## Persistent project truth

Use these files to survive long sessions and agent handoffs:

- `HACKATHON.md`: verified event intelligence and known unknowns.
- `HACKATHON_STATE.md`: current goal, time mode, Golden Path, blockers, P0/P1, bugs, owners, last verified state.
- `RUBRIC.md`: criterion weights and visible evidence.
- `BUILD_PLAN.md`: P0-P3 tasks, dependencies, owners, impact, and status.
- `ARCHITECTURE.md`: explainable components, data flow, integrations, and shortcuts.
- `COMPETITION.md`: what exists and why this entry is memorable.
- `DEMO.md`: timed actions, expected results, and recovery for every step.
- `PITCH.md`: exact-time story and likely judge answers.
- `SUBMISSION.md`: deliverables, links, tracks, deadline, and status.
- `POST_HACKATHON.md`: security debt, mocks, scale limits, assumptions, and production work.

Update instead of recreating. Keep status concise. `scripts/project-status.py --help` can produce a repository snapshot; its output is evidence to review, not a substitute for running the product.

## Reference routing

Read only what the current decision needs:

| Situation | Read |
| --- | --- |
| New event, missing rules, uncertain claims | [research-playbook.md](references/research-playbook.md), then [intelligence-and-intake.md](references/intelligence-and-intake.md) |
| Rubric, work ranking, or audit | [rubric-and-prioritization.md](references/rubric-and-prioritization.md) |
| Need or reconsider an idea | [idea-generation.md](references/idea-generation.md), [idea-tournament.md](references/idea-tournament.md), [competitive-analysis.md](references/competitive-analysis.md) |
| Architecture, security, shortcuts, tests, Git | [prototype-engineering.md](references/prototype-engineering.md), then [architecture-strategy.md](references/architecture-strategy.md) if needed |
| UI feels generic or unfinished | [ui-ux-strategy.md](references/ui-ux-strategy.md) |
| Golden Path, wow moment, flaky dependency | [demo-engineering.md](references/demo-engineering.md) |
| Sponsor prize | [sponsor-strategy.md](references/sponsor-strategy.md) |
| Pitch or judge questions | [pitch-strategy.md](references/pitch-strategy.md), [judge-psychology.md](references/judge-psychology.md) |
| Deadline or scope pressure | [time-management.md](references/time-management.md), [failure-and-emergency.md](references/failure-and-emergency.md) |
| Tools, MCPs, or multiple agents | [agent-and-tooling.md](references/agent-and-tooling.md) |
| README, screenshots, video, final form | [submission-strategy.md](references/submission-strategy.md) |
| Test this skill's behavior | [validation-playbook.md](references/validation-playbook.md) |

## Communication contract

During active hackathon work, respond situationally:

1. **CURRENT SITUATION** — time mode, Golden Path state, largest risk.
2. **HIGHEST VALUE ACTION** — one decisive action.
3. **WHY** — rubric/demo effect and tradeoff.
4. **IMPLEMENTATION** — perform or specify only the relevant work.
5. **NEXT CHECKPOINT** — observable pass condition and next review time.

Do not dump the whole handbook. Distinguish external claims as `VERIFIED`, `LIKELY`, `ASSUMPTION`, or `UNKNOWN`, with links where possible. Ask only for missing input that materially changes strategy or needs user authorization.

## Completion gate

Do not call a project finished until the final win audit is answered. Optional quality gaps may be accepted explicitly; unmet mandatory rules, unsafe exposure, or an unsubmitted entry remain blockers and cannot be waived by the team:

1. Problem explainable in 15 seconds; solution in one sentence.
2. Central claim and Golden Path genuinely work.
3. Wow moment is deliberate, visible, and timed.
4. Key screens are judge-ready and use realistic data.
5. Highest-weight criteria have visible, defensible evidence.
6. Technical contribution and all mocked/simulated parts are explainable honestly.
7. Required deployment/demo format works; allowed fallbacks are ready. Localhost or a recording does not satisfy a mandatory public or live-only requirement.
8. Pitch fits the exact duration; likely judge questions have credible answers.
9. Submission is valid, complete, backed up, and entered before the final minutes when possible.
10. Biggest remaining risk and highest-value remaining task are explicit.

Use `scripts/rubric-audit.py`, `scripts/submission-audit.py`, and the audit sequence in [validation-playbook.md](references/validation-playbook.md) where helpful. Passing a script is not proof that the product is judge-ready.

Read [research-sources.md](references/research-sources.md) when reviewing provenance; historical examples do not establish this event's rules.
