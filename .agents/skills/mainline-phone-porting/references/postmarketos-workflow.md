# postmarketOS and pmbootstrap workflow

pmbootstrap can build packages/rootfs/initramfs, export artifacts and wrap several flashing backends. It does not independently prove deviceinfo partition values or a port’s mainline status.

Primary references:

- pmbootstrap usage: https://docs.postmarketos.org/pmbootstrap/main/usage.html
- deviceinfo reference: https://docs.postmarketos.org/pmaports/main/deviceinfo-reference.html
- pmaports: https://gitlab.postmarketos.org/postmarketOS/pmaports
- porting guide: https://wiki.postmarketos.org/wiki/Porting_to_a_new_device

## Freeze the environment

Record pmbootstrap version/commit, pmaports remote/branch/commit/dirty diff, selected channel/device/kernel/UI, host distribution, work/output paths and package checksums. A pmaports branch may change while the kernel source remains pinned.

## Source-level inspection first

For a device inspect:

- device package APKBUILD and deviceinfo;
- kernel package APKBUILD, source URL/commit, config and patch list;
- firmware packages and licenses;
- initramfs hooks, boot image generation and flash method fields;
- shared SoC kernel package and patches outside the device directory;
- commit/MR history and device wiki discrepancies.

Run deviceinfo parsing/validation from the currently installed pmbootstrap version. Never infer a flash partition from the retail name.

## Build-only workflow

After pmbootstrap init is configured for the exact pmaports checkout:

~~~bash
pmbootstrap status
pmbootstrap build <device-or-kernel-package>
pmbootstrap kconfig check <kernel-package>
pmbootstrap initfs build
pmbootstrap install
pmbootstrap export <explicit-export-directory>
pmbootstrap log
~~~

Consult current --help. Build/package names and options are port-specific. pmbootstrap export is preferable when the next step is manual inspection: it makes artifacts available without immediately sending them to a device.

Use pmbootstrap kconfig edit/generate/migrate only after preserving the current config and understanding the package workflow. A generated config still requires review against upstream Kconfig dependencies.

## envkernel

envkernel can speed edit/build/test cycles for a local kernel, but it changes the normal package source path. Record exactly which local tree/output is used and ensure the final pmaports package remains reproducible. Do not let a successful envkernel test hide uncommitted kernel changes.

## Artifact verification

Before device interaction:

- list exported artifacts and hashes;
- inspect boot image/DTBO metadata;
- identify whether rootfs is raw/sparse/filesystem/archive;
- confirm deviceinfo flash method/partitions from exact device evidence;
- confirm the generated kernel build marker and patch stack;
- compare sizes with known partition limits;
- preserve the pmbootstrap log.

## Flashing boundary

pmbootstrap flasher exposes actions such as boot, flash_kernel, flash_dtbo, flash_rootfs, flash_vbmeta and sideload. These are not build commands. Before using any:

1. Read [flashing-tools.md](flashing-tools.md) and [boot-chain-and-recovery.md](boot-chain-and-recovery.md).
2. Verify the backend and exact deviceinfo partition.
3. Prefer a supported transient boot action when available.
4. Show the resolved artifact, hash, device serial, mode, partition/slot and rollback.
5. Obtain explicit user confirmation.

Never pass a manual --partition override merely to bypass an incorrect deviceinfo file. Fix/research deviceinfo first.

## Interpreting results

- initramfs shell/telnet proves early userspace and its transport, not full rootfs/peripheral support.
- pmbootstrap package success proves packaging, not kernel runtime.
- flasher success means the backend reported completion; verify the running artifact after reboot.
- a device page’s feature checkmark needs kernel revision, package source and a reproducible test.
