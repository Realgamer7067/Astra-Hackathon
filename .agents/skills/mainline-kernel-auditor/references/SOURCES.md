# Starting points: primary standards and official kernel docs

Use these as **research entry points**, not substitutes for checking documentation actually inside the target source revision. These URLs are starting points, not a certification of availability or current applicability. Open them when needed and pin the actual versions used.

- Agent Skills specification (packaging): https://agentskills.io/specification
- Linux kernel patch submission checklist: https://docs.kernel.org/process/submit-checklist.html
- Linux submitting patches: https://docs.kernel.org/process/submitting-patches.html
- Linux kernel coding style: https://docs.kernel.org/process/coding-style.html
- Linux kernel testing guide: https://docs.kernel.org/dev-tools/testing-overview.html
- Linux Devicetree usage model: https://docs.kernel.org/devicetree/usage-model.html
- DT schema authoring/testing: https://docs.kernel.org/devicetree/bindings/writing-schema.html
- DT binding design do/don't: https://docs.kernel.org/devicetree/bindings/writing-bindings.html
- DT ABI/stable bindings: https://docs.kernel.org/devicetree/bindings/ABI.html (or pinned equivalent)
- Driver model and probe/defer: https://docs.kernel.org/driver-api/driver-model/driver.html
- Kernel testing overview: https://docs.kernel.org/dev-tools/testing-overview.html
- Maintainer lists and responsibilities: https://docs.kernel.org/process/maintainers.html
- Kernel ABI and internal API distinction: https://docs.kernel.org/process/stable-api-nonsense.html
- Kernel upstream source browsing: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/
- Linux kernel mailing list archives: https://lore.kernel.org/
- Kernel patch tracker: https://patchwork.kernel.org/
- Devicetree schema source: https://github.com/devicetree-org/dt-schema
- Samsung open source release center: https://opensource.samsung.com/

## Review queries for this port

Look up actual board and exact peripheral variant before trusting results; use targeted searches such as:

- `site:lore.kernel.org Exynos9610 <subsystem> <compatible> binding`
- `site:git.kernel.org exynos9610 <controller> <register>`
- `"<exact compatible string>" "bindings"`
- `"<exact vendor driver function>" mainline linux`
- `site:docs.kernel.org <driver subsystem> probe remove runtime pm`
- `"<pin name>" "<board revision>" Samsung kernel`

For each result, read the actual patch discussion or source and record revisions. Prefer merged final code over an abandoned RFC. Do not assert that any particular Galaxy A50 Samsung release/vendor repo has been located until verified.

- Codex skill format and discovery: https://learn.chatgpt.com/docs/build-skills
- Codex execution permissions: https://learn.chatgpt.com/docs/agent-approvals-security
- Git configuration (fsmonitor, diff drivers and filters): https://git-scm.com/docs/git-config
