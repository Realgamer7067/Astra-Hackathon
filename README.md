# ASTRA Orbital Collision Lab

Explore source-backed orbital estimates, construct explicitly hypothetical collisions, replay simulated debris and inspect bounded orbital exposure.

**Status: planning complete; application not implemented.** No app startup, scientific validation, UI or performance claim is available yet.

Start with [four-person execution plan](docs/PLAN.md), [project brief](docs/PROJECT_BRIEF.md), [architecture](docs/ARCHITECTURE.md), [contracts](docs/CONTRACTS.md), and the [task board](tasks/README.md). The full supplied [master specification](docs/ASTRA_MASTER_PROMPT.md) is preserved; specialized details live in [physics](docs/PHYSICS.md), [data sources](docs/DATA_SOURCES.md), [UX](docs/UX.md), and [limitations](docs/LIMITATIONS.md).

First deliverable is TASK-001: runnable token-free globe, API, typed fixtures and real project checks. Four lanes then deliver catalog explorer, collision runner, globe/replay and exposure/reporting. You + main agent take collision runner (TASK-003), foundation and coordination; catalog explorer is proposed for Teammate 2. Names and merged claims remain pending. See [demo and freeze](docs/DEMO.md).

Educational research simulation. Catalog positions are estimates; collision scenarios and impact trajectories are hypothetical unless explicitly stated otherwise. Not for spacecraft operations or emergency decisions.

## Starter tooling and collaboration reference

The following describes the inherited starter workflow. ASTRA’s selected concept and baseline stack are recorded above; instructions about choosing them at kickoff apply to future reuse of the starter.

# Four-person hackathon starter

For the 24-hour space hackathon on November 21–22. The team chooses the problem and stack at kickoff and builds the submission from scratch. Libraries can be selected then.

## Before the event

Extract the ZIP. Commit the contents of the inner folder, including dotfiles, to your team repository. Invite the other three developers and follow the [GitHub setup checklist](docs/GITHUB_SETUP.md). Each teammate clones the repo and runs the setup command from its root.

| Arch Linux | Windows PowerShell |
|---|---|
| `bash scripts/setup.sh` | `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1` |

## At kickoff

| Who | First action | Hand off when |
|---|---|---|
| You and your main coding agent | Give the agent the official brief, rubric and [kickoff prompt](prompts/KICKOFF.md). Approve the proposed MVP and demo path. | Contracts, runnable checks and four first tasks are ready. |
| All four developers, including you | Pick one feature each. The coordinator can put all four agreed claims in one PR. Once merged, branch from updated main and use the [implementation instructions](AGENTS.md). | The feature PR includes its card, acceptance evidence and check results. |
| Separate reviewer | When invited, use [review all PRs](prompts/REVIEW_ALL_PRS.md). Review dependencies first and record the commit inspected for each PR. | Report what merged, what needs changes and who owns each follow-up. |
| Team at freeze | Follow the [demo rehearsal](prompts/FREEZE_AND_DEMO.md) with the same inputs and device you plan to show the judges. | One person can run the full demo and another can run the backup. |

See the [team workflow](docs/WORKFLOW.md) for claim conflicts, shared files and integration checkpoints.

## Agent support

| Agent / editor | Repo entry point |
|---|---|
| Codex / OpenCode | `AGENTS.md` |
| Claude Code | `CLAUDE.md` |
| Gemini CLI | `GEMINI.md` |
| Google Antigravity | `AGENTS.md` / `GEMINI.md` |
| Cursor | `.cursor/rules/repository.mdc` |
| GitHub Copilot | `.github/copilot-instructions.md` |

These adapters direct agents to the **same canonical guidance**, not seven independent rulebooks. Loading behavior and supported features vary by product and version; follow [compatibility notes](docs/TOOL_COMPATIBILITY.md). **Instruction files cannot force a cloud agent to run continuously or grant it GitHub permissions.**

## Commands

```bash
python scripts/doctor.py           # local tools, paths and optional local skills
python scripts/tasks.py list       # available task cards
python scripts/repo_health.py      # validate templates, task cards, repository rules
python scripts/run_project_checks.py  # execute configured app-specific checks, when present
```

After choosing a stack, create `project-checks.json` from [project-checks.example.json](project-checks.example.json). **Adding application code before configuring the checks will make CI fail deliberately.**

## Shared skills

Add your chosen team skills to `.agents/skills/` and commit them when ready. Personal tool-specific installations stay local. See the [skills guide](docs/TOOL_COMPATIBILITY.md#skills).
