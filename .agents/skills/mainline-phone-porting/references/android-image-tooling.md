# Android boot and partition image tooling

Inspect a known-good image before constructing anything. Repacking must reproduce the target’s exact image generation and bootloader contract; a generic mkbootimg command is unsafe.

## Tool and artifact map

| Artifact | Primary tools | Key facts to preserve |
|---|---|---|
| boot.img | AOSP unpack_bootimg/mkbootimg, avbtool | header version, kernel/ramdisk, cmdline, OS fields, offsets/alignment, signature/footer |
| vendor_boot.img | unpack_bootimg/mkbootimg | header v3/v4, DTB, vendor ramdisk fragments/table, bootconfig |
| init_boot.img | unpack_bootimg/mkbootimg | generic ramdisk and header relationship |
| dtbo.img/dtb.img | mkdtimg | page size, order, id/rev/custom selectors |
| vbmeta*.img | avbtool | descriptors, chain partitions, key identity, flags, rollback location/index |
| super.img | lpdump/lpunpack/lpmake/lpadd | sparse state, metadata slots, groups, logical sizes and slots |
| sparse filesystem image | simg2img/img2simg | sparse encoding versus raw filesystem |
| OTA payload.bin | matching official payload tooling | manifest, partitions, operation/data blobs and source build |

Primary sources:

- Boot image header: https://source.android.com/docs/core/architecture/bootloader/boot-image-header
- Vendor boot: https://source.android.com/docs/core/architecture/partitions/vendor-boot-partitions
- DTB images: https://source.android.com/docs/core/architecture/bootloader/dtb-images
- AVB implementation/tool: https://android.googlesource.com/platform/external/avb/
- Dynamic partition tools: https://android.googlesource.com/platform/system/extras/+/master/partition_tools/

## Inspection workflow

1. Preserve original filename and calculate SHA-256.
2. Identify format with file/magic and partition context.
3. Run the format-specific inspector and save complete output.
4. Extract into a new directory; never overwrite the original.
5. Hash extracted kernel, ramdisks, DTB/DTBO and metadata.
6. Record the tool repository/version.
7. Compare with a second trusted method where vendor formats are unusual.

Typical read-only commands:

~~~bash
sha256sum known-good.img
unpack_bootimg --boot_img known-good-boot.img --out unpacked
mkdtimg dump known-good-dtbo.img
avbtool info_image --image known-good.img
lpdump super.img
~~~

Exact CLI spelling can vary by source revision. Check --help from the version being used.

## Repacking rules

- Start from parameters emitted by the exact known-good image; do not use values from another model.
- Preserve compression type and any vendor-specific kernel concatenation.
- Preserve boot header generation and understand which partition owns DTB, ramdisk and bootconfig.
- For vendor_boot v4, preserve fragment names/types/order/table semantics.
- Preserve partition-size constraints and required AVB footer space.
- Re-run unpack/dump/info_image on the new image and compare metadata.
- A byte-identical unpack→repack is useful when achievable, but non-identical padding alone may not imply failure; understand the format.
- Never reuse production signing keys you do not own. Never recommend leaked keys or bypassing secure boot.
- Do not disable AVB or verification as a generic fix. Determine the device’s supported unlocked-development behavior.

## GKI/ACK/vendor-module boundary

Newer Android devices may use a generic kernel plus vendor_boot/vendor_dlkm/odm_dlkm modules. Determine kernel module ABI/versioning, ramdisk module lists, load order and matching vendor firmware. Replacing only boot.img may leave an incompatible vendor module set.

Kleaf or the vendor’s kernel build can generate coordinated dist artifacts; prefer that over hand assembly when supported.

## Community tools

magiskboot and OEM-specific unpackers can handle formats absent from a particular AOSP tool. Treat output as Tier 3/4 evidence, pin a version and compare against bootloader/vendor source. abootimg/unpackbootimg commonly target older headers and should not be assumed correct for modern vendor_boot/init_boot.

## Stop conditions

Do not build a flashable image when header generation, DTB location, ramdisk role, compression, AVB policy, partition size or slot behavior is Unknown. The next step is image archaeology, not trial flashing.
