# Device-tree source, build, overlay and packaging tools

Keep these artifacts distinct:

| Artifact | Meaning |
|---|---|
| DTS/DTSI | Human-maintained source and includes |
| DTB | Compiled flattened base tree |
| DTSO/overlay DTS | Source describing changes to a base tree |
| DTBO | Compiled overlay blob with fixups/symbol references |
| Merged DTB | Offline result of applying one or more overlays |
| dtb.img/dtbo.img | Android table container with entries and selection metadata |
| Appended DTB/Image-dtb | Kernel plus DTB packaging used by some bootloaders |

A file extension does not prove which format is inside. Identify magic/header and provenance.

Official references:

- DT usage model: https://docs.kernel.org/devicetree/usage-model.html
- Binding schema/checks: https://docs.kernel.org/devicetree/bindings/writing-schema.html
- Overlay notes: https://docs.kernel.org/devicetree/overlay-notes.html
- AOSP DTO overview: https://source.android.com/docs/core/architecture/dto
- AOSP DTB/DTBO partitions and mkdtimg: https://source.android.com/docs/core/architecture/dto/partitions

## Preferred in-tree build

Use Kbuild for kernel DTS because raw dtc does not automatically reproduce C preprocessing, includes, generated headers, tree-specific flags or Makefile-selected overlays. Identify the Makefile target and build into O=:

~~~bash
make -C <tree> O=<out> ARCH=arm64 <toolchain-vars> <config-target>
make -C <tree> O=<out> ARCH=arm64 <toolchain-vars> <exact-dtb-or-dtbo-target>
~~~

[build-kernel-artifacts.sh](../scripts/build-kernel-artifacts.sh) records this operation.

## Raw dtc: limited use

Raw dtc is appropriate for decompiling a blob or compiling a genuinely self-contained source with known include/preprocess requirements:

~~~bash
dtc -I dtb -O dts -o decoded.dts input.dtb
dtc -I dts -O dtb -o output.dtb source.dts
dtc -@ -a 4 -I dts -O dtb -o output.dtbo overlay.dts
~~~

The -@ flag emits symbol/fixup information needed by label-based overlays. The alignment requested by -a must match the packaging requirement; AOSP documents four-byte alignment for mkdtimg inputs. Do not copy these flags without checking the target build system.

Decompiled DTS is not canonical source: labels, comments, include boundaries, macros and symbolic constants can be lost or rewritten.

## Read-only inspection

~~~bash
fdtdump artifact.dtb
fdtget artifact.dtb / compatible
fdtget -t x artifact.dtb /memory reg
dtc -I dtb -O dts -o artifact.decoded.dts artifact.dtb
~~~

Interpret cell arrays with parent #address-cells/#size-cells and the applicable binding. fdtget output is not self-describing. Avoid fdtput for normal development; change source and rebuild so provenance remains reviewable.

## Offline overlay verification

Prerequisites:

- exact base DTB the overlay targets;
- base symbols when label references are used;
- overlay compiled with expected fixups;
- verified overlay order, because overlays may depend on earlier overlays.

Apply offline:

~~~bash
fdtoverlay -i base.dtb -o merged.dtb first.dtbo second.dtbo
dtc -I dtb -O dts -o merged.dts merged.dtb
~~~

Use [apply-and-verify-dt-overlays.sh](../scripts/apply-and-verify-dt-overlays.sh) to validate FDT magic, apply in explicit order, decompile and hash the result. Its manifest records the resolved `fdtoverlay` and `dtc` paths, version strings, and executable hashes; preserve that manifest with the output.

~~~bash
scripts/apply-and-verify-dt-overlays.sh \
  --base <exact-base.dtb> \
  --overlay <first.dtbo> \
  --overlay <dependent-second.dtbo> \
  --output <merged-test.dtb> \
  --dry-run
~~~

Remove `--dry-run` only after reviewing the resolved input order. The result and its `.dts`, `.sha256`, and `.manifest` sidecars are new host-side files; no target is touched.

Successful application proves structural references resolved. It does not prove the bootloader will select those overlays, the merged tree describes the target, or hardware will work.

## Binding and DT validation

~~~bash
make dt_binding_check DT_SCHEMA_FILES=<binding-pattern>
make dtbs_check DT_SCHEMA_FILES=<binding-pattern>
make dt_binding_check dtbs_check
~~~

Run the targeted check during iteration and the relevant broader checks before upstreaming. dtbs_check can skip schemas that fail binding validation; inspect both outputs.

## Android DT table packaging

mkdtimg create/cfg_create produces an Android DT table container. The table can include page size, entry order, id, rev and custom selector values used by the bootloader. A single DTB/DTBO may still require a table container. Conversely, some devices want a raw, appended or vendor_boot-contained DTB.

Prefer a checked-in mkdtimg config because entry metadata/order is reviewable:

~~~text
  page_size=<verified-value>
  id=<verified-global-selector-if-any>

board-rev-a.dtbo
  rev=<verified-value>

board-rev-b.dtbo
  rev=<verified-value>
~~~

Use [pack-dtbo-image.sh](../scripts/pack-dtbo-image.sh). It requires page_size to be explicit, runs cfg_create, dumps the resulting table and hashes it, and records the resolved `mkdtimg` path/version/hash. It does not sign or flash.

~~~bash
scripts/pack-dtbo-image.sh \
  --config <reviewed-dtboimg.cfg> \
  --output <candidate-dtbo.img> \
  --dry-run
~~~

The helper verifies that every config entry exists, has FDT magic and is four-byte aligned. Removing `--dry-run` creates the table plus dump, copied config, hash and manifest sidecars. Compare the dump with the known-good image before any boot test.

Never invent id/rev/custom selectors. Determine them from bootloader/vendor source, known-good table dumps and exact target artifacts.

## Final artifact checklist

- exact source commit and dirty diff recorded;
- DTS include/overlay order recorded;
- Kbuild command/tool versions recorded;
- dt_binding_check/dtbs_check result recorded;
- raw DTB/DTBO hashes recorded;
- offline merged tree inspected;
- mkdtimg config and dump stored;
- bootloader-selected format/location verified;
- size/alignment/AVB requirements verified;
- artifact contains an identifiable test marker where suitable;
- flashing remains separately authorized.
