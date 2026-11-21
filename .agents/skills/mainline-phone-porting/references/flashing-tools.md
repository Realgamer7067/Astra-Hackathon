# Flashing and boot-tool decision guide

Flashing is the last step of an evidence chain, not an exploratory substitute for understanding image format. Never provide a ready-to-run mutating command until the exact device, mode, serial, partition, slot, artifact, verification state and recovery path are established and the user confirms.

## Classify operations

| Class | Examples | Default handling |
|---|---|---|
| Read-only discovery | list devices, version/help, get supported variables, inspect local image/PIT/table | Allowed after confirming target selection |
| Transient execution | supported fastboot boot, verified second-stage/network boot | Prefer when truly supported; still confirm image compatibility |
| Recoverable write | inactive slot or documented development partition with tested restore | Explicit confirmation and rollback required |
| Persistent/high-risk | active boot, vbmeta, dtbo, rootfs, recovery | Explicit confirmation immediately before command |
| Critical/destructive | unlock, erase/format, repartition/PIT, bootloader/radio/calibration/secure partitions | Do not recommend unless necessary, officially supported, fully evidenced and explicitly confirmed |

Bootloader unlocking commonly erases user data. Relocking with modified/incompatible partitions can make recovery harder. Treat both as destructive.

## Identify host, target and mode

Before every operation:

1. Use an up-to-date, authoritative host tool and record version/hash/source.
2. List connected devices and require exactly one or select an explicit serial.
3. Record USB ID and mode.
4. Query non-mutating supported metadata.
5. Verify artifact hash and parse it locally.
6. Resolve physical versus logical partition and A/B slot.
7. Confirm battery/power stability, cable/port and no flaky hub.
8. State rollback steps and stock artifact location.

Never interpolate an untrusted filename, partition name or serial into a shell command.

## Tool families

| Device/mode | Common tools | Appropriate use | Critical cautions |
|---|---|---|---|
| Android userspace/recovery | adb, adb sideload | logs, shell, file transfer, reboot modes, signed recovery packages | adb authorization and recovery semantics vary; not raw partition proof |
| Bootloader fastboot | official Platform Tools fastboot | getvar, supported transient boot, physical boot partitions | fastboot boot may be unsupported; names/slots vary |
| fastbootd | official fastboot in userspace mode | logical/dynamic partitions | distinguish with is-userspace; do not treat as bootloader fastboot |
| postmarketOS wrapper | pmbootstrap flasher | uses deviceinfo-selected backend/artifacts | deviceinfo can be wrong; inspect resolved operation |
| Samsung Download Mode | Samsung-supported tooling where available, Odin, open-source Heimdall | protocol-specific partition transfer | PIT names are device-specific; do not repartition or assume Heimdall supports generation |
| Qualcomm EDL | OEM/service tools with an authorized matching programmer | recovery/service on supported devices | signed firehose/programmer and storage geometry are exact-device requirements; no auth bypass/leaked loaders |
| MediaTek preloader/BootROM | OEM SP Flash Tool/authorized Download Agent; community tools only where lawful | supported recovery/service | scatter/DA/preloader mismatch can be severe; do not use exploit/bypass workflows |
| Unisoc download mode | OEM ResearchDownload/UpgradeDownload and matching authorized FDL | supported firmware/recovery | FDL/packet/partition config is platform-specific |
| Rockchip loader/maskrom | rkdeveloptool/official vendor tools | supported Rockchip boards/tablets | loader and storage target must match board |
| Allwinner FEL | sunxi-tools/fel where SoC supports it | RAM loading and board-specific recovery | exact SoC/DRAM init and board boot flow required |
| U-Boot shell/fastboot/DFU | U-Boot commands enabled by exact build | board-controlled development path | environment/partition aliases vary; never assume commands are compiled in |
| Secondary loaders | lk2nd or platform-specific loader | verified supported devices only | not universal even within one SoC family |

Naming a tool is not a recommendation to use it. Prefer official/documented paths. Do not help bypass bootloader authentication, secure boot, ownership checks or paid/service authorization.

## Fastboot and fastbootd reconnaissance

The official AOSP distinction is important: bootloader fastboot handles bootloader-accessible physical partitions; fastbootd is a userspace mode for logical/dynamic partitions. Useful non-mutating queries, if implemented, include device listing and getvar for product, current-slot, slot count, is-userspace and partition properties. Unsupported variables are common.

Official references:

- lock/unlock behavior: https://source.android.com/docs/core/architecture/bootloader/locking_unlocking
- fastbootd: https://source.android.com/docs/core/architecture/bootloader/fastbootd
- adb: https://developer.android.com/tools/adb

Never use erase, format, set_active, flashing unlock/lock, force flash or logical-partition create/delete/resize as diagnosis.

After selecting one device explicitly, a read-only reconnaissance session can use this shape:

~~~bash
fastboot --version
fastboot devices -l
fastboot -s <verified-serial> getvar product
fastboot -s <verified-serial> getvar is-userspace
fastboot -s <verified-serial> getvar current-slot
fastboot -s <verified-serial> getvar has-slot:<verified-partition-base-name>
fastboot -s <verified-serial> getvar partition-size:<verified-partition-name>
~~~

Do not turn an empty, FAILED, or unsupported response into a guessed value. Record the exact response and corroborate it with bootloader source, stock image metadata, fstab or partition tables. Avoid broad `getvar all` dumps in shared reports because vendors may expose device identifiers.

From authorized Android userspace, establish identity before requesting a mode change:

~~~bash
adb version
adb devices -l
adb -s <verified-serial> shell getprop ro.product.device
adb -s <verified-serial> shell getprop ro.boot.slot_suffix
~~~

`adb reboot bootloader` changes device state and can interrupt work, so announce it and confirm the selected serial first. It does not prove that the resulting mode implements fastboot or supports transient boot.

## Samsung Download Mode

Odin packages, tar.md5 containers, LZ4-compressed components and PIT names vary by firmware generation. Heimdall implements a Samsung protocol but device support is not universal. A successful detect or PIT read does not prove safe writing.

Before a Samsung write, verify exact model suffix/bootloader revision, official firmware restore package, Download Mode recovery, target PIT entry from the device, accepted container/compression, image size and whether the bootloader allows custom images. Avoid PIT repartitioning.

For a Heimdall version known to support the exact device, begin with its own help and non-writing detection. Its upstream documentation describes this reconnaissance shape:

~~~bash
heimdall version
heimdall help
heimdall detect
heimdall print-pit --no-reboot
~~~

After `--no-reboot`, Heimdall expects `--resume` on the next command in the same Download Mode session; device/version defects exist, so stopping and manually rebooting may be safer than assuming session continuation. Preserve the PIT output, but do not use another model’s PIT and do not pass `--repartition` during ordinary kernel testing. Generate an exact write command only after matching its partition name to the verified PIT and receiving confirmation.

Primary project: https://github.com/Benjamin-Dobell/Heimdall

## pmbootstrap flasher

First inspect the selected device and backend:

~~~bash
pmbootstrap status
pmbootstrap flasher --help
pmbootstrap flasher list_devices
pmbootstrap export <explicit-export-directory>
~~~

Inspect the exported image and the selected pmaports `deviceinfo` before considering `flasher boot`, `flash_kernel`, `flash_dtbo`, `flash_rootfs`, `flash_vbmeta`, `flash_lk2nd`, or `sideload`. A `--partition` override is not a reasonable way to work around uncertain deviceinfo. Treat each flasher subcommand as the underlying backend operation, apply the same confirmation gate, and capture the full pmbootstrap log.

Current command reference: https://docs.postmarketos.org/pmbootstrap/main/usage.html

## SoC emergency/service modes

EDL, BootROM/preloader, FDL, maskrom and FEL may sit below the ordinary bootloader and can write broad storage ranges. Use only an official or well-audited path for hardware you own/manage, with exact signed loaders/configuration and full recovery research. Never suggest random programmer/DA/FDL binaries from another model.

There is deliberately no generic EDL, SP Flash Tool, mtkclient, ResearchDownload, FDL, maskrom or FEL write recipe here. For one of these modes, the agent must first document the exact protocol generation, SoC/package, storage type, authorized loader/programmer/DA/FDL provenance, partition map source, authentication state and OEM recovery documentation. If any are Unknown, stay with local image inspection or officially documented read-only detection.

## Executing an approved write

Once the command-presentation contract below is fully populated and the user confirms, follow this sequence:

1. Re-run tool version, selected-serial and mode checks immediately before the write.
2. Re-hash the local artifact and compare its parsed type/size with the verified target.
3. Issue one exact write or transient-boot command; do not combine unrelated partitions.
4. Save complete stdout/stderr and stop on any unexpected product, slot, size, protocol or verification response.
5. Verify the running build marker or read-back metadata by a separately justified method.
6. If validation fails, use the pre-written rollback route; do not improvise by trying neighboring partition names.

## Command presentation contract

When the gate is complete, present:

~~~text
Target device/serial:
Current mode and proof:
Tool/version/source:
Artifact/path/hash/type:
Target partition and slot:
Why that target is correct:
Expected tool response:
How running artifact will be verified:
Failure stop condition:
Rollback/recovery:
Data-loss/non-boot risk:
Confirmation required: yes
~~~

Then provide one command at a time. Stop after any unexpected product, slot, size, verification, protocol or disconnect result. Do not “try nearby partitions.”
