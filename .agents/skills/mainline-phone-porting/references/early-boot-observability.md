# Early-boot observability and minimal initramfs

Observability is a dependency. Establish how a test will prove execution before adding broad hardware support. Never guess a UART address, GPIO, reserved-memory region, USB role or boot argument.

Primary references:

- Kernel command line/`earlycon`: https://docs.kernel.org/admin-guide/kernel-parameters.html
- Serial console: https://docs.kernel.org/admin-guide/serial-console.html
- Initramfs: https://docs.kernel.org/filesystems/ramfs-rootfs-initramfs.html
- Ramoops: https://docs.kernel.org/admin-guide/ramoops.html

## Evidence ladder

| Channel | Prerequisites | What success proves | Frequent trap |
|---|---|---|---|
| Build marker | exact kernel/image packaging | Observed output belongs to the candidate build | Marker hidden by stale slot/DT/image |
| Bootloader log | accessible documented console | Bootloader selected/accepted something | Does not prove kernel entry |
| Decompressor/early console | verified UART/driver and handoff | Kernel reached an early code region | Wrong address/options can be silent |
| Normal serial console | serial driver, clock/pinctrl/IRQ as required | Console driver initialized | Early and normal console are different |
| Pstore/ramoops | verified persistent reserved RAM | Kernel wrote a surviving record | Invented/overlapping region can corrupt memory |
| USB gadget | controller, PHY, role, UDC, cable and initramfs config | Kernel plus early userspace reached gadget setup | No USB can mean many earlier dependencies |
| Network/initramfs | NIC/USB transport, userspace and safe host link | Early userspace and transport work | Do not expose an unauthenticated shell to untrusted networks |
| Display/LED marker | already verified display/GPIO path | One bounded milestone | Bootloader splash or guessed GPIO is misleading/risky |

Use two independent channels when practical. A changing USB ID plus serial output is stronger than either alone.

## Build identity

- Record source commit, dirty snapshot, config and toolchain.
- Use an unmistakable kernel local version/build marker without changing hardware description.
- Record boot image, DTB/DTBO and initramfs hashes separately.
- Confirm the running `/proc/version`, `uname -a` or first boot log contains the marker.
- When a bootloader can select multiple DTBs/slots, add a reversible test marker only through a documented mechanism and verify the running FDT/image selection.

An unchanged screen is not proof the candidate did not execute. An old kernel banner proves the candidate was not the observed kernel, even if a flashing tool returned success.

## Early console research

`earlycon` without options can use a supported Device Tree `chosen/stdout-path`; explicit forms require the exact supported UART type, address and options. Establish all values from current kernel source, the exact bootloader-provided/running DT, vendor source and known-good logs. Do not copy an earlycon string from a sibling solely because the SoC family matches.

Separate:

- bootloader console;
- decompressor debug (`DEBUG_LL` or platform equivalent on some ARM32 trees);
- kernel early console;
- full serial driver console;
- userspace getty.

Capture from power-on with host timestamps and raw bytes. Record UART voltage/interface evidence before physical connection; do not trial unknown pads or voltage levels.

## Pstore/ramoops gate

Ramoops writes into a predefined persistent RAM area. Enable it only when address, size, alignment, ownership and non-overlap are Verified from shipped DT/reserved-memory, bootloader/vendor source or a tested platform allocation. Preserve existing pstore records before a test and distinguish old from new records with the build marker/time sequence.

Do not carve out a plausible-looking address, borrow another device’s region, or use pstore/blk on an arbitrary partition. If no verified region exists, select another observation channel.

## Minimal initramfs design

An initramfs is a `newc` cpio root filesystem whose `/init` becomes PID 1. It may be embedded with `CONFIG_INITRAMFS_SOURCE` or supplied externally when the boot format supports it.

Keep the first image minimal and auditable:

- a statically linked, architecture-correct BusyBox/klibc-style userspace or known equivalent;
- `/init` with explicit error handling and a visible build marker;
- `/dev/console` plus `/proc`, `/sys`, `/dev` setup appropriate to the kernel;
- only modules and firmware needed for the chosen observation/recovery channel;
- a local console shell or a narrowly configured host-only USB/network channel;
- no automatic writes to internal storage, partition repair, formatting or mount-with-recovery behavior.

Validate the archive before packing: list entries/order, confirm `/init` executable ownership/mode, inspect ELF architecture/static dependencies, record compression and hash, and unpack it into a temporary directory to verify contents. Match the boot image’s expected ramdisk compression and header generation.

## Minimal `/init` milestones

Design PID 1 to emit and flush one marker after each independently useful step:

1. `/init` executed.
2. proc/sysfs/devtmpfs available.
3. console or selected transport available.
4. relevant device node/provider visible.
5. optional real-root discovery, kept read-only initially.

If a step fails, keep the prior channel alive and collect the exact return code/log. Do not add storage, display, networking and charging simultaneously.

## Failure interpretation

| Observation | Supported conclusion | Still unknown |
|---|---|---|
| No channel responds | Chosen channels produced no evidence | Image rejection, kernel entry, console config and hardware state |
| Early console stops at one line | Kernel reached that logged point | Whether the next subsystem or logging itself failed |
| Init marker appears | Kernel unpacked initramfs and executed PID 1 | Storage/rootfs and most peripherals |
| USB gadget enumerates | UDC/PHY/config and early userspace reached setup | Host mode, charging and full USB policy |
| New pstore record has marker | Candidate kernel wrote that record | Cause beyond the captured window |

## Observability readiness

~~~text
- Candidate build/image identity: verified / incomplete / unknown
- Selected channel and full dependency chain: verified / incomplete / unknown
- Console/region/address values: verified / incomplete / not applicable
- Minimal initramfs locally inspected: yes / no / not applicable
- Recovery channel remains available: yes / no
- Expected marker and failure boundary defined: yes / no
- Recommendation confidence: verified / strongly supported / plausible / unknown
~~~
