# Scoped readiness and response modes

Select one primary mode. Combine modes only when the request genuinely crosses boundaries. A narrow question does not inherit whole-device research obligations, but it does inherit every transitive dependency and safety boundary relevant to that question.

## Universal rules

Every substantive answer states:

- goal and explicit scope boundary;
- evidence with confidence labels and exact revisions/artifacts;
- material unknowns and contradictions;
- assessment;
- smallest justified next step;
- validation, failure signal and proof boundary;
- risk and rollback when an action changes state.

Use `not applicable` only with a reason. Use `unavailable` when the evidence source should exist but cannot be obtained. Use `unknown` when the claim cannot be established. Never upgrade Unknown to Plausible merely to complete a gate.

## Mode A — whole-device feasibility/support landscape

Use for “can this device be mainlined?”, a new device, or a requested complete landscape.

Required output: goal; full identity/variant matrix; hardware inventory; upstream/linux-next/lore landscape; vendor and shipped-artifact archaeology; ecosystem ports; justified siblings; whole-device dependency/support matrix; boot/recovery boundary; assessment; readiness; phased next steps; risks; research backlog.

Readiness:

~~~text
- Device/variant identity: verified / incomplete / unknown
- Whole-device hardware inventory: verified / incomplete / unknown
- Upstream, linux-next and relevant lore mapped: yes / no
- Matching vendor/source artifacts analysed: yes / no / unavailable
- Ecosystem ports inspected at source level: yes / no / not found
- Meaningful siblings justified: yes / no / not applicable
- Boot/recovery boundary: verified / incomplete / unknown
- Feature dependencies mapped: yes / no
- Recommendation confidence: verified / strongly supported / plausible / unknown
~~~

## Mode B — one feature, DTS node, binding or driver

Scope to the requested consumer, exact board variant, and its transitive providers: bus, clocks, resets, regulators, pinctrl, IRQ, power domain, interconnect, IOMMU, reserved memory, firmware and userspace. Do not inventory unrelated subsystems.

Required output: goal/scope; relevant identity facts; evidence table; current binding/driver/support; dependency chain and earliest blocker; verified/unknown values; assessment; scoped readiness; smallest change/test; expected log; failure signal; rollback/proof boundary.

Readiness:

~~~text
- Exact board/subsystem identity: verified / incomplete / unknown
- Consumer and provider evidence: verified / incomplete / unknown
- Current binding/driver/pending work mapped: yes / no / not applicable
- Relevant vendor/target evidence analysed: yes / no / unavailable / not applicable
- Transitive dependencies mapped: yes / no
- Board-specific values directly evidenced: yes / no / not applicable
- Safe minimal validation: yes / no
- Recommendation confidence: verified / strongly supported / plausible / unknown
~~~

## Mode C — debugging a failure

Begin with the observation, not a patch. Separate last known-good state, exact changed variable, running artifact identity, complete unfiltered log window and competing hypotheses.

Required output: symptom and baseline; evidence timeline; verified artifact/build marker; hypothesis table with discriminators; dependency slice; assessment; smallest one-variable experiment; expected positive/negative results; stop condition; recovery.

Readiness asks whether the observed artifact is identified, the log is complete enough, baseline/delta are known, hypotheses are falsifiable, and the experiment is safe. Upstream landscape or vendor archaeology may be `not applicable` unless the failure depends on them.

## Mode D — commit/patch archaeology

Required output: repositories/refs searched; author identity caveats; candidate table; series/base/parents; dependencies; current upstream equivalent; lore disposition; per-item applicability classification; missing evidence; next inspection/test. Device hardware inventory and flash readiness are normally `not applicable`.

Readiness asks whether repository history is complete, the patch base/series is identified, current upstream was compared, dependencies/review disposition are known, and exact-device relevance is established where claimed.

## Mode E — build or artifact construction

Required output: source revision and dirty snapshot; build family; architecture/boot artifact; config origin; resolved toolchain; exact command; fresh/reused output status; pre/post artifact evidence; validation result; what compilation does not prove. Do not require a hardware inventory unless choosing board-specific targets depends on it.

Readiness asks whether source/config/architecture/target names are verified, dirty evidence is preserved, output reuse is explicit, required tools resolve, and the produced format has a non-device validation method.

## Mode F — flashing, bootloader or persistent device mutation

Use the command-presentation contract in [flashing-tools.md](flashing-tools.md). Required output includes exact device/serial, mode, tool version, artifact hash/type, physical/logical partition and slot, authorization/lock state, expected response, running-artifact verification, failure stop, recovery and data-loss/non-boot risk.

No mutating command is ready while any of device identity, target partition/slot, artifact format, bootloader acceptance, recovery path or user confirmation is Unknown/missing. `not applicable` is not valid for these fields when performing a write.
