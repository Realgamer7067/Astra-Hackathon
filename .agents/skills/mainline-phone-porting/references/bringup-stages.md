# Dependency-ordered bring-up

Bring up one observable boundary at a time. Every stage has entry evidence, a minimal test, an exit criterion and a rollback. A later feature cannot compensate for an unverified foundation.

## Stage 0 — baseline, artifacts and recovery

Entry work:

- identify exact variant and installed firmware;
- capture known-good boot behavior, kernel/boot image metadata and relevant logs;
- preserve verified stock images from an official or target-derived source;
- map boot image format, partitions, slots, AVB and recovery modes;
- distinguish read-only, transient-boot and persistent tests.

Exit: the current state can be identified, and a failed proposed test has a credible restoration route. No destructive action occurs without immediate user confirmation.

## Stage 1 — observability

Aim for at least two independent signals where feasible:

- serial/early console;
- bootloader log or screen state;
- USB enumeration/initramfs network;
- pstore/ramoops already established by target evidence;
- heartbeat/reboot timing or other non-invasive state.

Do not invent a UART address or ramoops region. A silent console may be wrong pins/clock/parameters rather than a dead kernel.

Exit: kernel build/DT identity and the last reached phase can be distinguished.

## Stage 2 — minimal kernel execution

Validate the minimum platform chain:

- correct architecture/image and DT selection;
- memory map and reserved regions;
- exception level/PSCI and CPU bring-up;
- GIC, timer, console, watchdog/reboot;
- initramfs execution.

Keep the kernel config intentionally observable. Do not enable a vast vendor defconfig and call the result minimal.

Exit: repeatable boot into a controlled initramfs or equivalent early userspace with a complete log.

## Stage 3 — foundational providers

Bring up providers before consumers:

1. pinctrl/GPIO and interrupt controllers;
2. clock and reset controllers;
3. PMIC buses and regulators;
4. power domains and system controllers;
5. interconnect and IOMMUs;
6. firmware loaders/remote processors required by later blocks.

Use deferred-probe information and driver probe paths to find the earliest absent provider. Ignore-unused and always-on flags are bounded diagnostics, not completion.

Exit: provider graph is stable enough that target consumers either probe or fail with a specific, actionable reason.

## Stage 4 — storage and durable rootfs

Validate eMMC/UFS controller, PHY, supplies, clocks, resets, interconnect/IOMMU and block visibility before filesystem/userspace. Then distinguish:

- storage device visibility;
- partition discovery;
- initramfs module availability;
- filesystem support;
- dm/dynamic/encryption layers;
- root argument and userspace mount logic.

Prefer external/removable or initramfs workflows when supported and safer. Never make repartitioning a prerequisite for first boot.

Exit: reproducible access to the intended rootfs or a bounded storage-layer failure.

## Stage 5 — display and input

Display order:

1. display engine/IOMMU/interconnect/power;
2. PHY and host;
3. graph/bridge chain;
4. exact panel;
5. backlight;
6. KMS/userspace.

Input order: bus → supplies/pinctrl/reset → exact controller match → IRQ → firmware → events/coordinates.

Exit: a userspace-observable KMS connector/mode or input event with logs proving the native driver—not merely retained bootloader framebuffer—handled it.

## Stage 6 — USB and serviceability

Trace controller, PHY, role-switch/connector, Type-C/PD, VBUS and gadget/host userspace independently. A working USB gadget can become a valuable recovery/debug channel, but absence is ambiguous until boot is observed another way.

Exit: one declared role works repeatedly, disconnect/reconnect is sane, and failure does not endanger charging.

## Stage 7 — power-facing peripherals

Bring up battery reporting, charger, thermal sensors/zones, regulators, cpufreq/devfreq and cooling cautiously. Confirm units, profiles and limits from target evidence. Do not disable safeguards or stress-test an unvalidated power stack.

Exit: conservative monitoring is trustworthy; charge/thermal control is only called working after bounded runtime and suspend/resume tests.

## Stage 8 — audio, radios and sensors

Work in dependency order:

- audio DSP/codec/DAI/routing/topology/UCM, with speaker protection respected;
- Wi-Fi bus/power/firmware/calibration before association;
- Bluetooth transport/firmware/wake/coexistence before pairing;
- direct sensors or sensor-hub firmware/IPC before userspace transforms;
- GNSS/NFC with firmware/secure boundaries identified.

Exit: each feature has an exact test definition and target log, not a checkbox inferred from driver load.

## Stage 9 — suspend, resume and endurance

Audit wake IRQs, runtime PM, genpd, regulator/clock shutdown, remote processors, cpuidle, thermal state, idle drain and repeated resume. Fixing suspend may reveal incomplete descriptions intentionally hidden during early bring-up.

Exit: repeated cycles with logs and no known unsafe thermal/power behavior. Daily-driver claims require longer stability and data-integrity testing.

## Stage 10 — modem and camera as separate projects

Create separate dossiers. Modem and camera cross firmware, secure services, IPC/media graphs and userspace; neither should block clean upstreaming of unrelated foundations.

## Stage 11 — upstream decomposition

Remove diagnostic hacks, rebase to an appropriate current tree, validate bindings/build/runtime, split by subsystem and dependency, and document limitations. Upstream code only after the behavior it describes was tested.

## Action card at every stage

| Field | Required |
|---|---|
| Goal | One observable boundary |
| Evidence/confidence | Exact ledger items |
| Files/subsystems | Precise surface |
| Dependencies | Hardware, providers, firmware, userspace |
| Test | Smallest one-variable experiment |
| Expected result | Named log/probe/interface |
| Failure recognition | What distinguishes failure classes |
| Risk/rollback | Boot, data and hardware recovery |
| Exit decision | advance, revise hypothesis, or stop for evidence |

