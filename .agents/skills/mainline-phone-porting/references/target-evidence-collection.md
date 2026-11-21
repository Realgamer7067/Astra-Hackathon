# Read-only target evidence collection

Collect only what resolves a named question. Prefer targeted commands over a giant dump, preserve raw outputs before filtering, and label the privilege/mode and exact running build. Collection success does not make a vendor property or log claim authoritative by itself.

Primary references:

- ADB: https://developer.android.com/tools/adb
- Android logging: https://source.android.com/docs/core/tests/debug/understanding-logging
- Device-tree model: https://docs.kernel.org/devicetree/usage-model.html

## Provenance header

Every collection records:

| Field | Required detail |
|---|---|
| Target identity | model/codename/variant plus redacted serial label |
| State | stock Android, recovery, bootloader, initramfs or mainline userspace |
| Firmware/build | Android build fingerprint or kernel full release/build marker |
| Slot/mode | observed slot and boot mode when relevant |
| Collection | UTC timestamp, host/tool version, exact command, exit status |
| Privilege | shell/root/recovery and whether access failure truncated evidence |
| Artifact identity | raw filename, byte size and SHA-256 |
| Transformation | extraction/filter/redaction command and derived-file hash |

## Minimal Android-side ladder

Select one authorized device explicitly. Start with identity and kernel facts:

~~~bash
adb devices -l
adb -s <verified-serial> shell getprop ro.product.device
adb -s <verified-serial> shell getprop ro.product.board
adb -s <verified-serial> shell getprop ro.board.platform
adb -s <verified-serial> shell getprop ro.build.fingerprint
adb -s <verified-serial> shell getprop ro.boot.slot_suffix
adb -s <verified-serial> shell uname -a
adb -s <verified-serial> shell cat /proc/version
~~~

Properties are vendor namespaces and can be stale, overridden or generic. Cross-check them with bootloader identifiers, source and artifacts.

Then collect only relevant items:

| Need | Candidate evidence | Caveat |
|---|---|---|
| Kernel config | `/proc/config.gz`, build artifact `.config`, vendor defconfig/fragments | Requires IKCONFIG exposure; shipped config may differ from source default |
| Boot arguments | `/proc/cmdline`, `/proc/bootconfig` | Bootloader may rewrite; redact unique IDs |
| Complete kernel log | raw `dmesg`/pstore with boot marker and timestamps | Android permissions may deny or truncate it |
| Android logs | relevant `logcat -b all -d` window or local bugreport | Can contain personal/app/network information |
| Running FDT | binary `/sys/firmware/fdt` where exposed; `/proc/device-tree` as fallback | Running tree may be bootloader-fixed-up and differ from source |
| Drivers/modules | `/proc/modules`, module path, `modinfo`, vermagic, hashes | Loaded module does not prove feature correctness |
| Probe/defer state | sysfs device/driver links, modalias, `devices_deferred`, relevant debugfs | debugfs is unstable and often unavailable |
| Partitions | by-name symlinks, `lsblk`, `/proc/partitions`, fstab and slot property | Names can be aliases; do not read sensitive partition contents |
| Firmware failures | complete firmware-loader/remoteproc log and driver revision | A filename in a log does not prove lawful availability or exact board data |

When readable, preserve the running FDT as raw host-side bytes before decompiling:

~~~bash
adb -s <verified-serial> exec-out cat /sys/firmware/fdt > running-fdt.dtb
sha256sum running-fdt.dtb
dtc -I dtb -O dts -o running-fdt.decoded.dts running-fdt.dtb
~~~

Redirection occurs on the host. Verify FDT magic and command exit status; an empty/truncated file is not evidence. Decompiled output loses original includes, labels and comments.

## Mainline/initramfs collection

Capture the exact kernel release/build marker first, then a single uninterrupted log from boot start where possible. Useful read-only evidence includes `/proc/iomem`, `/proc/interrupts`, `/proc/modules`, `/sys/firmware/fdt`, device/driver symlinks, deferred probes and only the clock/regulator/power-domain summaries relevant to the failing feature.

Do not treat missing debugfs/sysfs nodes as proof that hardware is absent; config, permissions and kernel revision can remove interfaces.

## Privacy and preservation

Before sharing, review and redact:

- device serials, IMEI/MEID and phone numbers;
- account names, email addresses, tokens, keys and cookies;
- Wi-Fi SSIDs/BSSIDs, MAC addresses and public/private IPs when unnecessary;
- user-installed package lists, filenames, notifications and application logs;
- modem/subscriber identifiers and location history.

Keep an unmodified raw copy privately with its hash; create a separately hashed redacted copy. State what was removed so the absence is not misinterpreted. A full Android bugreport is privacy-heavy—collect it only when targeted logs cannot answer the question and inspect it locally before sharing.

Never request or dump EFS-like identity data, modemst/calibration, persist, keystore, userdata or secure partitions for routine mainlining research. Partition names and metadata are usually enough.

## Evidence quality checks

- Exact build marker appears in the log.
- Command exit status and stderr are preserved.
- Output is complete rather than a screenshot/snippet.
- Binary artifacts have size and SHA-256.
- Host transformations are recorded and reproducible.
- Stock, vendor, mainline and recovery outputs are not mixed silently.
- Negative evidence states permission/config/collection limitations.
