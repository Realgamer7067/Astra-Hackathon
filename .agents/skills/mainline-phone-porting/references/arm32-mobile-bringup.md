# 32-bit ARM mobile bring-up

Treat ARM32 as a distinct boot and build path, not a smaller ARM64 target. This is common on older Android phones/tablets and some vendor kernels.

Primary reference: https://docs.kernel.org/arch/arm/booting.html

## Establish the boot ABI

| Question | Evidence | Why it matters |
|---|---|---|
| CPU/SoC architecture | SoC manual, vendor config, ELF headers | `ARCH=arm`, ISA and toolchain selection |
| Kernel artifact | boot-image extraction and vendor build rules | raw Image, `zImage`, `uImage`, appended-DTB or vendor target are different |
| DT or ATAGS | bootloader/vendor source, known-good boot data | r2 points to DTB or tagged list; do not assume DT-only |
| Machine ID | platform state and ARM mach code | r1 matters for non-DT-only machines; DT-only convention differs |
| Entry state | bootloader/secure monitor source or tested logs | r0/r1/r2, interrupts, ARM/Thumb and SVC/HYP requirements |
| Load/decompression layout | bootloader source, image metadata, RAM map | compressed kernel, DTB and initramfs must not overwrite one another |
| SMP enable path | upstream/vendor platform code and DT | PSCI, holding pen, secure monitor or platform `smp_operations` may differ |

The documented ARM32 entry contract includes r0=0, r1 machine type, and r2 pointing to ATAGS or DTB; DT-only platforms can use the DT machine identification convention. The bootloader must provide initialized RAM and place boot data/initramfs outside decompressor overwrite regions. Do not convert these documented general rules into target addresses without exact board evidence.

## Build branch

Inspect `arch/arm/Makefile`, the platform Kconfig/Makefiles and vendor build scripts before choosing targets.

~~~bash
make -C <tree> O=<fresh-outside-tree-output> ARCH=arm \
  CROSS_COMPILE=<verified-arm-prefix> <verified-defconfig>
make -C <tree> O=<fresh-outside-tree-output> ARCH=arm \
  CROSS_COMPILE=<verified-arm-prefix> -j<N> zImage <verified-dtb-target>
~~~

LLVM can instead be valid when supported by the exact branch:

~~~bash
make -C <tree> O=<fresh-outside-tree-output> ARCH=arm LLVM=1 <verified-defconfig>
make -C <tree> O=<fresh-outside-tree-output> ARCH=arm LLVM=1 -j<N> zImage dtbs
~~~

These are command shapes, not target claims. Some trees require a raw Image, `uImage` plus a verified `LOADADDR`, `zImage-dtb`, a concatenated DTB, a vendor boot wrapper, or legacy Android toolchains. Never invent `LOADADDR`, machine ID, appended-DTB order or boot-image offsets.

Use `build-kernel-artifacts.sh --arch arm --target <verified-target>` so `zImage`, modules and other new/changed outputs enter the evidence hashes.

## Configuration and platform research

- Identify `CONFIG_ARCH_*`, `CONFIG_MACH_*`, multiplatform status and exact defconfig lineage.
- Determine whether the platform is DT-only or retains board files/machine descriptors.
- Trace GIC/timer, cache controller, outer-cache/L2, DMA/coherency and memory-zone assumptions.
- Check LPAE/highmem, RAM bank layout and reserved regions against the bootloader-provided data.
- Trace SMP release and hotplug through DT `enable-method`, PSCI, secure firmware or platform code.
- Check vendor decompressor/debug code separately from the normal serial driver.
- Treat a downstream `zImage-dtb` rule as packaging evidence, not an upstream ABI.

## Early observability

Normal console, `earlycon`, decompressor debug and vendor `DEBUG_LL` paths are distinct. Select only a console driver/address proven for this SoC and boot path. An incorrect early debug configuration can be silent or touch the wrong MMIO block. Read [early-boot-observability.md](early-boot-observability.md).

## Frequent ARM32 traps

- Building `Image` because ARM64 instructions were copied.
- Correct kernel code packaged in the wrong legacy boot-image/appended-DTB form.
- Wrong r1/r2 contract, ATAGS/DT distinction or entry CPU mode.
- `zImage`, DTB and initramfs overlap during decompression.
- Reusing another board’s machine ID or `LOADADDR`.
- Boot CPU starts but secondaries need a platform/secure-monitor release path, not PSCI.
- Vendor GCC-era warnings/errors differ under modern Clang; a compile fix is not hardware support.
- A 32-bit userspace/kernel ABI assumption is confused with the SoC’s physical capabilities.

## ARM32 readiness

~~~text
- Exact CPU/SoC and ARCH: verified / incomplete / unknown
- Artifact and packaging form: verified / incomplete / unknown
- DT versus ATAGS and r1/r2 contract: verified / incomplete / unknown
- Entry state and load/decompression layout: verified / incomplete / unknown
- SMP/secure-firmware path: verified / incomplete / unknown / not applicable
- Config/toolchain provenance: verified / incomplete
- Early observation and recovery path: yes / no
- Recommendation confidence: verified / strongly supported / plausible / unknown
~~~
