# Exhaustive review protocol

## Why this is different from a conventional AI code review

A typical code review samples modified hunks and searches for obvious bugs. Here the requirement is **traceable total change coverage plus semantic depth**. An auditable ledger cannot establish correctness by itself: external hardware facts, failure-path tests and trusted source citations are required. Keep these independent.

## Phase A: Freeze scope and threat model

1. Identify exact source repository, Linux base SHA, current HEAD, uncommitted changes, firmware version, Exynos model, PCB and peripheral variants. Do not assume a board revision from marketing name. Record whether changes are upstream backports, an out-of-tree port, new functionality, vendor reimplementation or generated code.
2. The integration base may be a known upstream commit or a reviewed prior snapshot. The audit target is *the actual intended installation*, including vendor binaries, initramfs/service changes if their effects matter. If there is no trustworthy comparison base, use limited implementation-review mode: inspect accessible behavior but mark complete change coverage NOT ESTABLISHED; do not invent a base or claim all implementation-agent changes were reviewed.
3. Run the scope inventory. Do not put audit files in Git source. Snapshot diff patches; track untracked, ignored and submodules explicitly. For external overlays, secondary trees or overlay packaging, generate an additional scope for each repo. If there is a single patch applied elsewhere, inspect the destination version too.
4. Resolve ignored and generated files as one of: verified reproducible output (record generator/input hash), active source (review), unused artifact (document evidence), opaque binary (review provenance and effects), or unresolved. The default is **unresolved**, not "harmless".
5. Read current code of the whole affected file/function and cross-function call graph even where those lines predate the patch. Track `git blame`, `git log -S/-G`, and function history if the assumption requires it. A modified constant can be safe on its own but wrong in the state machine it changes.

## Phase B: Build a hardware → driver → userspace map

For each device: physical block/chip, address/bus and revision; dependencies (supply, clock, reset, IRQ, GPIO, pinmux, power domain, interconnect, DMA/IOMMU); DT provider and consumer; specific kernel driver; subsystem class; expected ABI/user-facing nodes; firmware requirements; lifecycle and power states; security and trust boundary. Confirm each connection. For Wi-Fi also record SDIO/PCIe/USB wiring, rfkill, module power sequencing, MAC identity/provenance, NVRAM, firmware, regulatory handling and wake events (if supported).

Distinguish:
- **Observed** (tested on the exact board, with logs and timestamps).
- **Specified** (datasheet, schema or documented OS contract).
- **Inferred** (cross-checked but hardware proof not available).
- **Unknown** (requires evidence).

A Linux node does not establish hardware presence. Probe logs do not establish correct pinmux or voltage. A vendor register write does not establish sanctioned behavior. A workaround may be justified by erratum, but needs traceable applicability and minimal scope.

## Phase C: Two-directional review of all diffs

Read changes in **forward and reverse** direction. For each added line ask why it exists, what owns it, whether another layer already does it, and which failure path covers it. For each deleted line ask what behavior it used to provide, what replaces it, and whether removal breaks other boards or ABI. For moved or format-only code, verify semantic equivalence and note changed blame/traceability. For binary, mode, symlink, submodule and generated changes, inspect the content/provenance or explicitly mark `UNKNOWN`.

On the line ledger, record a concise evidence-backed outcome for **every entry**, including whitespace-only lines (`N/A` with reason is acceptable when proven irrelevant). Do not rubber-stamp a batch of code lines by placing the same generic explanation on each line. A group-level design proof can be referenced by multiple lines only if it is a real, locatable artifact that covers each group member and each line has been inspected. Especially inspect deletions and lines from commits later reverted.

Perform focused subreviews of each register access, DT property, fallback/magic value, array bound, concurrency primitive and all public/privileged interfaces. Trace all error paths and resource unwinding. Search for shared code that changes behavior for unrelated devices, even if its lines were not touched.

## Phase D: Challenge assumptions

Adopt at least four perspectives:

- **Hardware reviewer:** wiring, datasheets, power and reset timings, boot ROM/bootloader assumptions, eFuses, board-specific differences.
- **Subsystem maintainer:** ownership model, DT ABI, reuse, naming, bindings, missing generic properties, acceptable architecture and standard subsystem paths.
- **Security reviewer:** exposure/permissions, trust zones, DMA isolation, firmware loading, memory safety and userspace input validation. Also find excessive denial of legitimate userspace access.
- **Reliability reviewer:** degraded conditions, suspend/resume, cold boot and clean teardown, races, interrupts, partial hardware, slow peripherals, resource failures, error propagation and rollback.

If another agent is available, it may serve as an independent checker only if it receives the pinned scope and upstream sources, **not** the original agent's rationale or suggested verdict as the sole source of truth. Ask it to produce counterexamples, then compare. Agent agreement is not proof.

## Phase E: Evidence and resolution

For each concern record:

`finding ID | subsystem | exact path:line | observed code | expected contract | violating scenario | source/proof | counterevidence | severity | confidence | fix direction (NO edit) | test that would resolve it`.

For an unverified suspicion, state a hypothesis and concrete way to falsify it. Link the appropriate ledger rows. For accepted quirks, explain why a spec-compliant generic route does not apply.

## Phase F: Decision gates

1. **Scope gate:** every relevant artifact represented, file-level changes, deleted lines and unknown binaries surfaced; scope fingerprint unchanged.
2. **Disposition gate:** `verify` succeeds for the parent and every required linked child scope. Exit 0 means internally consistent dispositions, not semantic clearance or genuine citation verification. Report UNKNOWN/FINDING totals even on exit 0. Separate inventory completeness from review depth.
3. **Evidence gate:** substantive claims have correctly scoped, independent sources and resolved conflicts.
4. **Correctness gate:** for changed driver/API behavior, invariants and failure paths were reasoned about; missing dynamic validation is recorded.
5. **Upstream gate:** no unjustified board hacks or binding-ABI mistakes, maintainer-specific conventions examined.
6. **Final gate:** critical/high unresolved findings or unknown safety-critical properties ⇒ `NOT READY` or `BLOCKED`. Unknown low-risk properties may permit `CONDITIONALLY REVIEWED` with explicit limitations. `READY FOR HUMAN UPSTREAM REVIEW` means ready for expert scrutiny, not accepted or guaranteed correct.

Never summarize 40,000 changed lines as "all checked" unless the fingerprinted inventory, completed ledger and batch artifacts actually document them. If a review is interrupted, report the exact number reviewed and outstanding; persist outputs for resumption.

## Batch and resumption discipline

Partition by subsystem and deterministic phase/path/line ranges. Record which artifact and complete function each batch read, claim IDs, reviewed callers/dependencies, findings, tests and unresolved IDs. Count phase-specific ledger items separately from distinct current-tree added/deleted lines: the same line may occur in final-tree, staged, unstaged and historical phases. Do not add those counts and call them unique source lines.

Review current behavior first, then the complete historical delta required by scope. A reverted bug is a history finding, not a present regression unless current effects remain. Verify merge results, first-parent resolution changes and shared dependency effects; a first-parent patch is not itself proof of the author's intention.

Save the checkpoint before interruption. On resumption, check the recorded hashes and revalidate scope before reusing claims; an incomplete ledger is expected during work. A coverage-verification failure caused only by unfinished dispositions is not evidence that source drifted. Source drift requires a new scope and targeted revalidation of carried-forward analysis.
