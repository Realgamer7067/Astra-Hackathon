# DTS, binding and driver tracing

Treat DT as a hardware description consumed through a documented ABI, not a configuration language for trial-and-error numbers.

## Bidirectional trace

Trace forward:

~~~text
target component/topology
→ board node and parent bus
→ compatible and binding
→ driver match data
→ probe path
→ provider dependencies
→ subsystem registration
→ firmware/userspace-visible result
~~~

Trace backward from the earliest log/error to the exact return path and missing provider. Both traces should meet at a source line and evidence-backed DT fact.

## Step 1 — establish the effective DT

Record:

- source DTS/DTSI/overlay include chain;
- compiler/preprocessor inputs;
- base DTB and DTBO location;
- board/SKU/panel selection;
- bootloader fixups and chosen node/command line;
- running FDT versus build artifact;
- exact kernel commit and DT build ID.

The source file being edited may not be the DTB the bootloader selected. Compare source, packaged and running trees where possible.

## Step 2 — read the binding as ABI

Find the exact schema under Documentation/devicetree/bindings. Record compatible fallback ordering; required and conditional properties; cell counts/order; units; provider phandles; child-bus rules; additional/unevaluated property constraints; and examples.

Binding examples demonstrate schema shape, not the target’s addresses, IRQs, voltages or timing. If no upstream binding exists, stop before adding an undocumented board node and research whether a binding/driver series is pending.

## Step 3 — prove driver reachability

Trace:

- of_device_id or other match table;
- Kconfig dependencies/selects and Makefile object;
- built-in versus module and initramfs availability;
- bus enumeration and parent status;
- probe sequence and each resource acquisition;
- runtime-PM/genpd/IOMMU setup;
- firmware requests and subsystem registration;
- error/defer paths.

A compatible in a binding but absent from driver match data may be intentional, pending, or a different driver architecture.

## Step 4 — recursively trace providers

For every phandle/cell pair, verify the provider exists, its binding matches, the specifier is valid for the exact revision, its driver is enabled and it probed.

| Dependency | Evidence to capture |
|---|---|
| regulators | rail identity, target supply, voltage constraints, enable GPIO/PMIC topology |
| clocks | provider, ID, parents/rates if required, enable order |
| resets | provider, index/name, assertion semantics |
| pinctrl/GPIO | controller, physical pad/group, mux, bias, drive, active state |
| interrupts | controller, cells, trigger/polarity, wake role |
| power domains | provider/index and parent hierarchy |
| interconnect | endpoints/path and performance dependency |
| IOMMU | stream/context IDs and reserved mappings |
| reserved memory | target-proven address/size/alignment/no-map/reusable semantics |
| phys | exact PHY lane/port and provider |
| firmware/remoteproc | filename, loader, secure handoff, carveouts and IPC |

Never fabricate specifiers by analogy. Downstream numeric indices can differ from upstream dt-binding headers.

## Step 5 — semantic downstream translation

Build a translation table:

| Downstream node/property/API | Behavior or hardware fact | Upstream binding/driver equivalent | Not transferable | Evidence/confidence |
|---|---|---|---|---|

Classify vendor properties as:

- true physical description;
- parameter derived from a datasheet;
- Android policy/tuning;
- downstream framework glue;
- debug/bypass workaround;
- unexplained magic;
- obsolete because upstream models it differently.

Do not translate property names without tracing both consumers.

## Subsystem traces

### Display

Verify DPU/display engine, IOMMU, interconnect, power domain, PHY, host, graph endpoints/ports, bridge/panel, backlight, supplies, reset/TE, lanes, pixel format, command/video mode, DSC and handoff. Inspect every component’s probe separately before editing panel properties.

### Storage

Trace controller → PHY → clocks/resets → regulators → interconnect/IOMMU → block layer. Rootfs failure comes later; do not conflate it with controller probe.

### USB/Type-C

Trace controller → PHY → glue driver → role switch/connector → Type-C/PD/extcon → VBUS → gadget/host userspace.

### Audio

Trace CPU DAI/platform → DSP/remoteproc/IPC → codec/amp → sound card graph/machine driver → topology → UCM/userspace.

### Camera

Trace each sensor/EEPROM/actuator/flash → regulators/clocks/GPIO → CSI PHY/lane map → receiver/ISP/IOMMU → media graph → libcamera/userspace.

## Validation ladder

1. DTS builds without new errors.
2. Binding and DT schema checks pass for affected files.
3. Effective DT contains the intended exact node/property.
4. Provider and consumer probe logs are observed.
5. Subsystem object appears.
6. Minimal functional test passes.
7. Runtime PM and suspend/resume do not regress.

Each rung proves only itself. Schema-valid DTS may still describe the wrong board.

