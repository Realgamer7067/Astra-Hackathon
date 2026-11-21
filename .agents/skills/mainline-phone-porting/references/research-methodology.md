# Repeatable research methodology

The deliverable is not a pile of links. It is a versioned evidence model that identifies the earliest missing prerequisite and justifies one minimal next action.

## Phase 0 — define the question

Record:

- exact retail model, codename and variant if known;
- requested outcome: feasibility, first boot, one subsystem, patch review, distro integration or upstream submission;
- target kernel repository and commit, not merely “latest”;
- current working baseline and observed behavior;
- available device, source, firmware and log artifacts;
- permitted test boundary and recovery capability.

Split broad requests into claims. “Does this phone have mainline support?” becomes at least: SoC foundations, device DTS, bootability, storage, display/input, connectivity, power/thermal, suspend, modem/camera, userspace and upstream status.

For a narrow request, draw a scope boundary instead: include the requested subsystem, exact identity facts that can change it, its provider chain, boot/firmware/userspace dependencies, and its validation path. Mark unrelated device domains not applicable rather than researching them for completeness. Expand scope only when evidence exposes a transitive dependency.

## Phase 1 — freeze device identity and variants

Build an identity matrix before component research. Capture manufacturer model numbers, codenames, sales regions/carriers, PCB/board revisions, RAM/storage SKUs, SoC ID/revision/package, bootloader version, installed firmware build, launch Android, latest official Android and vendor kernel release.

Resolve identities through several namespaces:

- retail model and regulatory model;
- Android product/device/board/platform properties;
- bootloader board/product identifiers;
- vendor source repository/defconfig/DTS names;
- DT compatible/model and board-ID values;
- firmware package and OTA identifiers.

Do not merge rows when panel, touch, PMIC, charging, NFC, cameras, RF front-end, storage, boot chain or DTBO selection may differ.

## Phase 2 — acquire an artifact ladder

Prefer the least invasive evidence. Preserve original files and calculate hashes. Record acquisition method, date, firmware build and whether the artifact came from the target device or an external package.

1. Public upstream source, history, bindings and mailing-list discussion.
2. Official vendor GPL source and firmware documentation.
3. Read-only target information: complete logs, Android properties, kernel version/config, running FDT, module list, firmware request failures and partition metadata.
4. Shipped boot/vendor_boot/init_boot/dtbo images or official OTA packages.
5. Decoded DTB/DTBO, ramdisk manifests, module metadata and firmware manifests derived from those originals.
6. Reversible device tests after the research gate.

Ask for the smallest artifact that resolves a named uncertainty. Examples:

| Unknown | Smallest useful artifact |
|---|---|
| Exact running board compatible | NUL-separated strings from the running DT compatible property or the source DTB |
| Which panel variant is selected | Shipped composite DT/DTBO plus boot log, or a verified component identifier |
| Vendor kernel lineage | uname/version banner, config and official source branch/commit |
| Missing firmware | Complete firmware-loader/remoteproc log plus driver source revision |
| Which test image booted | Embedded build marker, image hash, active slot and running kernel version |

Do not ask for secrets, proprietary keys, unique modem identities or an entire personal data partition.

## Phase 3 — map upstream before downstream

For the exact target revision, inspect:

- arch/arm64/boot/dts and relevant SoC include hierarchy;
- Documentation/devicetree/bindings;
- driver match tables and probe paths;
- Kconfig/Makefile reachability;
- MAINTAINERS and recent path history;
- released upstream, linux-next, subsystem maintainer trees, lore and patchwork;
- reverted, rejected, superseded and RFC series.

Search both device and reusable block names:

~~~text
"<retail model>" "<codename>" "<board name>"
"<SoC>" dts OR clk OR pinctrl OR interconnect OR iommu
"<PMIC/part>" site:lore.kernel.org
"<compatible>" site:git.kernel.org
"<driver function/error text>" linux
~~~

Check dates and ancestry. A patch on lore may be obsolete, partially merged, superseded by a differently named series, or based on a non-upstream tree.

## Phase 4 — locate matching vendor evidence

Find the official kernel source release matching the Android/firmware generation where possible. Record repository, branch/tag, commit, toolchain/build notes, defconfig, DTS entry point and missing source. If the release is a tarball, hash it and create a local Git import for history-independent comparison; do not pretend it contains original history.

Trace vendor configuration across:

- SoC DTSI, board DTS/DTSI, SKU overlays and generated DTBO;
- defconfig/config fragments and built modules;
- drivers, headers, Kconfig/Makefile, board files and firmware paths;
- Android device trees, BoardConfig, proprietary manifests and init/fstab files;
- boot-image build rules.

Vendor DTS is evidence of the downstream ABI. Translate behavior and topology to current upstream bindings; do not copy syntax mechanically.

## Phase 5 — inspect ecosystem work

Use [ecosystem-and-projects.md](ecosystem-and-projects.md). For any apparent port, resolve exact kernel source/base, patch queue, device package and variant. Reproduce its claims from source or logs where possible.

## Phase 6 — build three ledgers

### Evidence ledger

| ID | Claim | Source/revision | What it proves | What it does not prove | Tier | Confidence |
|---|---|---|---|---|---|---|

### Contradiction ledger

| Claim | Source A | Source B | Likely reason | Resolving artifact/test | Current state |
|---|---|---|---|---|---|

Never pick the convenient source silently. Common causes are variant drift, stale wiki data, different firmware, downstream versus upstream semantics, and a patch stack not disclosed in a status page.

### Hypothesis ledger

| Hypothesis | Evidence for | Evidence against | Falsifier | Minimal safe test | Confidence |
|---|---|---|---|---|---|

A hypothesis without a falsifier is not ready to guide implementation.

## Phase 7 — create the dependency graph

For each feature, trace consumer to provider:

~~~text
userspace behavior
  → kernel subsystem/client driver
  → bus/transport and binding
  → clocks/resets/regulators/pinctrl/IRQ
  → power domain/interconnect/IOMMU/reserved memory
  → firmware/remote processor/secure monitor
  → bootloader handoff and board wiring
~~~

Mark each node present, missing, pending, downstream-only, firmware-only or unknown. The earliest missing prerequisite is the candidate next task.

## Phase 8 — score support precisely

Do not publish one vague percentage. Use a feature matrix with states such as:

- upstream in target release;
- upstream after target release;
- in linux-next;
- active reviewed series;
- community tree only;
- downstream-only;
- blocked by unknown hardware;
- blocked by missing framework/firmware/userspace;
- tested on exact target;
- untested.

Separate “code exists,” “binds,” “passes a minimal test,” “survives suspend/resume,” and “usable in a distribution.”

## Phase 9 — stop research at the right point

Research is ready for one action only when:

- target identity and relevant variant are established;
- the exact interface/binding/driver revision is known;
- prerequisites and boot/recovery boundary are mapped;
- contradictory evidence is resolved or explicitly bounded;
- the action changes one variable and has a useful negative result;
- failure can be observed and recovered.

Stop and request evidence when any safety-critical or board-specific value remains Unknown. Stop a search branch when it only produces mirrors, copied claims, unrelated SoC siblings or unversioned snippets.

## Convert research into an implementation card

Every proposed card contains:

| Field | Required content |
|---|---|
| Goal | One observable outcome |
| Evidence | Ledger IDs and exact source revisions |
| Change surface | Files, bindings, drivers and config |
| Dependencies | Required provider nodes, firmware and userspace |
| Assumptions | Only bounded Plausible claims |
| Risk | Data, boot, hardware and regression risk |
| Smallest test | One-variable experiment |
| Expected result | Exact log/probe/artifact behavior |
| Negative result value | What failure would rule in/out |
| Rollback | Verified recovery/restoration |
| Proof boundary | What success still does not establish |
