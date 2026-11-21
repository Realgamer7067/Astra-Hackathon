# Firmware, remote processors and userspace boundaries

“The driver exists” is not “the feature works.” Mobile subsystems often cross kernel, signed firmware, trusted firmware, calibration, IPC and userspace layers.

## Boundary map

| Feature | Kernel-side pieces | Non-kernel dependencies | Frequent false conclusion |
|---|---|---|---|
| Wi-Fi/BT | bus, power sequence, rfkill, radio driver | firmware, board/NVRAM, calibration, regulatory DB | compatible chipset means radio works |
| Modem | remoteproc/MHI, IPC, WWAN/net | signed modem firmware, secure loader, SIM services, ModemManager/ofono | firmware boot means calls/data work |
| Audio | ASoC, codec/amp, DSP IPC | DSP firmware/topology, UCM, mixer policy, calibration | codec probe means audio is complete |
| Camera | sensor/CSI/ISP/media graph | ISP firmware, calibration, libcamera pipeline | vendor HAL success maps to V4L2 |
| Sensors | IIO/input or hub transport | hub firmware, calibration, transforms | Android sensor name identifies a bus device |
| GPU | DRM/GPU, IOMMU, clocks/devfreq | firmware and Mesa/userspace driver | display output means acceleration |
| Fingerprint/NFC | bus/subsystem driver | TEE/trustlet, secure element, proprietary protocol | bus response means usable support |

## Research sequence

1. Identify whether the component is AP-controlled, remoteprocessor-controlled or TEE-mediated.
2. Trace upstream match data and firmware request paths.
3. Record exact firmware names only from source/logs, then map them to lawful shipped packages.
4. Trace reserved memory, IOMMU, secure monitor calls, clocks/regulators and IPC.
5. Determine whether firmware is signed, relocatable, board-calibrated, version-coupled or bootloader-loaded.
6. Identify userspace requirements such as ALSA UCM, Mesa, libcamera, ModemManager/ofono, BlueZ, wpa_supplicant/iwd, PipeWire or sensor services.
7. Report redistributability separately from technical availability.

For concepts, start at https://docs.kernel.org/staging/remoteproc.html and then read the exact target-revision drivers and bindings.

## Evidence rules

- A firmware name in vendor DTS is a lead; confirm which driver requests it.
- A blob in a firmware release proves availability there, not compatibility elsewhere.
- A remote processor marked running does not prove IPC endpoints or clients.
- Android HAL code may document topology but is not an upstream driver.
- Missing-firmware errors may be secondary to wrong compatible, board ID, remoteproc state or search path.

Record filename, source build/package, hash when lawful, license, consumer, load stage, board coupling and runtime evidence. Never publish keys, secrets, unique calibration identities or personally identifying modem data.

