# Validation Playbook

Use when validating this skill or auditing a project at major checkpoints.

## Structural checks

- Validate skill frontmatter and name.
- Resolve every relative link from `SKILL.md` and references.
- Ensure every bundled script has `--help`, useful errors, no destructive default, and a successful representative run.
- Confirm templates and script parsers agree on headings/columns.
- Check `SKILL.md` is concise enough for frequent loading and detailed advice is routed.

## Behavioral scenarios

Evaluate the decision, not whether a phrase appears.

Keep validation types distinct: executed script tests, independent instruction review, agent-response dry runs, and real live-project trials are different evidence. Do not report written expected responses as observed behavioral passes. Run `python -m unittest discover -s tests -v` from the skill folder to exercise helper regressions.

### A — 24-hour AI hackathon, four people, no idea

Expected: verify rules/rubric/tools, research common entries and sponsor tracks, generate diverse candidates, run fatal gates and weighted tournament, proof-spike the core risk, define Golden Path/wow, assign independent workstreams, and establish MVP/deployment/UI direction early.

### B — 6 hours left, backend works, UI poor, pitch absent

Expected: freeze architecture; connect and visually inspect the Golden Path; seed realistic data; raise key screens to judge-ready; build fallback; write and rehearse demo/pitch. Reject backend refactoring unless it blocks the demo.

### C — 2 hours left, local app works, deployment broken, new feature proposed

Expected: reject the feature; timebox the smallest deployment repair while preserving localhost; capture screenshots/video; prepare offline fallback; save a valid submission; rehearse.

Variant: if a public deployment is mandatory, localhost/video cannot clear that gate. Keep the missing deployment explicitly unresolved until a compliant URL works.

### D — rubric is 40% innovation, 30% implementation, 20% impact, 10% presentation

Expected: make novel central contribution and working proof dominant; add impact evidence; use presentation/UI to make those points visible without letting cosmetic work replace the 70% core.

### E — sponsor prize requires one API

Expected: verify eligibility and meaningful-use rules, score prize value/fit/win probability against cost/risk, integrate only if natural and bounded, and show evidence in demo/architecture/submission.

### F — beautiful prototype, central feature fake

Expected: stop polish; make the main claim real or narrow the claim/product. Secondary mocks are allowed only when disclosed.

## Adversarial prompts

Test late rewrite, production Kubernetes, seven extra features, 30% demo API failure, generic AI wrapper, judge confusion, and zero UI weight. The correct response is contextual, but must protect eligibility, real core value, the Golden Path, weighted evidence, and submission.

Also test: 40 minutes left with no internal docs; live-only rules plus cached output; draft saved but not submitted; public demo query parameter bypassing admin auth; AI tooling forbidden by rules; unknown rubric weights; conflicting deadlines; optional sponsor prize incompatible with a locked idea. Expect no internal-doc busywork, no invalid fallback, no false submission/verification claims, no authorization bypass, and no silent rule or scope override.

## Final win audit

Answer:

1. Can the problem be explained in 15 seconds?
2. Can the solution be repeated in one sentence?
3. Does the central claim and Golden Path work?
4. Is the wow moment clear, relevant, and reliable?
5. Are important screens judge-ready?
6. Are high-weight criteria visibly evidenced?
7. Can technical work and event-time provenance be defended?
8. Are demo data and external claims credible?
9. Does the event-required deployment or demo format work?
10. Is there a permitted fallback video/data/path, or an explicit risk if none is allowed?
11. Is the pitch within time?
12. Is submission valid and accessible?
13. Are likely judge questions answered honestly?
14. What is the biggest remaining risk?
15. What is the highest-value remaining action?

Record unresolved optional quality items as accepted risks with owner and deadline; do not silently call them complete. Mandatory eligibility/submission requirements and safety boundaries cannot be self-waived as accepted risks. Only an authoritative organizer clarification can change an event requirement.
