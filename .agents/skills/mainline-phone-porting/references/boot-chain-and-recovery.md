# Android boot chain, image layout and recovery research

Do not generalize a boot procedure across phones. Establish the exact boot generation, verification state, image format, partitions, slots and recovery path for the target variant and firmware.

## Boot-chain dossier

| Item | Evidence required | Why it matters |
|---|---|---|
| Unlock state and policy | Official documentation or observed target state | Custom-image execution and whether unlocking wipes data |
| Header/version/compression | Extracted known-good image with tool/version | Kernel, ramdisk, DTB, bootconfig placement and size rules |
| boot/vendor_boot/init_boot/recovery | Partition map plus Android-generation docs | Contents moved between partitions over Android generations |
| DTB/DTBO location and selection | Extracted images, running FDT, bootloader/vendor source | Base DTBs and overlays may be selected dynamically |
| A/B or virtual A/B | Bootloader variables/official docs/partition map | Wrong slot can hide a correct test or trigger rollback |
| AVB/vbmeta/rollback protection | Official AVB docs and target state | Structurally correct modified images may still be rejected |
| Kernel load constraints | Vendor source/image metadata/tested path | Size, alignment, architecture, load address and appended DTB |
| Recovery route | Verified stock image, mode and host tooling | Required before persistent mutation |

Authoritative starting points:

- https://source.android.com/docs/core/architecture/bootloader
- https://source.android.com/docs/core/architecture/bootloader/boot-image-header
- https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions
- https://source.android.com/docs/core/architecture/bootloader/dtb-images
- https://source.android.com/docs/security/features/verifiedboot/verified-boot
- https://source.android.com/docs/core/ota/ab
- https://source.android.com/docs/core/ota/dynamic_partitions

## Preferred testing ladder

Choose the least persistent method actually verified for this device:

1. Inspect existing artifacts and running metadata.
2. Build and validate without touching the device.
3. Boot transiently through a documented boot or second-stage path.
4. Write only a verified inactive/recoverable target with an exact backup and restoration procedure.
5. Use persistent modification only when prior stages cannot answer the question.

Do not output a generic command. Some devices use fastboot, fastbootd, Download/Odin mode, proprietary tools, a secondary loader, recovery, or no transient path. Fastboot boot and partition names are not universal.

## Mutation gate

Before any mutation, state the artifact hash, target partition and slot, backup source and verification, expected format/size, recovery entry method, stock restore artifact, host/cable requirements, and failure boundary. Ask for explicit confirmation at that moment.

Never make repartitioning an early bring-up step. Never overwrite bootloader, radio, persistent calibration/identity, secure-storage or partition-table data merely to test a kernel.

