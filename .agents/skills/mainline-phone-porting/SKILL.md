---
name: mainline-phone-porting
description: Research-first, evidence-gated work on mainline Linux support for Android phones and tablets. Use for device feasibility studies, SoC and board research, vendor-tree archaeology, old patch evaluation, DTS or driver bring-up, postmarketOS integration, evidence-led debugging, and upstream patch preparation. Do not use it to invent board data or promise support from retail specifications.
---

# Mainline Phone Porting

## Non-negotiable principle

**Do not guess hardware support into existence. Research the device deeply, establish evidence and dependencies, then propose the smallest justified implementation or test.**

A booting kernel, a working downstream Android kernel, a postmarketOS device page, and support for the same SoC are four different facts. Never silently treat one as proof of another.

## Default operating mode

For new devices and substantial subsystems, spend most effort on source discovery, cross-checking, history, and dependency tracing before code. Maintain an evidence ledger and a hypothesis ledger. Research continues until one small change or experiment is justified; it does not continue merely to collect links.

Label every decision-relevant claim:

- **Verified** — direct primary source, exact source-tree evidence, binding, schematic, trustworthy target log, or reproduced result.
- **Strongly supported** — multiple independent reliable indirect sources agree.
- **Plausible** — bounded hypothesis with a falsifiable validation method.
- **Unknown** — insufficient or conflicting evidence; do not implement from it.

Never fabricate hardware, variants, compatibles, registers, addresses, GPIOs, IRQs, regulators, clocks, resets, power domains, interconnect paths, firmware names, DTS properties, panel sequences, timings, boot commands, support status, or patch applicability. Never claim two boards share a component because they share a SoC or retail family.

## Read only the references needed

- **New device, feasibility, or complete support landscape:** read [research-methodology.md](references/research-methodology.md), [source-hierarchy.md](references/source-hierarchy.md), [hardware-inventory.md](references/hardware-inventory.md), [soc-family-research.md](references/soc-family-research.md), [ecosystem-and-projects.md](references/ecosystem-and-projects.md), and [device-research-dossier-template.md](references/device-research-dossier-template.md).
- **Old commits, abandoned series, forks, or vendor patches:** read [git-and-patch-archaeology.md](references/git-and-patch-archaeology.md), [downstream-kernel-translation.md](references/downstream-kernel-translation.md), and [source-hierarchy.md](references/source-hierarchy.md).
- **Comparing another phone or reference board:** read [sibling-device-analysis.md](references/sibling-device-analysis.md).
- **DTS, DTB/DTBO, binding, Kconfig, or driver question:** read [dts-and-driver-tracing.md](references/dts-and-driver-tracing.md) and the relevant sections of [common-failure-modes.md](references/common-failure-modes.md).
- **Forward-porting an Android/vendor kernel implementation:** read [downstream-kernel-translation.md](references/downstream-kernel-translation.md); translate hardware intent into current subsystem design rather than mechanically rebasing vendor code.
- **Boot images, slots, AVB, bootloader behavior, or recovery:** read [boot-chain-and-recovery.md](references/boot-chain-and-recovery.md). Do not provide a flashing command until the exact device path and recovery route are verified.
- **Firmware, remoteproc, modem, Wi-Fi, audio DSP, camera, or userspace boundary:** read [firmware-and-userspace-boundaries.md](references/firmware-and-userspace-boundaries.md).
- **Boot failure or broken hardware:** first inventory the evidence, then read [debugging-from-evidence.md](references/debugging-from-evidence.md) and the relevant failure-mode section.
- **Bring-up sequencing:** read [bringup-stages.md](references/bringup-stages.md).
- **Preparing upstream work:** read [upstreaming.md](references/upstreaming.md).
- **Choosing tools or establishing a workstation:** read [tool-map.md](references/tool-map.md).
- **Compiling upstream or Android/vendor kernels, configs, modules, DTBs, or checks:** read [toolchain-and-builds.md](references/toolchain-and-builds.md).
- **ARM32 phone/tablet or `ARCH=arm`, zImage, ATAGS, machine-ID, legacy SMP/entry-state question:** read [arm32-mobile-bringup.md](references/arm32-mobile-bringup.md), [toolchain-and-builds.md](references/toolchain-and-builds.md), and [boot-chain-and-recovery.md](references/boot-chain-and-recovery.md).
- **Creating, inspecting, applying, or packaging DTS/DTB/DTBO artifacts:** read [devicetree-tooling.md](references/devicetree-tooling.md).
- **Inspecting or rebuilding boot/vendor_boot/init_boot/dtbo/vbmeta/super images:** read [android-image-tooling.md](references/android-image-tooling.md).
- **Using pmbootstrap/pmaports for build, packaging, export, or device integration:** read [postmarketos-workflow.md](references/postmarketos-workflow.md).
- **Selecting fastboot, fastbootd, Heimdall/Odin, recovery, or SoC-specific flash tools:** read [flashing-tools.md](references/flashing-tools.md) and [boot-chain-and-recovery.md](references/boot-chain-and-recovery.md). Research the exact device before giving commands.
- **Collecting evidence from stock Android or a running mainline test:** read [target-evidence-collection.md](references/target-evidence-collection.md).
- **No/partial early logs, serial/earlycon, pstore, or minimal initramfs work:** read [early-boot-observability.md](references/early-boot-observability.md).
- **Choosing the readiness gate and response shape:** read [response-modes-and-readiness.md](references/response-modes-and-readiness.md); use only the contract matching the request.

Reusable local helpers:

- [index-kernel-evidence.py](scripts/index-kernel-evidence.py) searches a named commit by default; its explicit working-tree mode preserves tracked and relevant untracked evidence.
- [build-kernel-artifacts.sh](scripts/build-kernel-artifacts.sh) uses a fresh out-of-tree Kbuild directory by default and records pre/post inventories, changed-output hashes, source snapshots, and resolved tool provenance.
- [apply-and-verify-dt-overlays.sh](scripts/apply-and-verify-dt-overlays.sh) applies overlays to a base DTB offline and records the merged artifact.
- [pack-dtbo-image.sh](scripts/pack-dtbo-image.sh) wraps AOSP mkdtimg cfg_create with an explicit configuration and produces a dump/hash.
- [test_helpers.py](scripts/tests/test_helpers.py) runs isolated host-side regression tests for provenance, stale-output exclusion, no-clobber behavior, LLVM naming, and DT-tool fingerprints.

These scripts never flash, sign, unlock, repartition, or choose target-specific values. Inspect their help before use. Automated success proves artifact construction only, not hardware correctness or bootloader compatibility.

## Scope the dossier before implementation

Use a whole-device dossier for feasibility studies, new-device bring-up, or a requested complete landscape. For a narrow feature, patch, build, or failure, scope the dossier to that question, the exact device/repository identity needed to answer it, and all transitive dependencies. Do not investigate unrelated camera, modem, audio, or RF paths merely to satisfy a global checklist.

Before proposing a non-trivial DTS change, driver port, or patch application, produce or update the appropriately scoped dossier containing:

1. Exact identity and variant boundaries.
2. Component inventory with confirmed and inferred items separated.
3. Current upstream, linux-next, lore, binding, driver, Kconfig, and maintainer landscape.
4. Matching vendor/downstream source and artifact archaeology.
5. Justified sibling comparison.
6. Feature dependency graph, including firmware and userspace.
7. Boot/recovery boundary and safe validation route.
8. Contradictions, unknowns, and the smallest artifacts that would resolve them.

Treat postmarketOS, pmaports, pmbootstrap, Droidian, Mobian, UBports/Halium, LineageOS, community mainline trees, and device wikis as high-value leads and reproducibility evidence—not automatic proof of upstream support or board identity.

## Research readiness gate

State the scope first, then use the applicable gate from [response-modes-and-readiness.md](references/response-modes-and-readiness.md). For feature implementation, this compact gate is the default:

~~~text
Research readiness:
- Scope: <requested feature plus transitive dependencies>
- Target identity/revision: verified / incomplete / unknown
- Scope evidence inventory: verified / incomplete / unknown
- Relevant upstream/pending support mapped: yes / no / not applicable
- Relevant vendor/target evidence analysed: yes / no / unavailable / not applicable
- Sibling comparison justified: yes / no / not applicable
- Transitive dependencies mapped: yes / no
- Safe validation method available: yes / no / not applicable
- Recommendation confidence: verified / strongly supported / plausible / unknown
~~~

If an essential item is incomplete, ask for the smallest useful artifact or conduct more research. The user asking for “a patch now” does not make Unknown values safe to encode.

## Action and safety contract

For every action, state: goal; evidence; exact files/subsystems; dependencies; assumptions; risk; smallest test; expected result/log; failure signal; rollback/recovery; and what the test will and will not prove.

Prefer transient booting or reversible tests when the verified bootloader supports them. Require explicit user confirmation immediately before unlocking, flashing, erasing, formatting, repartitioning, changing slots, overwriting boot-critical firmware, or any action that may lose data or leave the device unbootable. Never assume fastboot commands, partition names, slot behavior, Odin/Download Mode behavior, or recovery capabilities transfer between devices.

Do not weaken battery, charging, thermal, secure-boot, or RF safeguards merely to obtain a positive result. Do not alter modem identity/calibration data. Treat speakers, batteries, panels, storage, and RF firmware as damage-sensitive.

## Substantive response format

Do not force every request into a 13-section report. Select the feasibility, feature implementation, debugging, patch archaeology, build/artifact, or flashing contract in [response-modes-and-readiness.md](references/response-modes-and-readiness.md).

Every substantive response still states: **Goal and scope; evidence and confidence; material unknowns; assessment; smallest justified next step; validation/proof boundary; and risks/rollback where applicable.** Add full inventories, source tables, dependency graphs, readiness blocks, or command gates only when the selected mode requires them.

Use compact tables for hardware, source provenance, support state, patch applicability, sibling differences, contradictions, and feature dependencies. Separate current upstream, linux-next/pending work, community patch stacks, and downstream-only behavior.
