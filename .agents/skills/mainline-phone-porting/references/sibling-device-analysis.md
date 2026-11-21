# Sibling-device analysis

A sibling is useful only for a documented shared dependency. Same SoC, chassis, product family or Android codename style is not enough.

## Choose candidates by the question

| Feature being studied | Useful shared anchor |
|---|---|
| SoC foundations | exact SoC/revision, PMIC topology, reference-board lineage |
| Display | exact DPU/PHY generation plus panel/bridge family and topology |
| Touch | exact controller/revision, bus, supplies and firmware |
| Charging | exact charger/PMIC, Type-C/PD controller and battery topology |
| Audio | exact codec/amp/DSP path and board routing |
| Wi-Fi/BT | exact radio/module, bus, board/calibration format |
| Camera | exact sensor/ISP/CSI PHY and lane topology |
| Boot | exact bootloader generation, image format and board-ID selection |

A board can be a good sibling for one feature and irrelevant for another.

## Comparison workflow

1. State the proposed shared dependency.
2. Prove it independently on target and candidate.
3. Compare binding and driver revision, not just compatible spelling.
4. Diff provider graphs: supplies, clocks, resets, pinctrl, IRQ, power domain, interconnect, IOMMU, reserved memory and firmware.
5. Compare bootloader ownership/handoff and userspace dependencies.
6. Identify every board-specific value.
7. Decide whether the sibling offers architecture, node shape, a candidate hypothesis, or truly transferable data.

## Mandatory table

| Candidate | Feature | Shared dependency | Target proof | Candidate proof | Material differences | Transferable concept | Values that must not be copied | Confidence |
|---|---|---|---|---|---|---|---|---|

## Anti-copy-paste gate

Before adapting a DTS node, answer:

- Is the exact compatible documented for the target?
- Are address and bus instance verified?
- Are IRQ controller, number and trigger verified?
- Are every supply and voltage constraint verified?
- Are clocks/resets and indices defined by the same provider ABI?
- Are pinctrl groups for the target pads?
- Are lane count, timings, mode flags and graph endpoints target-derived?
- Are firmware, calibration and reserved-memory relationships equivalent?
- Does bootloader handoff differ?
- What test will detect wrong wiring without persistent damage?

If any required value is Unknown, use the sibling only to guide further research. Never preserve a magic number merely because it boots another phone.

## Beware false families

- OEMs can ship several panels/touch controllers under one retail model.
- Reference designs expose components that production phones omit or reroute.
- Carrier variants can change NFC/RF/charging and board revision.
- Same SoC may pair with different PMICs or PMIC subtypes.
- A later board may use the same component with different voltage, IRQ or firmware.
- Community trees often inherit one another, so apparent agreement may be a single copied source.

