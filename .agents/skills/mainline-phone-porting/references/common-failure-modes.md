# Common mobile-mainlining failure modes

Use this as a hypothesis catalog, not a recipe. A listed cause is **Plausible** until target evidence connects it to the symptom.

## Boot and observability

| Symptom | Frequent causes to research | Evidence that separates them |
|---|---|---|
| Immediate reboot or returns to bootloader | image rejected, AVB/format/size mismatch, watchdog, early exception, wrong DTB | bootloader screen/log, image metadata, slot state, serial timing, known-good comparison |
| Permanent black screen | kernel never executed, console wrong, display absent, userspace stuck | serial/early console, USB enumeration, pstore, initramfs network, independent power/state signal |
| Kernel starts then hangs early | memory/reserved region, PSCI/GIC/timer, firmware handoff, invisible panic | last log, exception trace, memory/reserved-memory diff, bootloader-provided FDT |
| Boots only with keep-unused flags | missing clock/regulator/provider description or handoff dependency | provider/consumer graph and result after removing one diagnostic flag |
| Test seems unchanged | wrong slot/partition, bootloader selected another DTB/DTBO, stale artifact | build ID in kernel/DT, active slot, running FDT, image hashes |

A vendor splash remaining on screen is not proof that the display driver probed; it can be a bootloader framebuffer left untouched.

### ARM32-specific early failures

On older 32-bit ARM devices, research the bootloader-to-kernel ABI before changing drivers: raw kernel versus `zImage`, DTB versus ATAGS, r1 machine ID on non-DT-only platforms, r2 boot-data pointer, decompressor/load overlap, ARM/SVC/HYP entry state, appended DTB conventions and platform-specific SMP release. Do not assume ARM64 PSCI, `Image`, load placement or console conventions. See [arm32-mobile-bringup.md](arm32-mobile-bringup.md).

## Device tree and probe ordering

- Downstream bindings may share names with upstream while using different cell encodings or semantics.
- Vendor DTS may be preprocessed through several SoC, board, SKU and overlay layers. Study the shipped composite DT as well as source.
- Multiple DTBs may be selected by board ID, SoC revision, SKU, RAM size, panel ID or bootloader logic.
- EPROBE_DEFER usually means a required provider is not ready; the visible consumer is often not the first blocker.
- Dummy regulators, fixed clocks, always-on flags, clk_ignore_unused, regulator_ignore_unused and disabling IOMMU are diagnostic clues, not upstream fixes.
- A node marked okay still cannot probe without its parent bus, match data, Kconfig, firmware and providers.
- fw_devlink can expose dependency problems older/downstream kernels masked.

## Power, clocks, resets and interconnect

Mobile IP blocks often need multiple supplies/clocks in order, reset deassertion, power-domain attachment, bandwidth votes and IOMMU setup. Common faults are wrong supply phandles, absent parent clocks, mismatched indices, bootloader-left-on hardware hiding incomplete DT, and underdescribed OPP/thermal coupling.

Do not enable every regulator or mark domains always-on to force progress. If a keep-on change is used as a bounded diagnostic, label it temporary and test one dependency.

## Storage and root filesystem

- eMMC and UFS have distinct dependency paths; UFS commonly includes PHY, clocks, resets, regulators, interconnect and sometimes firmware.
- Reaching initramfs but not rootfs can be storage, filesystem, device-mapper, encryption, partition discovery, missing modules or userspace.
- Android dynamic partitions inside super are not normal GPT partitions.
- Inline encryption and vendor storage features can make downstream behavior misleading.
- Never write GPT, super, userdata, persist, EFS-like, modemst, calibration or bootloader partitions without explicit verified recovery planning and confirmation.

## Display

Trace: display controller → IOMMU/interconnect/power → PHY → host → graph endpoints → panel/bridge → backlight → userspace modeset.

Typical traps include variant-specific panels; embedded downstream command tables; wrong lane count/format/mode flags/DSC; panel identification blocked by bad reset/supplies; bootloader framebuffer mistaken for DRM; simple framebuffer takeover conflicts; deferred parent probes; backlight failure mistaken for panel failure; and a generic compatible selected because timings look similar.

Never invent panel init sequences or copy them between model names.

## Input, sensors and USB

Touch parts can change by SKU and require supplies, reset/IRQ polarity, pinctrl, firmware and coordinate transforms. An I2C address is not identity. Sensors may be behind a hub; an Android HAL name does not prove a directly attached chip.

For USB, separate controller, PHY, role switch, Type-C/PD controller, connector graph, VBUS and gadget/userspace. No host enumeration can mean no boot, missing gadget config, controller/PHY failure, wrong role or a power-only cable.

## Charging, battery and thermal

Charging is safety-sensitive. A percentage reading does not prove fuel-gauge calibration; VBUS detection does not prove safe charging. Verify charger, battery profile, thermistors, current/voltage limits, thermal zones and cutoffs. Never disable temperature checks, raise limits, or bypass protection to demonstrate support.

## Wi-Fi, Bluetooth, GNSS and NFC

Separate transport from radio operation. Common blockers are signed firmware, board/NVRAM/calibration, MAC provisioning, power sequence, regulators, clocks, UART wake lines, rfkill, coexistence and regulatory userspace. A family driver match does not prove the correct board file.

## Audio

ASoC can require CPU DAI, codec/amp, DSP/remoteproc, machine routing, topology firmware, UCM and userspace policy. Codec probe is not complete audio. Smart amplifiers can require calibration and protection; do not drive speakers from guessed configuration.

## Modem, camera and secure peripherals

Treat each as a separate project:

- Modem: secure firmware, remoteproc/MHI, shared memory, IPC, regulators, SIM and userspace protocol. Do not touch identity/calibration partitions.
- Camera: exact sensors, CSI PHY/lanes, supplies/clocks/GPIOs, ISP/media graph, firmware, calibration and userspace pipeline. Vendor HAL support does not directly translate to V4L2/libcamera.
- Fingerprint/NFC/security: a responding bus device may still depend on TEE/trustlets, secure elements or proprietary protocols.

## Suspend and daily-driver status

Boot is an early milestone. Suspend/resume, wake IRQs, cpuidle, cpufreq/devfreq, thermals, interconnect votes, regulator shutdown, remoteproc recovery and idle drain reveal missing dependencies later. “Display, touch and Wi-Fi work” is not “fully supported.”
