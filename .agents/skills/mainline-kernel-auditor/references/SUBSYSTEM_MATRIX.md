# Exhaustive kernel subsystem risk matrix

Use as a **prompt for analysis**, not a claim each property applies. Mark each item applicable / inapplicable / unknown with evidence. For substantial code, attach a row-specific finding or grouped invariants table.

| Area | Verify and try to falsify |
|---|---|
| Kernel version | API/callback signatures, lifecycle rules at pinned commit, upstream backport assumptions, Kconfig selection, duplicate definitions, compiler/linker behavior |
| DT and bindings | expected hardware, proper compatible/fallback, required properties and `additionalProperties`/`unevaluatedProperties`, address/size/interrupt cells, schema matching, disabled/enabled parent/children, label uniqueness, provider phandles, correct level SoC/board, stable DT ABI |
| Clocks / regulators / reset | physical wiring, rates, voltage and load constraints, enable/refcount symmetry, shared ownership, reset timings, bypass of constraints, speed bins, OPP, retention and boot-on semantics |
| Memory / DMA | reserved memory, secure carve-outs, DMA mask/limits, allocation lifetime, mapping/unmapping synchronization, coherent/noncoherent assumptions, IOMMU domains, `__iomem`/`__user`, alignment and endianness |
| Probe/defer/remove | absence/alternate revision, missing dependent supplier, correct `-EPROBE_DEFER`, error pointer checking, unwind order, devres/explicit lifetime consistency, `dev_set_drvdata`, no children before unsafe defer, rebind when supported |
| Concurrency | IRQ contexts, soft/hard threaded IRQ constraints, mutex/spinlock selection, lockdep order, state races, completion/timeout, workqueue cancellation and ordering, barriers and atomics with justification |
| PM/thermal | runtime PM reference management, system suspend/resume, wake IRQ, reset after resume, cold vs warm state, cpuidle/DVFS/thermal governor and policy separation, clocks/regulators off when not needed |
| Firmware / security | firmware identity/version/license, signed/verified boot chain where applicable, ownership of secure regions, bounds validation, device firmware loading failures, unsafe debug backdoor, userspace ioctl/sysfs/debugfs capability and permissions, unintended interface removal |
| Networking / Wi-Fi | kernel cfg80211/mac80211 vs vendor paths, MAC address provenance, fw loading, regulatory domain, rfkill, power save, WoWLAN if present, channel definitions, TX/RX queues and error recovery, AP/P2P functionality claimed |
| DRM/display | panel ID, component bind/unbind, clocks, lanes, timing, supplies, bridges, atomic helpers, framebuffer vs DRM ownership, modeset failures, suspend/resume, backlight polarity |
| Input | irq edge/level, GPIO reset, regulator timing, multitouch slot handling, axis transformations vs compositor rotation, wake gestures, firmware update integrity, unexpected `/dev/input` interfaces |
| Storage | eMMC/UFS bus capabilities/voltage transitions, tuning, cache flush/barriers, CQE, reset, power loss, wear-sensitive testing, DMA correctness |
| USB | host/device role switching, VBUS, extcon/type-C, PHY clock/reset, charger detection, wake, gadget interface exposure, current limits |
| GPU | hardware variant, clock/power/IOMMU, firmware/protected contexts, userspace DRM ABI, address isolation, devfreq, thermal, memory carve-outs |
| Audio/camera/modem | codec/card topology, clocks/routing, capture permissions, buffers/DMA, calibration, firmware and secure processing, privacy indicators where present, feature discovery and no invented support |
| User ABI | sysfs ABI and mode, proc/debugfs exposure, ioctl and netlink input validation, uevents, device enumeration, SELinux/LSM interaction, stable documented user-visible interface |
| Upstream architecture | generic mechanism vs board-specific data, no duplicative framework, no custom ABI for standard subsystem capability, no arbitrary delays or overrides, maintainers/subsystem rules, unit tests |
| Compatibility | other boards using same shared driver, default DT/binding rules, legacy compatibles, config matrix, module/built-in variants, bootloader differences, non-Android Linux userspace behavior |

## Anti-patterns worth deliberate searches

Search target files (using read-only `git grep` or equivalent) for `TODO`, `FIXME`, `HACK`, `XXX`, long `udelay/mdelay/msleep`, literal magic MMIO addresses, explicit register pokes to other drivers' regions, global mutable state for per-device settings, ignored return values, `WARN_ON` during expected failures, `BUG_ON`, `__force`, unexpected capability overrides, `of_machine_is_compatible` used to special-case board from shared driver, `regulator-always-on` without consumer rationale, `no-map` misconfiguration, permissive device node modes, `debugfs_create_*` storing secrets, power supply delays without spec, and force-enabled `status = "okay"`.

These are **search leads**, not automatically bugs; verify applicability and intent. Absence of these terms does not imply safety.
