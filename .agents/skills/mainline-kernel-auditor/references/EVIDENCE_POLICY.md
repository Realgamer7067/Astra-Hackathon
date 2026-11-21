# Evidence quality and truth rules

## Evidence hierarchy (not rigid ranking)

- Exact target SoC/board **verified primary** documentation, public manuals, schematic, silicon errata, firmware/API spec, register tables.
- Version-pinned upstream kernel source and `Documentation/` with relevant interfaces, bindings and accepted maintainer patches.
- Matching vendor kernel source with immutable SHA, device revision, OEM configuration, firmware and bootloader assumptions.
- Mainline family/neighbor driver, other board, maintained community port, mailing list discussion and patch revision histories.
- Runtime data produced on exact hardware with build hash, actual `.config`, loaded DTB/DTBO, bootloader details and repeatable steps.
- Prior AI output, issue threads and unsourced wikis: leads only, never ground truth.

A high-priority source can be wrong or inapplicable; applicability determines weight. Direct observation is strong evidence for observed behavior, but weak evidence for absence of hidden bugs.

## Source record

Each external source citation should specify source class, canonical URL or local absolute repo path, **pinned commit/tag/doc version**, file path and exact function/line range or section, board/chip revision matching, review date and how it supports or contradicts the claim. Web search snippets are not sufficient where primary sources can be opened. Respect licenses for vendor sources. Do not send proprietary source code to web tools.

Example (ILLUSTRATIVE, NOT ACTUAL HARDWARE EVIDENCE):

`kernel-core@<sha> drivers/mmc/core/core.c function:mmc_start_host (behavior); bindings@<same sha> Documentation/devicetree/bindings/mmc/mmc-controller.yaml (properties); A50-vendor@<verified-sha> ... (board wiring); target dmesg@<boot-id> (observation).`

## Corroboration by claim, not citation quotas

- Binding and matching target-version driver source (separate facts; same repo is acceptable if each independently supports the line).
- Vendor board-specific wiring + SoC datasheet electrical specification.
- Kernel documented API contract + actual function and caller behavior.
- Mainline analog + observed exact-board test, if silicon equivalence has been established.

A Reddit post reproducing a GitHub comment is not independent. Two AI summaries of one source are not independent. Claims such as "PASS because it compiled" are insufficient for semantics; compiler success belongs in validation notes.

## Confidence

- **Confirmed:** exact contract and concrete violating path/test supported; no material alternative explanation.
- **High:** consistent authoritative evidence but lacks direct hardware exercise.
- **Medium:** analogous driver pattern or incomplete vendor context.
- **Low:** hypothesis, missing private datasheet, uncertain board variant.

Cite enough evidence to establish the actual claim. Do not require two citations for each brace or comment. Do require independent corroboration of material hardware facts and safety-critical/disputed assumptions; if unavailable, record precisely which inference remains unverified. A group argument must name the inspected rows, target-version invariants and supporting source locations.

A PASS does not mean fully tested. Link any important unexecuted test to an `UNKNOWN` row/issue.

## Contradictions

Record the conflict (e.g. vendor writes an undocumented bit; mainline code never does), hypotheses (bootloader state, different silicon revision, workaround), independent discriminating test, and provisional ruling. Avoid copying undocumented register operations into a generic driver merely because vendor did it. Avoid removing a needed operation merely because upstream example lacks it.

## Boundary/security considerations

On a mobile SoC, verify TrustZone/secure firmware/bootloader ownership and protected address regions; do not suggest probing protected areas as a casual test. Check debugfs permissions and kernel lockdown behavior when enabled, but do not arbitrarily hide ordinary interfaces. Distinguish permissions on sysfs from what an unprivileged process can do via interfaces supplied by that subsystem. Audit custom debug interfaces for capabilities checks and leakage. Review host versus device DMA access bounds.

## Reporting accuracy

Use `NOT RUN` for every test not executed, not `PASS` or `LIKELY PASS`. A boot log from a different kernel is not proof for this commit. If upstream documentation is for a different version, say so and cross-check the pinned version. If source is unreachable, give full attempted queries and mark unresolved; never produce plausible fake citations.

## Absence of evidence and source independence

Record attempted searches and what was actually opened. A search returning no result cannot prove a device, erratum or capability does not exist. Two copies of one vendor implementation are one provenance chain; accepted upstream code is evidence of that implementation's contract, not independent proof of undocumented electrical behavior. Source publication date and applicability matter more than apparent authority.

Do not infer author identity or independence from model branding. A fresh review with no implementation rationale reduces anchoring, but is not hardware validation. State whether an actual independent reviewer participated and what they inspected.
