# Rubric and Prioritization

Use whenever deciding what to build, cut, polish, or demonstrate.

## Translate the rubric into visible proof

Create `RUBRIC.md` from the template and keep one row per criterion:

| Criterion | Weight | What Judges Want | Our Evidence | Demo Moment | Current Strength | Missing Work |
| --- | --- | --- | --- | --- | --- | --- |

Do not translate "technical innovation" as "many technologies." Translate it as: a judge can identify within about 30 seconds which genuinely difficult, novel, or unusually integrated technical contribution the team built and can see proof.

For each criterion:

1. Read its official definition and examples.
2. Identify the judge's likely question.
3. Define observable evidence: working behavior, measured result, architecture, source, user proof, or comparison.
4. Place that evidence in the demo, pitch, submission, or repository.
5. Score current strength from 0-5 only after inspecting the evidence.
6. List the smallest missing action that could raise the score.

If weights are absent, mark them `UNKNOWN`; do not pretend all criteria are equal. Use an explicit temporary weighting assumption only when a decision cannot wait.

## Feature gate

Every proposed feature must answer:

- Which criterion or eligibility rule improves?
- What will the judge see or believe differently?
- Is it on the Golden Path?
- What is the probability it works before the deadline?
- What higher-value task does it displace?

If it improves no criterion, no demo, no credibility, and no submission safety, cut it.

## Priority model

Use estimates, not false precision:

`Priority = RubricImpact x DemoImpact x ProbabilityOfSuccess / TimeCost`

Apply multipliers when appropriate:

- Hard eligibility/submission blockers are gates outside numeric ranking, not just multipliers.
- `x1.5` for a broken Golden Path or missing high-weight evidence.
- `x1.25` for a reliable wow moment.
- `x0.5` for judge-invisible or production-only work.
- `x0.25` for an architecture migration with no measured benefit.

The numerical result ranks work; it does not replace judgment. A low-cost task cannot compensate for a fake central claim.

Estimate marginal improvement in the current evidence, not total criterion weight. Use demo impact as an enabling value for invisible prerequisites instead of multiplying their priority to zero. Include integration/test/recovery in time cost; never divide by zero. Score ranges and uncertain probabilities are estimates, not measured win likelihoods. Check whether the top choice survives a plausible change in estimates.

## Periodic project audits

Run the full sequence after idea lock, after the first end-to-end Golden Path, at feature freeze, and before final submission. Under severe time pressure, run only the audit most likely to expose a submission, demo, or high-weight rubric failure.

- **Product Audit:** Is the user/problem clear and believable?
- **Rubric Audit:** Is each high-weight criterion visibly earned?
- **Technical Audit:** Does the core contribution genuinely work and withstand questions?
- **Visual Audit:** Are key views judge-ready at demo resolution?
- **Demo Audit:** Can the Golden Path run repeatedly with a recovery plan?
- **Time Audit:** Is current work appropriate for the time mode?
- **Submission Audit:** Is a valid version already saved, or can it be saved now?

Run `scripts/rubric-audit.py --help` for a document-level gap scan. It detects missing evidence in `RUBRIC.md`; it cannot verify the actual build.

## Weighted-rubric behavior

When a rubric is 40% innovation, 30% implementation, 20% impact, and 10% presentation, prioritize real, demonstrable novelty first, then a functioning Golden Path, then credible impact evidence. Presentation polish remains necessary to make the other 90% legible, but cosmetic work must not replace the central innovation or implementation.

If UI has zero explicit weight, do not ignore design. Apply a smaller enabling value: clarity, speed, trust, and presentation can determine whether judges recognize the weighted evidence. Stop polishing when further changes no longer improve comprehension or perceived completeness.
