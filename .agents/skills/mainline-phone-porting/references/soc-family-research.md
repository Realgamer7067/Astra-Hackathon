# SoC-family research prompts

These are search maps, not templates. Verify exact generation, package and board topology; vendor frameworks change across generations.

## Qualcomm

Research exact MSM/APQ/SDM/SM/QCS identity and board/PMIC combination. Potential dependency families include TLMM, GCC/clock controllers, resets, RPM/RPMh, SPMI PMIC blocks, PDC, interconnect, IOMMU, SCM/PAS, SMEM, GLINK/SMD/QRTR, remoteproc, MHI, UFS/SDHCI, DPU/MDSS/DSI/PHY and WCN.

Traps: using QRD/MTP wiring as phone proof; mixing RPM and RPMh; firmware-protected remote processors; PMIC subtype differences; assuming lk2nd from another generation; translating downstream qcom properties literally.

## Samsung Exynos

Research exact Exynos ID/revision, board/codename, PMIC/MFD, clock domains, pin banks, PMU/sysreg, timers, SYSMMU, storage, USB PHY, DECON/FIMD, DSIM/DP PHY, audio and secure-firmware expectations. Retail variants often change panel, touch, camera, NFC and RF components while keeping the SoC.

Traps: GPL source not matching installed firmware; deep include/overlay stacks; vendor display/media stacks unlike upstream; bootloader-specific image/appended-DTB rules; secure firmware owning power or coprocessor operations.

## MediaTek

Research exact MT platform and aliases, PMIC/pwrap, topckgen/infracfg/pericfg, reset, pinctrl, SCPSYS, IOMMU, EMI/reserved memory, interconnect, storage, USB PHY, MMSYS/display, DSI/PHY, SCP/SSPM/MDP/VPU and modem boundaries.

Traps: evaluation-board DTS used as phone proof; incompatible clock/reset indices; vendor drivers tied to Android frameworks; bootloader handoff assumptions; similar SoC names with different multimedia blocks.

## Unisoc / Spreadtrum

Research all aliases (SC/UMS/Tiger), architecture/revision, PMIC, access bus, clocks/resets/syscon, pinctrl, power domains, storage, display and modem/secure firmware. Source scarcity means Unknown may remain the correct result.

Traps: retail spec sites as component proof; vendor-only frameworks; incomplete GPL releases; nearby SoC board files treated as compatible; closed firmware coupling.

## Rockchip, Allwinner and other tablet-class SoCs

Upstream SoC support may be broad while the tablet remains board-specific. Verify PMICs, rails, panels, touch, Wi-Fi modules, cameras and boot layout. U-Boot/Tow-Boot availability is exact-board evidence only.

## Required family output

| Foundation | Upstream status/revision | Driver/binding | Target evidence | Earliest missing prerequisite | Confidence |
|---|---|---|---|---|---|
| CPU/PSCI/GIC/timer/console |  |  |  |  |  |
| memory/reserved memory |  |  |  |  |  |
| clock/reset/pinctrl/power/interconnect/IOMMU |  |  |  |  |  |
| storage/USB |  |  |  |  |  |
| display/input |  |  |  |  |  |
| firmware/remote processors |  |  |  |  |  |

Search by IP blocks and compatibles, not only the SoC string. Reused names can hide different integration; reused IP may already be supported under another exact compatible.

