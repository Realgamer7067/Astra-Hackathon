# Hardware inventory and subsystem mapping

Inventory physical components, SoC-integrated blocks, board topology, firmware ownership and Linux support separately. Never fill blanks from a similar phone.

## Inventory row schema

| Field | Requirement |
|---|---|
| Function/component | Exact part/revision if verified; alternatives remain separate rows |
| Presence state | Confirmed physical, confirmed SoC-integrated, inferred, conflicting, unknown |
| Variant scope | Model/region/PCB/RAM-storage/firmware/DTBO selector |
| Bus/topology | I2C/SPI/UART/SLIMbus/SoundWire/DSI/CSI/PCIe/SDIO/UFS/etc. |
| Address/IRQ/GPIO | Record only from target evidence; include controller and flags |
| Supplies/clocks/resets | Named providers and indices with evidence |
| Linux subsystem | Driver area, Kconfig, binding, maintainers |
| Upstream state | Release/commit/next/series/community/downstream/absent |
| Vendor implementation | Exact repository/path/revision |
| Firmware/userspace | Files, remoteproc, calibration, HAL replacement/userspace |
| Evidence | Ledger IDs and confidence |
| Earliest blocker | First missing prerequisite |
| Validation | Smallest read-only or reversible test |

## Core platform foundations

Inventory before peripherals:

| Area | Required facts |
|---|---|
| CPU/platform | architecture, SoC/revision/package, PSCI/conduit, CPU topology, errata |
| Interrupt/time | GIC revision, interrupt parents, architected/platform timers |
| Memory | physical ranges, usable RAM, reserved-memory/carveouts, CMA, secure/firmware regions |
| Console | UART block, pins, clock, address, bootloader ownership, accessible transport |
| System control | syscon/PMU, reset, reboot/poweroff, watchdog |
| Providers | clocks, regulators, GPIO/pinctrl, resets, power domains, interconnect, IOMMU |
| Storage | eMMC/UFS/NVMe controller, PHY, supplies, boot/rootfs constraints |
| Thermal/performance | sensors, cooling, OPP, cpufreq/devfreq, regulators, trip policies |

If core providers are incomplete, peripheral rows must show those dependencies as blockers rather than being called independently unsupported.

## Board component checklist

| Group | Components/questions |
|---|---|
| Power | PMIC(s), sub-PMIC, charger, Type-C/PD, fuel gauge, battery profile, thermistors, wireless charging |
| Display | display engine, IOMMU, PHY, DSI/eDP bridge, exact panel, DSC, backlight, TE/reset |
| Input | touchscreen, buttons, keyboard/pen, hall sensor, haptics |
| Audio | SoC audio/DSP, codec, smart amps, microphones, jack/USB audio, routing/topology |
| Connectivity | Wi-Fi, Bluetooth, modem, GNSS, NFC, UWB, FM, antennas/coexistence |
| Sensors | accelerometer, gyro, magnetometer, proximity/light, pressure, sensor hub |
| Cameras | each sensor, EEPROM/calibration, actuator, flash, CSI lanes/PHY, ISP |
| Security | fingerprint, secure element, TEE-mediated peripherals |
| Indicators | notification LEDs, RGB/controller, vibrator/haptics |
| Expansion | USB roles, Type-C alt modes, microSD, dock/pogo accessories |

## Evidence discovery by artifact

| Artifact | Useful clues | Limits |
|---|---|---|
| Running FDT / shipped DTB/DTBO | compatibles, topology, providers, SKU overlays | downstream ABI; can include disabled/incorrect nodes |
| Vendor kernel source | drivers, properties, configs, firmware names | may mismatch firmware; history may be absent |
| Android properties and logs | board/platform/product/firmware and probe results | aliases and userspace naming can mislead |
| Kernel modules | aliases, firmware requests, driver coverage | module presence does not prove hardware or load |
| Firmware/vendor manifests | blob names, HALs, services | proprietary name does not identify physical topology |
| Teardown/chip markings | physical part and board revision | not always same regional SKU; routing remains unknown |
| Public datasheet/schematic | exact electrical requirements/topology | confirm document applies to exact revision |

## Support-state matrix

For each component, separate:

| Layer | State |
|---|---|
| Binding | accepted / pending / downstream-only / absent / unknown |
| Provider drivers | complete / partial / blocked / unknown |
| Function driver | accepted / pending / fork / downstream-only / absent |
| DTS | exact device upstream / community / downstream / absent |
| Firmware | available / signed-coupled / redistribution-limited / missing / unknown |
| Userspace | available/configured / special integration / absent / unknown |
| Runtime | exact target tested / sibling only / untested / failing |

“Supported” is allowed only with the intended layer and test named.

## Variant-control rules

- Keep alternative panel/touch/camera/storage rows until a selector or physical identifier resolves them.
- Do not use a single model number to collapse carrier/region PCB differences.
- Record board-ID/DTBO conditions and source include paths.
- Treat RAM/storage capacity as potentially relevant to memory carveouts and bootloader DT selection, not proof of different wiring.
- When two sources disagree, create a contradiction row instead of choosing.

