# Upstream-oriented patch preparation

Upstreaming starts during research: use current subsystem architecture and bindings, preserve DT ABI, gather runtime evidence, and avoid a downstream compatibility layer that must later be discarded.

## Pre-submission readiness

- Work from a named current upstream/subsystem base and record full commit.
- Check linux-next, maintainer trees, lore and patchwork for overlapping work.
- Read MAINTAINERS, recent accepted patches and subsystem-specific process docs.
- Ensure hardware facts and compatible strings are target-proven.
- Remove diagnostic hacks, commented experiments, vendor-only properties and unexplained values.
- Separate technical availability from firmware redistribution.
- Confirm user—not the agent—can make the Developer’s Certificate of Origin attestation before adding Signed-off-by.
- Never send patches, email maintainers or open merge requests without user authorization.

Authoritative process starting points:

- https://docs.kernel.org/process/submitting-patches.html
- https://docs.kernel.org/process/maintainer-soc.html
- https://docs.kernel.org/devicetree/bindings/writing-schema.html
- the target tree’s Documentation/process and MAINTAINERS at the exact revision.

## Series architecture

A typical dependency-aware series may be split into:

1. dt-binding schema/update;
2. dt-binding constants only when justified;
3. reusable SoC/provider driver support;
4. subsystem driver support;
5. SoC DTSI nodes;
6. board DTS;
7. defconfig only when maintainers expect it and an upstream board needs it;
8. documentation/MAINTAINERS.

Do not force all layers into one tree. Driver/binding/DTS changes may need sequencing across maintainer trees, an immutable branch, or a later release. Follow current maintainer guidance.

## Patch quality

Each commit should:

- do one reviewable thing and build independently when possible;
- explain the hardware and why the current model is correct;
- cite public documentation or clearly describe target validation;
- have no unrelated formatting or generated churn;
- use existing subsystem abstractions;
- preserve bisectability and compatibility;
- document remaining limitations without claiming full support.

Do not add magic register writes to board DTS, undocumented properties, broad always-on workarounds, or duplicate vendor frameworks merely because downstream does.

## Checks

Select checks from the actual change:

| Change | Minimum evidence/checks |
|---|---|
| DT binding | targeted and full relevant dt_binding_check; schema examples |
| DTS/DTSI | dtbs, targeted dtbs_check, W=1 where required/current guidance |
| Driver | relevant architecture builds, modules, warnings, static analysis/tests where available |
| Cross-subsystem | build each dependency state expected during merge |
| Runtime | before/after logs and minimal exact-target functional test |
| Power-related | runtime PM plus suspend/resume and thermal/power observations |

Also review checkpatch output intelligently; passing checkpatch is not proof of correctness. Record checks not run and why.

## Cover letter and commit evidence

Include base, dependency links, changes by revision, tested device/variant/firmware, test method, known limitations and who tested. Do not claim Tested-by or other trailers without the person’s explicit statement.

Use scripts/get_maintainer.pl plus MAINTAINERS and recent history; do not spam unrelated lists. When revising, use range-diff to explain meaningful changes and retain message/thread linkage.

## Final upstream gate

| Question | Required answer |
|---|---|
| Exact hardware identity proven? | yes, with evidence |
| Current upstream model used? | yes |
| Binding/driver/DTS dependency order valid? | yes |
| No unexplained or copied board values? | yes |
| Builds/schema checks pass? | results recorded |
| Tested on exact target? | scope and result recorded |
| Firmware/userspace boundary honest? | yes |
| Risks/regressions considered? | yes |
| User authorized external submission? | yes before sending |

