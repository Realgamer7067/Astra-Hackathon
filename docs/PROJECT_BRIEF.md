# ASTRA Orbital Collision Lab

## Scope and authorization

The user supplied the ASTRA master specification and requested a proper four-person work plan followed by execution on 2026-11-21. This adopts that supplied concept; it does not establish official event rules, teammate assignments, completed implementation or measured performance.

- Event: VIT Bhopal ASTRA 2026; 24-hour target.
- Domain: Sustainable Space & Space Environment.
- Audience: students, researchers, communicators and non-expert judges.
- Promise: explore source-backed orbit estimates, construct clearly hypothetical collisions, replay physically propagated fragments, and inspect bounded orbital exposure.
- Differentiator: cinematic collision storytelling with inspectable numerical states and provenance.
- Official rubric, allowed prebuilt code, submission requirements and hosting budget: not supplied; coordinator must verify before submission or paid provisioning.

## Must-work journeys

1. Start offline with explicitly synthetic fixtures, or load a real/cached catalog; search, select and inspect objects and source age on a token-free globe.
2. Select two distinct objects, review assumed masses/radii and the forced-contact modification, run a seeded collision, see propagated debris, pause and replay.
3. Inspect shell occupancy, bounded selected-neighbor encounters, ground projections and only calculated entry crossings; export a factual report.

## Scope priorities

- MVP: satellite–satellite and satellite–debris forced hypothetical scenarios, deterministic propagation, provenance, timeline, exposure and offline demo.
- Generalized participant model supports debris/rocket bodies/inactive spacecraft without assuming operational status.
- Second tier: real JPL asteroid identity/ephemeris plus explicitly fictional state injection, secondary fragmentation, richer entry overlays and advanced mobile polish.
- Excluded: Earth-surface asteroid impacts, crater/blast/tsunami models, operational warnings, invented probabilities/outages/casualties, unbounded cascades.
- Targets, never reported as achievements: usable cached scene around 5 seconds, 5,000 markers around 30 FPS, 300–600 fragments over 24 hours around 60 seconds.

## Team and delivery

Four humans own feature lanes; the main agent coordinates and implements its lane. A separately invoked reviewer inspects all PRs. The user takes collision lane B (TASK-003), foundation and coordination. Catalog lane A is proposed for Teammate 2. Names and merged claims remain pending. See [execution plan](PLAN.md), [contracts](CONTRACTS.md), [architecture](ARCHITECTURE.md) and [source specification](ASTRA_MASTER_PROMPT.md).

## Decisions

- Concept and planning: authorized by the current user request.
- Recommended stack: adopted as the implementation baseline in ARCHITECTURE.md; package versions await installation/API verification.
- Ready task claims: must merge before significant implementation under WORKFLOW.md.
- No application features have been implemented or verified.
