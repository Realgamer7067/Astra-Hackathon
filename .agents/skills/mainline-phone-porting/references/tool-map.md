# General tool map

Choose tools after identifying the evidence question and source generation. Record tool version, origin and exact command in the dossier. Prefer tools shipped by the relevant upstream project or official Android Platform Tools over repackaged binaries from unknown sites.

## Research and source history

| Need | Tools | Notes |
|---|---|---|
| Fast source search | ripgrep, git grep | Search compatibles, symbols, error strings, codenames and component aliases |
| History/lineage | git log/show/blame/range-diff/patch-id, b4 | Search all relevant refs; inspect lore series and parents |
| Patch recipients | scripts/get_maintainer.pl, MAINTAINERS | Current target tree is authoritative |
| Source browsing | git.kernel.org, lore.kernel.org, kernel source, Android Gitiles | Search engines provide leads only |
| Reproducible index | scripts/index-kernel-evidence.py | Records HEAD, shallow/dirty state and capped matches |

## Kernel and module builds

| Build family | Typical tools | Use when |
|---|---|---|
| Upstream Kbuild | make, GCC/binutils or Clang/LLVM, ccache/sccache | Mainline and mainline-oriented trees |
| Android Kleaf | repo, Bazel via tools/bazel | Branch defines Kleaf targets/build files |
| Legacy Android build | repo, build/build.sh plus BUILD_CONFIG | Only branches that actually provide/support it |
| postmarketOS | pmbootstrap, abuild/pmaports | Reproducible distro package and image integration |
| External module | Kbuild with make -C tree M=module | Driver experiment against a prepared matching tree |

Common build dependencies include make, bc, bison, flex, perl, Python, OpenSSL development files, libelf/elfutils, pahole for BTF, cpio, rsync, compression tools, dtc/dtschema and the selected cross toolchain. Determine exact packages from the tree/build documentation; do not paste one distro’s package line universally.

## Device tree

| Tool | Role | Evidence boundary |
|---|---|---|
| Kernel Kbuild | Preprocesses and builds in-tree DTB/DTBO correctly | Preferred over invoking dtc directly |
| dtc | Compile/decompile FDT | Decompiled output loses source structure/comments/labels |
| fdtdump | Low-level FDT inspection | Diagnostic output, not canonical source |
| fdtget | Read exact properties safely | Interpret cells with the binding |
| fdtput | Mutates a blob | Avoid for source-controlled work; never use to invent values |
| fdtoverlay | Apply overlays offline | Success proves structural application only |
| dtdiff | Compare trees where available | Normalize provenance before interpreting |
| dtschema/yamllint | Binding and DT validation | Schema validity is not board correctness |
| mkdtimg | Build/dump Android DT table images | IDs, revision, order and page size are bootloader ABI |

## Android images and partitions

| Need | Tools | Caution |
|---|---|---|
| Boot image inspect/repack | AOSP unpack_bootimg/mkbootimg | Preserve exact header generation and parameters |
| DT table inspect/build | AOSP mkdtimg | Container differs from a raw DTB/DTBO |
| AVB inspect/sign | AOSP avbtool | Signing keys, descriptors, rollback and partition size are device policy |
| Sparse conversion | simg2img/img2simg | Sparse versus raw is a file encoding distinction |
| Dynamic partitions | lpdump/lpunpack/lpmake/lpadd | super metadata and slot/group sizing are sensitive |
| OTA payloads | official payload tooling for the matching generation | Preserve source build and hashes |
| Compression | gzip, lz4, xz, zstd as identified | Compression format and legacy headers can be bootloader-specific |

Community utilities such as magiskboot, abootimg, payload dumpers and OEM-specific unpackers can be useful when official tools do not support an older/vendor format. Record their repository and revision; cross-check output with known-good metadata.

## Device communication, logging and inspection

- adb and logcat for authorized Android-side shell/log collection.
- fastboot getvar and device listing for supported bootloader metadata.
- lsusb/usbmon/Wireshark for host USB enumeration/protocol evidence.
- picocom, minicom, tio or screen for an already identified serial console.
- dmesg, dynamic debug, ftrace/trace-cmd, debugfs and pstore when justified.
- modinfo, readelf, nm, objdump and strings for binary/module clues; strings are leads.
- file, sha256sum, cmp and hexdump/xxd for artifact identity.

Do not use devmem, arbitrary register pokes, JTAG, UART voltage experiments, unknown EDL/Download Agents or boot-ROM exploit tools as routine diagnostics. They require separate hardware/security authorization and exact electrical/device evidence.

## Runtime subsystem tools

Use these after the kernel has booted far enough to gather evidence. Availability depends on the root filesystem and kernel config.

| Area | Common read-mostly tools/interfaces | Main caution |
|---|---|---|
| Kernel/logging | dmesg, journalctl, pstore/ramoops, dynamic debug, trace-cmd/ftrace, perf | Record timestamps and exact kernel build; tracing can alter timing |
| Probe/dependency state | /sys/bus/*/devices, /sys/kernel/debug/devices_deferred, driver bind links, modalias, udevadm | Manual bind/unbind is an experiment, not a persistent fix |
| Clocks/power | clk_summary, regulator_summary, genpd/runtime-PM debugfs, cpupower, devfreq sysfs | Debugfs names vary and are not ABI; never force unsafe voltage/current |
| GPIO/pinctrl | gpioinfo/gpioget from libgpiod, pinctrl debugfs | GPIO line names/numbers can change; setting a line may conflict with a driver |
| I2C/SPI | adapter/device sysfs, i2cdetect/i2cget only when chip behavior is known, logic traces when authorized | Probing arbitrary addresses can have side effects; address is not identity |
| DRM/display | modetest, drm_info, /sys/kernel/debug/dri, connector status and EDID where present | A lit bootloader framebuffer is not DRM probe; avoid unverified panel modes |
| Input | evtest, libinput debug-events, /proc/bus/input/devices | Coordinate transforms and wake behavior require separate validation |
| USB/Type-C | lsusb, lsusb -t, usb-devices, usbmon, Type-C/role-switch sysfs | Enumeration separates host/cable evidence from controller/PHY evidence |
| Storage | lsblk, blkid, findmnt, udevadm; mmc-utils/ufs-utils read-only queries when supported | Do not issue sanitize, format, RPMB, provisioning or destructive health commands |
| Audio | /proc/asound, alsa-info, amixer, aplay/arecord, tinyalsa tools on Android | Start muted/low-risk; smart amps and speakers need verified calibration/protection |
| Wi-Fi/BT | rfkill, iw, wpa_cli, bluetoothctl, btmon | Transport-up is not calibrated/regulatory-correct radio operation |
| Thermal/suspend | thermal sysfs, turbostat where applicable, rtcwake, wakeup_sources, suspend_stats | Validate temperatures and wake sources; do not bypass thermal policy |
| Media/camera | media-ctl, v4l2-ctl, yavta/libcamera tools | Sensor streaming needs exact power/clock/CSI and calibration evidence |
| Modem/remote processors | remoteproc sysfs/debugfs, rpmsg/QRTR traces, ModemManager/mmcli where supported | Preserve identity/calibration; firmware boot is not functional telephony |

Prefer source-level fixes and repeatable scripts over one-off sysfs/debugfs writes. If a write is needed as a diagnostic, document the original value, one changed variable, duration, expected evidence and rollback.

## Code-quality and binary-analysis tools

| Need | Tools | Boundary |
|---|---|---|
| Kernel patch style | scripts/checkpatch.pl | Style hints are not correctness proof |
| Static analysis | sparse, smatch, Coccinelle/coccicheck, compiler W= levels | Pin tool versions and separate new warnings from baseline |
| ABI/symbols | nm, readelf, objdump, modinfo, depmod, scripts/mod/modpost | A symbol name does not prove compatible semantics |
| Size/layout | size, pahole, bloat-o-meter, scripts/checkstack.pl | Debug/config differences can dominate comparisons |
| Reproducibility | diffoscope, cmp, sha256sum, SOURCE_DATE_EPOCH where supported | Different bytes require explanation; equal bytes do not prove runtime support |

## Flash and recovery families

Use [flashing-tools.md](flashing-tools.md). adb is not a raw flashing protocol. Bootloader fastboot and userspace fastbootd are different modes. Samsung Download Mode, Qualcomm EDL, MediaTek BootROM/preloader, Unisoc FDL, Rockchip loader/maskrom and Allwinner FEL are unrelated protocols with different trust and recovery boundaries.

## Tool acceptance checklist

Before relying on a tool:

- verify authoritative project/source and version;
- capture its help/version output;
- confirm it supports the exact image/protocol generation;
- test read-only inspection against a known-good artifact;
- compare unpack→repack metadata before using output;
- preserve original images and hashes;
- declare what the tool output cannot prove.
