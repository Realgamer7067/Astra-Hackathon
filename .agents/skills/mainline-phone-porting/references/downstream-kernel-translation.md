# Translating Android/vendor kernels to mainline

The downstream tree is a hardware notebook and behavioral reference. It is not a patch queue that becomes mainline by resolving compiler errors.

## First establish lineage

Android device kernels can combine an Android Common Kernel, SoC-vendor BSP, OEM board changes, product overlays, external modules and binary firmware. Determine:

- base kernel release and Android common branch;
- SoC vendor branch/tag and OEM delta;
- exact firmware build the source release claims to match;
- whether Git history is real, flattened, squashed or imported;
- built-in versus external/vendor_dlkm/odm_dlkm modules;
- actual defconfig/config fragments and generated headers;
- missing proprietary source, firmware or build tools.

The running version string, source archive label and retail Android version may disagree. Keep that contradiction until ancestry or build metadata resolves it.

Official Android kernel sources are useful for ACK/GKI lineage: https://android.googlesource.com/kernel/common/ . For Samsung devices, model/build-specific source releases begin at https://opensource.samsung.com/ . Use each OEM’s official source portal when available.

## Extract intent, not syntax

For every downstream item ask:

1. What hardware block or board connection is described?
2. Which code actually consumes each property, ID or table?
3. Is the value physical, calculated, policy/tuning, firmware ABI, or workaround?
4. What is the current upstream subsystem abstraction?
5. Does an upstream binding/driver already represent it differently?
6. Which dependencies were assumed always-on or initialized by firmware?
7. Can behavior be validated independently on the target?

## Common translation traps

| Downstream pattern | Why mechanical copying fails | Research response |
|---|---|---|
| Vendor-prefixed DT properties | Upstream driver may not parse them or models behavior generically | Trace downstream consumer and current binding |
| Hardcoded register writes/tables | May duplicate firmware, clock, PHY or regmap framework | Identify hardware meaning and owning subsystem |
| Large monolithic driver | Mixes policy, HAL glue, power and several devices | Decompose by upstream subsystem and reusable IP |
| Board files plus DTS | Initialization may be split outside DT | Trace callbacks/platform data and generated config |
| Dummy supplies/fixed clocks | Hides real provider graph | Identify rail/clock from board evidence |
| Always-on/ignore-unused flags | Relies on bootloader state and prevents power correctness | Treat as diagnostics and find missing consumers |
| Disabled IOMMU/security | Avoids a dependency at cost of correctness/isolation | Port IOMMU/secure interface or declare blocker |
| Old Android APIs | Wakelocks, early-suspend, ION, vendor hooks and private PM APIs changed | Find current upstream PM/DMA-buf/subsystem design |
| Giant defconfig | Includes debug, unrelated boards and vendor frameworks | Derive minimal Kconfig from actual drivers |
| Panel/camera command arrays | Hardware/firmware-specific and often undocumented | Require lawful exact-part evidence; do not infer |
| Vendor sysfs/ioctl ABI | Often Android HAL policy rather than generic kernel ABI | Identify existing upstream userspace interface |

## Device-tree dialect comparison

Vendor source may build DTS through C preprocessor macros, generated headers, multiple includes and DTBO overlays. Reconstruct the effective target DT, then create:

| Downstream fact | Consumer source line | Physical/behavioral meaning | Current upstream representation | Confidence | Validation |
|---|---|---|---|---|---|

Numeric phandle arguments are ABI-specific. Clock, reset, interconnect, pin and power-domain numbers from downstream headers must not be transplanted into upstream DTS.

## Driver translation workflow

1. Find any current upstream driver for the exact or related IP.
2. Compare documented register/interface generations and integration dependencies.
3. Map only required missing capability.
4. Write/update a binding first when new hardware description is necessary.
5. Keep board wiring in DTS and reusable behavior in the subsystem driver.
6. Avoid copying vendor licensing-incompatible or provenance-unclear code.
7. Validate one capability on target and test existing upstream users for regression.

When no upstream abstraction exists, research maintainer expectations and comparable accepted drivers before designing one.

## Patch classification

| Classification | Treatment |
|---|---|
| Backport of upstream | Locate canonical upstream commit; do not re-port |
| Upstream behavior under new API | Recreate configuration using current API/binding |
| Useful hardware documentation | Cite as downstream evidence; reimplement cleanly |
| Small reusable capability | Isolate, document and validate for upstream driver |
| Vendor framework dependency | Map prerequisites or defer; do not stub success |
| Debug/bypass hack | Do not upstream; use only as declared bounded diagnostic |
| Unexplained or mismatched | Unknown; obtain provenance/evidence |

## Completion standard

Translation is complete only when the current upstream model describes the target hardware, all prerequisites are explicit, schema/build checks pass, exact-target behavior is observed, diagnostic hacks are removed, and the source/provenance story is suitable for review.

