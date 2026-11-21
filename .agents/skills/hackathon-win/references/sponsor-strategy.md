# Sponsor Strategy

Use whenever sponsor or partner prizes exist.

## Evaluate each prize separately

Record:

| Prize | Value | Required technology/use | Core-product fit | Evidence required | Likely competition | Integration effort | Failure risk | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Estimate:

`PrizeOpportunity = PrizeValue x Fit x WinProbability / IntegrationCost`

Use relative 1-5 or 1-10 scales; avoid pretending win probability is known precisely. Consider whether sponsor judging is separate from the overall track and whether multiple prizes can be won.

Compare uncertainty ranges, not invented competition counts or exact probabilities. Integration cost includes research, credentials, integration, verification, and the core work displaced. A zero-cost estimate still needs a small positive verification cost. Optional sponsor ineligibility does not invalidate the base project. If the user's selected track makes an integration mandatory, surface that tradeoff; do not silently change the track or locked idea.

## Eligibility before enthusiasm

Verify from current official sources:

- required API, SDK, model, chain, cloud, or dataset;
- minimum meaningful use and prohibited uses;
- track selection or declaration requirements;
- demo, code, attribution, branding, or open-source evidence;
- credits, quotas, regions, authentication, and data terms;
- deadline and whether sponsor judging uses different criteria.

Never claim eligibility from a logo, dependency, or superficial API call. Make sponsor use visible in the architecture, demo, repository, and submission when required.

## Natural-fit test

Integrate when the technology materially improves the central workflow, technical depth, reliability, or user result. Reject an awkward bolt-on when it adds failure risk, confuses the story, or delays P0.

When two integrations offer similar eligibility, prefer the one with:

- an SDK the team already knows;
- low setup and deterministic demo behavior;
- a visible result;
- good official docs and local fallback;
- a sponsor story explainable in one sentence.

## Late-integration rule of thumb

Under six hours, a sponsor integration must normally be demonstrably useful, bounded, and finishable within a small fraction of the remaining time. If the Golden Path, pitch, deployment, or submission is not safe, defer it.

Document the decision even when the answer is no; this prevents repeated reconsideration.
