# Multi-agent instruction compatibility

The repo has **one common policy** in `AGENTS.md`. Native entry points point to that file; no tool gets independent, contradictory policy.

| Product | Checked-in entry point | Notes |
|---|---|---|
| OpenAI Codex | `AGENTS.md` | Project instructions; user must explicitly provide the main/review role. |
| OpenCode | `AGENTS.md` | OpenCode recognizes repository `AGENTS.md`. |
| Claude Code | `CLAUDE.md` | Uses `@AGENTS.md` import to include canonical policy. |
| Gemini CLI | `GEMINI.md` | Short entry point asks agent to read `AGENTS.md`. |
| Google Antigravity | `AGENTS.md` and `GEMINI.md` | Workspace discovery varies by app/CLI version; keep both files consistent. |
| Cursor | `.cursor/rules/repository.mdc` | Always-applied rule points to canonical policy. |
| GitHub Copilot | `.github/copilot-instructions.md` | Repository custom instructions point to canonical policy. |

**Verification:** `python scripts/doctor.py` validates file presence and local tools, but cannot prove a cloud product actually loaded or obeyed a rule. At onboarding, prompt each agent: **"Which repository instruction files did you load? Summarize the three most important constraints and the active task owner."** If it cannot answer accurately, explicitly attach `AGENTS.md` and the role prompt before development.

Some clients may load both root `AGENTS.md` and `GEMINI.md`: the latter contains no new policy, minimizing contradictions.

## Skills

The repository includes 89 distinct installed skill snapshots under `.agents/skills/<name>/SKILL.md`, with supporting resources and available licenses. See the [catalog](../.agents/skills/README.md) and [manifest](../.agents/skills/manifest.json). Identical installations are deduplicated; differing versions are retained with a source prefix. This snapshot covers local shared, Codex (including system skills), and Claude (including synced skill bundles) directories; plugin caches and personal settings are not exported.

A teammate whose client does not discover the shared directory can explicitly point it to a catalog entry’s committed SKILL.md. No global installation or absolute symlink is required to read a skill. Tool-specific scripts or connected services may still need separate setup; copied instructions do not provide credentials or tools. Keep personal settings and later personal installs local.

## Remote agent requirements

- Launch both main and reviewer agents in **separate cloud workspaces/branches**, not one mutable checkout.
- Grant GitHub/repo access through the agent provider's supported integration or authenticated CLI. Instruction files cannot grant access.
- If an agent lacks repo or PR write permissions, it should produce review findings and a patch/PR plan rather than pretending to have merged.
- Keep the reviewer independently tasked via `prompts/REVIEW_AGENT.md` / `prompts/REVIEW_ALL_PRS.md`.
- Never assume different agent sessions automatically share memory; durable decisions live in tracked `docs/` and task cards.

Official references: [Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex), [Claude Code](https://code.claude.com/docs/en/memory), [OpenCode](https://opencode.ai/docs/instructions), [OpenCode skills](https://opencode.ai/docs/skills), [Antigravity](https://antigravity.google/docs/rules/), [Cursor](https://docs.cursor.com/context/rules-for-ai), [Copilot](https://docs.github.com/en/copilot/concepts/prompting-and-context/custom-instructions).

