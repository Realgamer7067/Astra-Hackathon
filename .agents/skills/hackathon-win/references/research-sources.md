# Research Sources and Adopted Patterns

This file documents sources studied during skill creation. The skill synthesizes behavioral patterns; it does not copy source code or substantial prose from these materials.

## Agent skills and workflow systems

- [Agent Skills specification](https://agentskills.io/specification) — standard directory/frontmatter constraints, focused references, progressive disclosure, and script expectations.
- [OpenAI: Build skills](https://learn.chatgpt.com/docs/build-skills) — concise activation metadata, progressive loading, repository/user skill scope, and optional UI metadata.
- [Anthropic Agent Skills documentation](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) — filesystem-based skills, on-demand references, deterministic scripts, and third-party skill security.
- [Anthropic public skills repository](https://github.com/anthropics/skills) — representative modular skill structures and licensing boundaries.
- [Anthropic frontend-design skill](https://github.com/anthropics/skills/blob/main/skills/frontend-design/SKILL.md) — subject-specific visual direction, restraint, screenshot critique, and clarity-oriented interface writing. Consulted for patterns only; no source text or assets copied.
- [Anthropic webapp-testing skill](https://github.com/anthropics/skills/blob/main/skills/webapp-testing/SKILL.md) — black-box helpers, help-first usage, and rendered-state reconnaissance before automation. Consulted for patterns only; no code copied.
- [GitHub Copilot custom agents](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-custom-agents) and [cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent) — repository research/planning, specialized workstreams, scoped agent profiles, commits/logs as durable evidence, and tool/MCP configuration.
- [Windsurf/Devin workflows](https://docs.devin.ai/desktop/cascade/workflows) — reusable trajectory-level workflows, workspace scope, and explicit ordered steps.

## Tool discovery, UI verification, and evaluation

- [Model Context Protocol architecture](https://modelcontextprotocol.io/docs/learn/architecture) — discover capabilities/tools dynamically before invocation and tolerate changing availability.
- [Playwright visual comparisons](https://playwright.dev/docs/test-snapshots) and [Trace Viewer](https://playwright.dev/docs/trace-viewer) — real screenshot checks, deterministic baselines, action/network/console inspection, and failure traces.
- [OpenAI evaluation best practices](https://developers.openai.com/api/docs/guides/evaluation-best-practices) — task-specific eval objectives, early/continuous evaluation, pairwise or pass/fail judgments, and typical plus adversarial cases.

## Hackathon judging and rules

- [MLH Hackathon Organizer Guide](https://guide.mlh.com/) — organizer-side judging/submission perspective and the need to understand how projects are reviewed.
- [ETHGlobal rules](https://ethglobal.com/rules) — eligibility, pre-existing-work disclosure, version-control provenance, partner technology licensing, and submission deadlines.
- [NASA Space Apps judging and awards guide](https://www.spaceappschallenge.org/resources/judging-awards-guide/) — example of global criteria/award structures and event-specific judging material.
- [Microsoft Imagine Cup](https://imaginecup.microsoft.com/) — official example of a competition emphasizing innovation, validation, acceleration, impact, and finalist storytelling.
- [Devpost Build Session: How to Win the All Things Agentic Hackathon](https://www.youtube.com/watch?v=DCXjvKmUIGY) — organizer/judge briefing example where README, architecture, and constrained demo-video evidence are explicit judging surfaces.
- [TAIKAI hackathon judging criteria](https://taikai.network/en/blog/hackathon-judging-criteria) — organizer-platform synthesis of recurring innovation, technical execution, functional MVP, impact, and presentation criteria.

## Resulting design choices

- Compact `SKILL.md` plus shallow routed references.
- Capability mapping rather than assumed MCP names.
- Repository and deadline verification before strategy.
- Rubric evidence and observable checkpoints rather than generic encouragement.
- Black-box, dependency-light scripts with help output.
- Separate Golden Path, wow, failure fallback, and submission-safety controls.
- Scenario and adversarial validation with decision-level expectations.
