# Toolchains and reproducible builds

Use the build system defined by the exact source tree. Do not convert a vendor Kleaf/build.sh project to plain make—or an upstream tree to Android scripts—without evidence that the alternate path is supported.

Official starting points:

- Kbuild: https://docs.kernel.org/kbuild/kbuild.html
- LLVM builds: https://docs.kernel.org/kbuild/llvm.html
- Android kernel builds/Kleaf: https://source.android.com/docs/setup/build/building-kernels
- External modules: https://docs.kernel.org/kbuild/modules.html

## Pre-build record

Capture:

| Item | Required |
|---|---|
| Source | repository, branch, full commit, shallow status, dirty diff |
| Architecture | arm64/arm and exact SoC ABI |
| Build family | Kbuild, Kleaf, legacy build.sh, pmaports |
| Config origin | upstream defconfig, vendor defconfig, fragments or known-good .config |
| Compiler | full version and provenance |
| Binutils/LLVM | versions and LLVM/CROSS_COMPILE settings |
| Output | fresh dedicated O=/OUT_DIR/DIST_DIR path outside the source worktree |
| Intended targets | Image/Image.gz/etc., modules, named DTBs/DTBOs |

Do not call a build reproducible if the tree is dirty but the diff is not preserved.

## Upstream/mainline-oriented Kbuild

Prefer an out-of-tree output directory:

~~~bash
make -C <kernel-tree> O=<output> ARCH=arm64 LLVM=1 <defconfig>
make -C <kernel-tree> O=<output> ARCH=arm64 LLVM=1 -j<N> Image modules dtbs
~~~

For GCC cross compilation, use the exact installed target prefix:

~~~bash
make -C <kernel-tree> O=<output> ARCH=arm64 \
  CROSS_COMPILE=aarch64-linux-gnu- <defconfig>
make -C <kernel-tree> O=<output> ARCH=arm64 \
  CROSS_COMPILE=aarch64-linux-gnu- -j<N> <explicit-targets>
~~~

The examples show command shape only. Determine config and image targets from the tree’s arch Makefile, board documentation and known build. LLVM=1 can remove the need for a GNU cross prefix when using the full LLVM tool set, but use the same LLVM value for configuration and build. `LLVM=-14` selects suffixed tools such as `clang-14` and `ld.lld-14`; `LLVM=/path/to/llvm/` selects tools beneath that prefix. Record the resolved compiler, linker, binutils, host compiler, Kbuild-built `dtc` and `pahole`, not a guessed generic name.

Use [build-kernel-artifacts.sh](../scripts/build-kernel-artifacts.sh) to make the config/toolchain/targets explicit and record a manifest.

Example after the config and targets have been verified in the exact tree:

~~~bash
scripts/build-kernel-artifacts.sh \
  --tree <kernel-tree> \
  --out <new-output-directory> \
  --arch arm64 \
  --llvm 1 \
  --config-target <verified-defconfig-target> \
  --target Image \
  --target <verified-board-dtb-target>
~~~

Start with `--dry-run`. Add `--target modules` or a DTBO target only when it is actually required. Use a new/empty output directory. `--reuse-output` is an explicit exception that records complete pre/post content inventories and attributes only new/content-changed files to that run, preventing an unchanged stale DTB from appearing as a newly built artifact. The helper hashes every changed regular output—including `zImage`, `.ko`, and vendor-specific targets—captures source state before touching output, preserves source-like untracked files, records submodules, and refuses output inside the source worktree.

Evidence is placed under `<out>/.mainline-port-evidence/run.*`; retain that directory with exported artifacts. If the source state changes during the build, treat the build’s source identity as unstable and repeat after freezing it.

For 32-bit mobile kernels, do not substitute `arm64`/`Image`: read [arm32-mobile-bringup.md](arm32-mobile-bringup.md) and select the exact documented `ARCH=arm`, configuration, `zImage`/other target and boot ABI.

## Configuration discipline

- Begin from the correct upstream defconfig or documented vendor build config.
- Use olddefconfig only after selecting a known source config.
- Compare requested symbols with the final output .config; Kconfig dependencies can silently change selections.
- Record built-in versus module status. A module needed before rootfs must be in initramfs or built in.
- Use scripts/config carefully for repeatable changes, then review the diff.
- savedefconfig is useful for minimizing, but its output is not automatically the project’s accepted defconfig.
- A running downstream /proc/config.gz is archaeological evidence, not a valid mainline config by itself.
- Avoid allyesconfig/giant vendor configs as bring-up proof; they obscure reachability and can create unrelated failures.

## Building DT targets

Prefer Kbuild because it supplies C preprocessing, include paths, dtc flags, generated headers and overlay rules:

~~~bash
make -C <kernel-tree> O=<output> ARCH=arm64 LLVM=1 dtbs
make -C <kernel-tree> O=<output> ARCH=arm64 LLVM=1 \
  <repository-specific-relative-dtb-or-dtbo-target>
~~~

Do not guess a target name. Inspect arch/arm64/boot/dts/*/Makefile and the tree’s make help/output. Some downstream trees build concatenated Image-dtb artifacts or external DT directories.

## Android Kleaf and legacy build.sh

For Kleaf:

1. Use the branch’s repo manifest and source documentation.
2. Discover Bazel targets in BUILD.bazel and device documentation.
3. Run the provided tools/bazel target and capture dist artifacts.
4. Do not assume environment variables influence a hermetic Kleaf build.

For legacy build.sh:

1. Verify the branch actually supports it.
2. use the documented BUILD_CONFIG relative to the repo root;
3. record OUT_DIR/DIST_DIR and toolchain;
4. inspect build.config includes and post-build image steps.

Android 13 introduced Kleaf and later branches may not support build.sh; the exact branch is decisive.

## External modules

Build only against the exact configured/built kernel output:

~~~bash
make -C <kernel-output-or-tree> M=<module-source> modules
~~~

modules_prepare alone does not create Module.symvers when CONFIG_MODVERSIONS requires it. A module compiled successfully may still fail version/signature/ABI checks on target.

## Validation ladder

| Stage | Suggested target/check | Proves |
|---|---|---|
| Configuration | olddefconfig, diff final .config | Requested symbols resolved |
| Compile | explicit Image/modules/DT targets | Source compiles with recorded inputs |
| DT | dt_binding_check/dtbs_check, targeted DT_SCHEMA_FILES | Schema conformance |
| Warnings | W=1 or subsystem-required level | Additional diagnostics, not runtime correctness |
| Static checks | checkpatch, sparse/smatch/Coccinelle where relevant | Specific classes of issues |
| Artifact | file, size, hash, embedded version | Exact output identity |
| Runtime | build marker and target logs | Exact artifact reached observed state |

## Frequent build failures

- Wrong branch/config pair or missing generated headers.
- Host dtc/dtc version used instead of the tree’s expected tool.
- Mixed GCC/LLVM utilities or absent cross binutils.
- BTF failure from missing/old pahole.
- OpenSSL/libelf/bison/flex dependencies missing.
- Stale O= directory after branch switch.
- Kconfig symbol renamed or dependency unmet.
- dtbs_check skipped because binding validation failed first.
- Image exceeds bootloader/partition size despite successful compile.
- External modules built against mismatched Module.symvers or release string.

Never solve unexplained build failures by deleting the user’s source changes. Use a new output directory or preserve a patch before clean operations.
