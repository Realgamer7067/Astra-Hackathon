# Prototype Engineering

Use for stack, scope, implementation, security, testing, dependency, Git, and shortcut decisions.

## Optimize for the judged prototype

Prefer the fastest stack the team can confidently build, debug, and deploy. Team familiarity, ecosystem, component availability, AI-tool compatibility, and rollback speed usually matter more than theoretical elegance.

Do not replace a working system—React with another web framework, one hosted database with another, REST with GraphQL, Python with Rust—unless the migration has specific measurable judging value and fits the current time mode.

Use mature UI libraries, auth providers, hosted databases, SDKs, chart/animation libraries, and icon systems when they accelerate P0/P1. Do not add a dependency merely because it is fashionable. Check maintenance, license, bundle/latency impact, and whether the team can debug it.

## Demo-first architecture

Architect backward from the Golden Path:

`entry -> core input -> real processing -> clear result -> wow moment -> impact`

Remove signup friction, optional setup, deep navigation, and long waits from this path. Implement `?demo=true` or an equivalent mode when it makes behavior deterministic, preloads realistic data, bypasses nonessential onboarding, or reveals the core experience faster.

The main claim must work end-to-end. Classify every supporting system:

- **REAL:** genuinely implemented and required for the central claim.
- **SIMULATED:** realistic simplified behavior backed by some live logic.
- **MOCKED:** static or prerecorded secondary behavior.
- **FALLBACK:** used only when the live dependency fails.

Document classifications in `ARCHITECTURE.md` and `POST_HACKATHON.md`. Proactively label material simulated, mocked, cached, or prerecorded behavior in the demo/submission; do not wait for a judge to ask. Never fabricate usage metrics, integrations, or functionality.

## Controlled shortcuts

Usually acceptable when disclosed and not central:

- seeded data and predefined demo users;
- simplified role mappings or minimal middleware;
- cached known-good external responses;
- mocked expensive secondary calls;
- a single demo organization or region;
- local fallback data;
- minimal onboarding and validation focused on judge-visible or dangerous inputs;
- hidden or feature-flagged incomplete routes.

Demo entry may skip onboarding, never privileged authorization. An unauthenticated `?demo=true` must only access isolated synthetic, read-only, or explicitly restricted data/actions. Public paid inference needs a simple spend/quota control and bounded execution; synthetic data does not eliminate financial abuse risk. A hidden button is not backend access control. Keep privileged keys server-side and use trivial injection safeguards such as parameterized queries.

Never fake the central innovation. A beautiful shell around a nonfunctional core is not demo-ready.

Label material shortcuts close to the implementation and summarize them in `POST_HACKATHON.md`, for example:

`HACKATHON SHORTCUT: Demo accounts use predefined role mappings. Replace with persistent RBAC before production deployment.`

## Security boundary

Prototype security is risk-weighted, not absent.

Always:

- keep secrets out of source, logs, screenshots, client bundles, and public submissions;
- use environment variables and provider-supported authentication;
- avoid real sensitive participant or user data when realistic synthetic data suffices;
- protect destructive, privileged, or expensive actions with the simplest reliable control;
- validate judge-visible and dangerous inputs first;
- preserve provider security controls unless a documented prototype need justifies a safe alternative.

For domains where incorrect output can harm people, narrow the claim, use synthetic data and human review, and avoid autonomous real-world actions. A short deadline does not turn safety-critical operation into an acceptable shortcut.

Normally defer custom RBAC frameworks, exhaustive authorization matrices, enterprise rate limiting, security observability, and full threat-model remediation unless the rubric, domain, deployment exposure, or central workflow requires them. Record the debt.

## Technical depth

If technical depth is scored, choose one or two defendable elements—retrieval, realtime sync, multimodal processing, optimization, edge inference, ranking, caching, graph logic, computer vision, orchestration, or a difficult integration. Make them real enough to inspect, explain, and demonstrate. Avoid fake complexity and architecture theater.

## Testing order

1. Golden Path end to end.
2. Central technical claim and deterministic known-good case.
3. Authentication only if the demo requires it.
4. External API failures and fallback mode.
5. Deployed build and judge-visible pages.
6. Projector/demo resolution, console errors, loading/error/success states.

Add focused automated tests where they shorten repeated verification. A huge suite is production-only unless testing itself is judged. Measure performance only where it affects loading, response time, animation, or a scalability criterion.

## Git and deployment

- Commit small meaningful milestones frequently.
- Keep a stable, identifiable demo commit or tag such as `demo-working-v1` or `submission-safe`.
- Use `main` plus short-lived branches when useful; avoid ceremony.
- Integrate early enough to find conflicts.
- Deploy a thin path early and keep a local working version.
- Do not destroy the last known-good state while chasing polish.

When time is short, freeze architecture. Permit bug fixes, content, UI polish, demo reliability, and submission work; reject framework migrations, speculative infrastructure, and large schema changes.
