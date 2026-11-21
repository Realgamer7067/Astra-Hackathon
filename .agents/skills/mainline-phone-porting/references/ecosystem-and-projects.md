# Mobile Linux ecosystems as research evidence

These projects can reveal device identifiers, kernel branches, patch queues, boot packaging, firmware expectations, userspace integration, and people already working on related hardware. They do not replace primary kernel or target-device evidence.

## Keep the support labels separate

| Statement | What it may mean | What must still be checked |
|---|---|---|
| “postmarketOS boots” | An Alpine-based rootfs reached some stage | Which kernel, patch stack, exact variant and features |
| “mainline” | Often upstream or close to upstream | Exact base commit, carried patches, downstream drivers and unmerged DTS |
| “close-to-mainline” | A recent kernel plus a maintained delta | Size/content of delta and whether patches are submitted, rejected or local |
| “downstream port” | Linux userspace runs on an Android/vendor kernel | It does not demonstrate mainline drivers or acceptable upstream design |
| “SoC supported” | Some boards using that SoC boot upstream | Board PMIC, panel, touch, storage, firmware and boot-chain support remain separate |
| “feature works” | Someone observed useful behavior | Kernel revision, userspace, firmware, variant, test definition and reproducibility |

## postmarketOS

Start with:

- pmaports: https://gitlab.postmarketos.org/postmarketOS/pmaports
- pmbootstrap: https://gitlab.postmarketos.org/postmarketOS/pmbootstrap
- Porting guide: https://wiki.postmarketos.org/wiki/Porting_to_a_new_device
- Mainlining guide and FAQ: https://wiki.postmarketos.org/wiki/Mainlining_Guide and https://wiki.postmarketos.org/wiki/Mainlining_FAQ
- Device index: https://wiki.postmarketos.org/wiki/Devices

Inspect source, not only the device-page status table:

1. Find the device package, deviceinfo, dependencies, initramfs hooks, firmware packages, install scripts and kernel package.
2. Resolve the kernel package source URL, branch/tag/commit, config, patch list and checksums.
3. Classify every carried patch: upstream, pending, backport, distro-only, debugging workaround or unknown.
4. Check commit history and merge requests for regressions, abandoned work, variant caveats and maintainer activity.
5. Reconcile the wiki page with pmaports and actual logs. A wiki matrix can be stale or use a broad meaning of “works.”
6. Record whether pmbootstrap is only packaging an existing port or supplying a device-specific workaround.

Important distinctions:

- A device package describes packaging and installation choices; it is not authoritative hardware documentation.
- A downstream kernel package is valuable archaeology, but may contain Android APIs, old BSP interfaces, permissive hacks and large out-of-tree drivers.
- A shared mainline kernel package can hide device-specific patches elsewhere in pmaports.
- A successful initramfs/telnet stage proves more than “black screen,” but less than healthy storage, display or userspace.
- Category and feature-status definitions can change. Record the date/revision and do not turn a category into a permanent fact.

## Other projects

| Project/source | Good research use | Common trap |
|---|---|---|
| LineageOS device/kernel/vendor trees | Exact downstream branches, board config, proprietary-file manifests, boot image construction | Android HALs and blobs are not mainline drivers; forks may not match retail firmware |
| Droidian / Mobian | Debian-based packaging, userspace integration, mobile shell and service dependencies | May rely on Halium, libhybris, downstream Linux or an external patch stack |
| UBports / Halium | Android userspace compatibility boundary, device manifests, boot/rootfs packaging | Ubuntu Touch support does not imply upstream kernel support |
| Maemo Leste and other mobile distros | Userspace, telephony, power-management and packaging evidence | Distribution support and kernel support are separate axes |
| Community SoC trees | Often the newest working mainline-oriented patches and discussions | Branch may be rebased, incomplete, never submitted, or depend on unavailable firmware |
| lk2nd / U-Boot / Tow-Boot | A verified alternate/second-stage boot path on specific platforms | Never assume availability or commands for another SoC/device |
| Device wikis and chat archives | Leads, failure reports, developer identities | Ephemeral, hard to reproduce, and weak as final proof |

## Ecosystem evidence record

| Project | Exact repo/path/revision | Kernel source/base | Carried delta | Exact variant | What it proves | What it does not prove | Reproducibility |
|---|---|---|---|---|---|---|---|

When a project conflicts with upstream source or target logs, preserve the contradiction. Determine whether it is a different hardware revision, firmware generation, kernel base, or stale documentation.

