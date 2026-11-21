# Hardware/provenance investigation guide (Galaxy A50 / Exynos 9610 focus)

**Device context supplied by user:** Samsung Galaxy A50 (SM-A505 family), Exynos 9610, mainline-derived kernel with display/DSI, Wi-Fi, CPU frequency, touchscreen, and desktop work. This is starting context only; verify the actual checkout, booted board variant, and peripheral identification. The historical kernel string `7.3.0-rc1-next-20260904` is **not** an asserted current version or base SHA.

## Find authoritative sources without guessing

1. Locate target kernel repository and branches; run non-mutating `git log`, `git remote -v`, `git show`, `git grep`, `git diff`. Do not automatically fetch or merge; request permission for network operations that mutate local refs (can use web/remote source browsing instead).
2. Locate OEM device source and exact tag/commit plus OEM `.config`, DTS/DTSI, board files, headers and binaries. Search Samsung opensource release packages and any relevant vendor repositories; do not silently assume the release matches this SM-A505 variant.
3. Extract hardware identity **from authorized existing evidence**: `/proc/device-tree/compatible`, board compatible, boot log, `uname -a`, `.config`, regulator/clk summaries, bus IDs, known PMIC, Wi-Fi chip ID, firmware name, display panel, touchscreen controller. Never infer every Galaxy A50 uses identical vendor ICs.
4. For every driver replacement or copied constant trace: (a) vendor source declaration, (b) silicon / component documentation if available, (c) target upstream subsystem expected input, (d) observed board behavior, (e) electrical/firmware trust boundaries. Mark unavailable datasheets explicitly.
5. Search **other accepted upstream Exynos drivers** and discussion/patch revisions relevant to the IP; confirm the SoC generation/IP revision and compare registers before reuse. Search mailing list critiques and bindings; design rationale may explain why a vendor approach was rejected.
6. Search all local `compatible` strings and their schema constraints. Device model/binding should describe reality, including properties of hardware not yet supported by driver when needed, not mirror a code workaround.

## Specific cross-checks

**Display / DSI / DRM:** panel exact ID/revision, reset sequence and timings, DSI lane count, pixel format, polarity, mode clocks/porches, supplies and enable order, bridge topology, regulator and backlight consumer relationships, atomic modeset, framebuffer handling, IOMMU/DMA, suspend/resume and error unwinding. A lit panel is not proof correct timing or power-down.

**Wi-Fi:** ascertain SDIO vs alternative bus and chip variant from verified source; regulator and reset/pwrseq topology, pinmux, interrupts and wake, firmware+NVRAM version/provenance, MAC identity without exposing private values, interface naming and rfkill, regulatory enforcement, power save, resume, AP/P2P if supported, coexistence with BT and shared clocks/rails. Compare upstream driver capabilities against vendor bcmdhd or other chip-specific driver **only if device IDs prove applicability**. Do not copy Android-specific rfkill or MAC workarounds without proof. Ensure unintended bus devices/DT nodes are not instantiated.

**CPU / clocks / DVFS:** OPP tables and voltage support, clock and PLL parents, thermal throttling, CPU topology/cluster identity, SCMI/firmware versus kernel-controlled clocks, regulator ownership, hardware speed-bin fuses and correct selection, transitions/failure rollback, cpuidle and energy behavior. Never treat observed maximum clocks as evidence all OPP entries are electrically safe.

**Touchscreen:** real controller ID and bus, regulators, GPIO reset/IRQ polarity, coordinate mapping, rotation/inversion ownership (DT vs compositor), gesture wake, firmware update security, I2C transaction failures, IRQ storm and suspend handling. Separate driver errors from userspace input transformations.

**USB / storage / battery / audio / GPU / cameras / modem:** independently identify hardware and ABI. Pay special attention to secure firmware hand-off, shared rails, IOMMU memory maps and explicit exclusion of inaccessible protected devices. Do not enable missing functionality solely by importing a vendor DT node.

## `status = "okay"` review

For each enabled hardware node, establish the physical block, ownership and applicable wiring/power requirements. Classify logical, virtual, bus and provider nodes by their bindings; do not reject them merely because they have no separate physical consumer. Check overlapping `reg` ranges, IRQ claims, aliases and labels, clocks/resets, DMA routes, reserved memory, IOMMU ownership, address and size cells, sleeping context, power domain references and constraints. Check parent bus enabled; child absence; bootloader-created overlays; schema-required properties; binding compatible ordering and fallbacks.

## Required vendor vs upstream table

| Hardware property / operation | Exact vendor evidence | Exact upstream/DT contract | Actual port | Board evidence | Verdict / uncertainty |
|---|---|---|---|---|---|
| Controller identity and revision | SHA + line | SHA + binding | path:line | IDs | |
| MMIO/register bit/offset | register/table | driver/spec | path:line | measurement | |
| IRQ/clock/regulator/power | vendor DT | binding/provider | DT:line | logs | |
| PM/error behavior | source function | upstream API | function | tests | |
| Exposed Linux ABI/permissions | vendor user APIs | documented Linux ABI | path:line | ls/getfacl | |

Never let a blank authoritative-evidence cell silently become a PASS.
