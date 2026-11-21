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

Install team skills under `.agents/skills/<name>/SKILL.md` and commit them when ready. Keep personal skills in the ignored tool-specific directories. A teammate whose client does not discover a shared skill can point it directly to the committed file.

## Remote agent requirements

- Launch both main and reviewer agents in **separate cloud workspaces/branches**, not one mutable checkout.
- Grant GitHub/repo access through the agent provider's supported integration or authenticated CLI. Instruction files cannot grant access.
- If an agent lacks repo or PR write permissions, it should produce review findings and a patch/PR plan rather than pretending to have merged.
- Keep the reviewer independently tasked via `prompts/REVIEW_AGENT.md` / `prompts/REVIEW_ALL_PRS.md`.
- Never assume different agent sessions automatically share memory; durable decisions live in tracked `docs/` and task cards.

Official references: [Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex), [Claude Code](https://code.claude.com/docs/en/memory), [OpenCode](https://opencode.ai/docs/instructions), [OpenCode skills](https://opencode.ai/docs/skills), [Antigravity](https://antigravity.google/docs/rules/), [Cursor](https://docs.cursor.com/context/rules-for-ai), [Copilot](https://docs.github.com/en/copilot/concepts/prompting-and-context/custom-instructions).

