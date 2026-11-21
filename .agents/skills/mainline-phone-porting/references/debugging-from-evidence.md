# Debugging from evidence

Debugging should reduce uncertainty. Do not respond to a symptom with a catalog of guesses or a large DTS rewrite.

## Preserve the experiment

Record:

- exact kernel commit/config/toolchain;
- exact DTB/DTBO and boot image hashes;
- device model/revision/firmware and active slot;
- command line and bootloader handoff;
- complete unfiltered log with timestamps;
- baseline result;
- single intended change;
- test conditions and userspace/initramfs;
- recovery outcome.

Add an unmistakable build marker so a stale/wrong-slot boot cannot impersonate the test.

## Find the earliest divergence

Compare good versus bad logs from the beginning, not only the final error. The earliest changed provider message often causes many downstream failures.

Classify the boundary:

| Boundary | Questions |
|---|---|
| Image accepted? | Did bootloader parse/verify/select it? |
| Kernel executed? | Any early console, USB/state, watchdog timing or retained log? |
| Correct DT? | Build marker, model/compatible, chosen and expected overlay? |
| Core platform alive? | CPU, GIC, timer, memory, initramfs? |
| Parent enumerated? | Bus/controller/remoteproc present? |
| Driver matched? | compatible/modalias/Kconfig/module? |
| Probe completed? | success, errno, defer, timeout, missing firmware? |
| Subsystem registered? | DRM/input/net/sound/power/media object? |
| Userspace configured? | service, permissions, policy, firmware/UCM/libcamera/etc.? |
| Survives PM? | runtime suspend, system suspend, reset/recovery? |

## Read errors in source context

Locate the exact printk/dev_err string in the target source revision. Read surrounding control flow and return value. Trace whether the message is primary, a cleanup consequence, or a generic wrapper. If EPROBE_DEFER is involved, inspect deferred devices and the missing supplier; do not “fix” the consumer.

Kernel driver-model documentation describes EPROBE_DEFER as a dependency-not-ready signal: https://docs.kernel.org/driver-api/driver-model/driver.html

## Rank competing hypotheses

Use:

| Hypothesis | Evidence for | Evidence against | Expected observation if true | Smallest differentiating test | Confidence |
|---|---|---|---|---|---|

Choose a test with a useful negative result. Changing five DTS properties and obtaining a boot provides little causal evidence.

## Typical diagnostic traps

- grep-filtered logs remove the prerequisite error;
- increased log level changes timing;
- retained bootloader framebuffer is mistaken for DRM;
- wrong image/slot/overlay is tested;
- a module exists but is absent from initramfs;
- vendor driver emits same string with different semantics;
- missing firmware is blamed before driver/board match is proven;
- ignore-unused flags conceal incomplete power descriptions;
- userspace failure is misclassified as kernel failure;
- success on one reboot is called stable.

## Symptom-specific starting points

### No visible output

Separate image rejection, no kernel execution, wrong console, early crash, framebuffer handoff and DRM/userspace. Obtain an independent boot signal before panel edits.

### Repeated deferred probes

Find the lowest unresolved supplier in device links/DT graph. Verify its node, driver, Kconfig, parent and its own dependencies.

### Display never probes

Build a component matrix:

| Component | Node enabled | Driver matched | Probe result | Missing provider | Evidence |
|---|---|---|---|---|---|
| DPU/display engine |  |  |  |  |  |
| IOMMU/interconnect/power |  |  |  |  |  |
| DSI/eDP PHY |  |  |  |  |  |
| host/bridge |  |  |  |  |  |
| panel |  |  |  |  |  |
| backlight |  |  |  |  |  |

Only propose a DTS edit after the failing edge and exact target value are supported.

### Boots but hardware is unstable

Study runtime PM, clocks/regulators after late init, thermal throttling, IOMMU faults, remoteproc crashes and suspend/resume. Bootloader-left-on state often explains first-use or warm-boot-only success.

## Report the result honestly

State observation, supported conclusion, non-conclusion, updated confidence and next discriminating test. If evidence cannot distinguish hypotheses, say Unknown.

