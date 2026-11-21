# Safe, evidence-based test plan

**Scope:** review first. No real hardware tests are automatic. Some builds/tools write outside the source tree and may execute project-controlled scripts; obtain permission if the environment or user's restrictions require it. Never do dangerous hardware changes simply to improve a score.

## Inspection commands (require controlled execution)

- Use the hardened inventory helper first. For additional Git inspection, apply the same execution restrictions described in `COVERAGE_AND_EXECUTION.md`; ordinary Git commands may invoke configured monitors, filters, diff drivers or network object retrieval. Read config and attributes safely before running ad hoc commands. Do not assume a command is side-effect-free from its name.
- Inspect `Documentation/devicetree/bindings/` at the *pinned target SHA*, not just online latest.
- Inspect `MAINTAINERS`, relevant `Documentation/driver-api/`, `Documentation/core-api/`, `Documentation/process/`, and subsystem tests in the pinned repository.
- Inspect the tool program/script itself and its flags. Tools may install dependencies, emit generated code or write cache files if invoked without precautions.

## Build/static-check matrix (only if authorized)

Use a separate build directory with `O=/path/outside/repo`; capture command, toolchain version, kernel SHA, arch, compiler flags, input config and all diagnostics. Do not assume `make O=` prevents all script side effects in a compromised/untrusted repo. Inspect generated scripts as needed.

| Check | Why | Limits |
|---|---|---|
| `git diff --check` | whitespace/conflict markers | no semantic checking |
| `scripts/checkpatch.pl --no-tree < patch` | kernel style and suspicious constructs | false positives; does not prove correctness |
| ARM64 kernel build with relevant defconfig | compiler/linker errors and integration | only compiled config paths |
| `make O=<out> ARCH=arm64 dt_binding_check` | validate binding schemas | broken schemas can cause skip in DTB validation; inspect full output |
| `make O=<out> ARCH=arm64 dtbs_check` | validate DTB against applicable schemas | silent gaps if bindings missing/broken; binding compliance is not electrical truth |
| `make O=<out> ARCH=arm64 W=1 ...` | extra warnings | version/toolchain sensitive |
| `make O=<out> ARCH=arm64 C=1 ...` | sparse, where available | type/static analysis only; tests config-specific |
| Smatch / Coccinelle | flow analysis and common misuse patterns | requires correct setup, false positives/negatives |
| KUnit / kselftest | targeted logic and user ABI | requires test design/appropriate host/target |

Capture missing-tool findings accurately: e.g. `NOT RUN: sparse unavailable`, not `PASSED`. If a command partially executes or times out, say so and preserve logs.

## Hardware (plan only until authorized and arranged)

For each supported feature, define test ID, exact board variant and installed kernel/DTB hash, environment, observable output, pass/fail threshold, known risks, rollback/recovery plan and missing evidence. Start with non-destructive reads; avoid repeated thermal/power/voltage experiments, unsafe MMIO and flashing.

Functional/regression categories:

1. Cold boot vs reboot; recovery from missing supplier and firmware; normal/unusual firmware versions.
2. Normal operation across all supported user-visible capabilities, not just existence of a device node.
3. Secure/unprivileged access boundaries; unexpected devices, reserved memory and MMIO ranges never exposed.
4. Runtime idle, system sleep/wake, screen off/on, wireless connect/disconnect, low power, error injection if safe and subsystem-supported.
5. Repeated initialization, rebind only where explicitly supported, race stress only after environment and risk review.
6. Power/thermal/performance compared to physically valid hardware limits (do not blindly import vendor speed bins).
7. Negative tests (missing optional/peripheral, wrong DTS, firmware failure) generally need emulation, debug support or a controlled spare device; **do not** pretend these were performed on production hardware.

## Evidence and signoff

A test row needs `Test ID | scope commit/config/DTB | preconditions | exact command or procedure | actual output/log | result | risk | evidence artifact`. User-provided logs require verification they correspond to the same build. Never alter test data to make a conclusion appear stronger. If not executable, provide expected observable evidence and mark UNKNOWN.

## Validate the reviewer before relying on it

Run `python3 <skill-dir>/scripts/test_review_scope.py -v` in a disposable environment. Tests exercise synthetic repositories; they neither validate a real kernel nor prove the absence of helper defects. Preserve actual output and tool versions. Use an independent reviewer to challenge real findings and try to falsify claimed invariants when available; agent agreement alone is not evidence.
