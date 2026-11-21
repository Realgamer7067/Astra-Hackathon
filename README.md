# ASTRA Orbital Collision Lab

Explore source-backed orbital estimates, construct explicitly hypothetical collisions, replay simulated debris and inspect bounded orbital exposure.

**Status: TASK-001 foundation.** The local app includes a Cesium globe and a 12-object synthetic snapshot. Live catalog ingestion, collision physics, replay and exposure analysis are feature tasks.

Start with [four-person execution plan](docs/PLAN.md), [project brief](docs/PROJECT_BRIEF.md), [architecture](docs/ARCHITECTURE.md), [contracts](docs/CONTRACTS.md), and the [task board](tasks/README.md). The full supplied [master specification](docs/ASTRA_MASTER_PROMPT.md) is preserved; specialized details live in [physics](docs/PHYSICS.md), [data sources](docs/DATA_SOURCES.md), [UX](docs/UX.md), and [limitations](docs/LIMITATIONS.md).

Four lanes deliver catalog explorer, collision runner, globe/replay and exposure/reporting. The coordinator owns TASK-001 and has reserved TASK-003 for collision work. See [demo and freeze](docs/DEMO.md).

Educational research simulation. Catalog positions are estimates; collision scenarios and impact trajectories are hypothetical unless explicitly stated otherwise. Not for spacecraft operations or emergency decisions.

## Run the foundation locally

Install Node.js 24, Python 3.12 and `uv`. From the repository root, install the locked dependencies once:

```bash
uv sync --locked --python 3.12
npm ci --no-audit
```

In two terminals at the repository root:

```bash
# Terminal 1 — API
uv run --locked uvicorn --app-dir services/api app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — web
npm run dev -- --strictPort
```

Open `http://127.0.0.1:5173`. The globe, imagery and fixture data are served locally, including when the internet is unavailable after dependency installation. Select a demo object to highlight its marker and inspect its example position. The API serves `/health`, `/api/v1/demo` and `/docs` at port 8000. The dev server proxies API requests to that port.

Run `python scripts/repo_health.py`, `python -m unittest discover -s tests`, and `python scripts/run_project_checks.py`. The security check uses the npm registry. For the production web output, run `npm run build` and serve `apps/web/dist` with `/api/` and `/health` routed to FastAPI.

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

The installed Codex, Claude and shared skills are now bundled in [.agents/skills/README.md](.agents/skills/README.md): 89 distinct bundles, with identical installations deduplicated and differing versions retained. Personal tool settings, credentials and sessions stay local. See the [skills guide](docs/TOOL_COMPATIBILITY.md#skills).
