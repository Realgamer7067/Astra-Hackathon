# Device research dossier — reusable template

## Goal and scope

Use this full template for whole-device feasibility/landscape work. For a single subsystem, retain only the identity, evidence, dependencies, readiness and validation sections material to that subsystem; mark unrelated areas not applicable.

- Device:
- Exact model/codename/variant:
- Firmware/bootloader build:
- Target kernel repository + full commit:
- Requested outcome:
- Available artifacts:
- Allowed test boundary:
- Dossier date:

## Executive assessment

Summarize feasibility without collapsing layers. State the earliest missing prerequisite, recommendation confidence and why. Distinguish boots, mainline code presence, exact-target testing, distro usability and upstream acceptance.

## 1. Identity and variants

| Fact | Value | Source/revision | Proves / does not prove | Confidence | Variant impact |
|---|---|---|---|---|---|
| Manufacturer/product/codename |  |  |  |  |  |
| Regional/carrier models |  |  |  |  |  |
| Board/PCB/SKU identifiers |  |  |  |  |  |
| SoC/revision/package |  |  |  |  |  |
| RAM/storage variants |  |  |  |  |  |
| Launch/latest Android |  |  |  |  |  |
| Vendor kernel release/branch |  |  |  |  |  |
| Bootloader/AVB/slots/image format |  |  |  |  |  |
| Known recovery path |  |  |  |  |  |

### Variant contradiction ledger

| Claim | Source A | Source B | Likely explanation | Resolving artifact | State |
|---|---|---|---|---|---|

## 2. Source and artifact ledger

| ID | URL/repo/path/artifact | Branch/commit/build/hash | Tier/state | What it proves | What it does not prove | Current? |
|---|---|---|---|---|---|---|

Include upstream Linux, linux-next, subsystem trees, lore, bindings, vendor sources, official firmware, target logs/images and ecosystem ports.

## 3. Hardware inventory

| Function/component | Presence/variant | Bus/topology | Providers | Upstream binding/driver/Kconfig | Vendor path | Firmware/userspace | Evidence IDs | Confidence | Earliest blocker | Validation |
|---|---|---|---|---|---|---|---|---|---|---|
| SoC/core/interrupt/timer |  |  |  |  |  |  |  |  |  |  |
| PMIC/regulators/power domains |  |  |  |  |  |  |  |  |  |  |
| Memory/reserved memory |  |  |  |  |  |  |  |  |  |  |
| eMMC/UFS/storage |  |  |  |  |  |  |  |  |  |  |
| USB/Type-C/charger/fuel gauge |  |  |  |  |  |  |  |  |  |  |
| Display/panel/backlight |  |  |  |  |  |  |  |  |  |  |
| Touch/input/haptics/LED |  |  |  |  |  |  |  |  |  |  |
| Audio codec/amps/DSP |  |  |  |  |  |  |  |  |  |  |
| Wi-Fi/Bluetooth |  |  |  |  |  |  |  |  |  |  |
| Sensors/hub |  |  |  |  |  |  |  |  |  |  |
| Modem/GNSS |  |  |  |  |  |  |  |  |  |  |
| Cameras/ISP |  |  |  |  |  |  |  |  |  |  |
| NFC/fingerprint/security |  |  |  |  |  |  |  |  |  |  |
| Thermal/cpufreq/devfreq/suspend |  |  |  |  |  |  |  |  |  |  |

Keep confirmed and inferred components explicitly separate.

## 4. Upstream landscape

| Layer | Target release | Newer upstream | linux-next | Active/recent lore | Community tree | Exact target tested? |
|---|---|---|---|---|---|---|
| SoC foundation |  |  |  |  |  |  |
| Providers |  |  |  |  |  |  |
| Board DTS |  |  |  |  |  |  |
| Storage/USB |  |  |  |  |  |  |
| Display/input |  |  |  |  |  |  |
| Power/audio/radios |  |  |  |  |  |  |

List maintainers, relevant trees and rejected/superseded designs.

## 5. Vendor/downstream archaeology

- Matching official source and firmware generation:
- DTS/DTSI/DTBO include path:
- defconfig/config fragments:
- relevant driver/firmware/module locations:
- source-release gaps:

| Downstream item | Behavior/fact extracted | Upstream relation | Hidden dependencies | Classification | Evidence |
|---|---|---|---|---|---|

Classify: upstream; represented differently; applicable incomplete; vendor-infrastructure-dependent; unsuitable hack; documentation-only; superseded; wrong variant; unknown.

## 6. Ecosystem ports

| Project | Device/package path + revision | Kernel base/source | Patch delta | Variant | Feature evidence | Limit/staleness |
|---|---|---|---|---|---|---|
| postmarketOS/pmaports |  |  |  |  |  |  |
| LineageOS |  |  |  |  |  |  |
| Droidian/Mobian/UBports/other |  |  |  |  |  |  |

## 7. Sibling comparison

| Sibling | Feature | Shared dependency + proof | Material difference | Reusable concept | Non-transferable values | Confidence |
|---|---|---|---|---|---|---|

## 8. Dependency graph and blockers

| Desired feature | Complete dependency chain | Present upstream | Missing/pending/unknown | Earliest blocker | Safe test |
|---|---|---|---|---|---|

## 9. Support matrix

Use exact states, not a percentage:

| Feature | Code state | Exact-target runtime state | Firmware/userspace state | Confidence | Evidence | Blocker |
|---|---|---|---|---|---|---|

## 10. Hypotheses

| Hypothesis | For | Against | Falsifier | Minimal experiment | Confidence |
|---|---|---|---|---|---|

## 11. Research readiness

- Device identity: verified / incomplete / unknown
- Hardware inventory: verified / incomplete / unknown
- Relevant upstream support mapped: yes / no / not applicable
- linux-next and active/recent lore checked: yes / no / not applicable
- Vendor-tree and shipped-artifact evidence analysed: yes / no / unavailable / not applicable
- Ecosystem ports inspected at source level: yes / no / not found / not applicable
- Sibling-device comparison justified: yes / no / not applicable
- Hardware and software dependencies mapped: yes / no / not applicable
- Boot/recovery boundary verified: yes / no / not applicable
- Safe validation method available: yes / no / not applicable
- Recommendation confidence: verified / strongly supported / plausible / unknown

## 12. Smallest justified next step

- Goal:
- Evidence IDs:
- Exact files/subsystems:
- Dependencies:
- Assumptions:
- Risk:
- Smallest test:
- Expected log/result:
- Failure recognition:
- Rollback/recovery:
- What success will not prove:

## 13. Research backlog

| Priority | Unknown | Why it blocks progress | Smallest artifact/search/test | Owner/source |
|---|---|---|---|---|
