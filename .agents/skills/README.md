# Shared installed skills

Snapshots of the installed Codex, Claude and shared skill bundles. Identical copies are deduplicated; differing versions use a source prefix. Supporting files and available licenses are preserved. No personal agent settings, memory exports, sessions, credentials or sync bookkeeping are included.

## Use after cloning

Start with repository AGENTS.md and your role prompt. Use only skills relevant to the task. If your client does not discover `.agents/skills`, explicitly ask it to read the linked SKILL.md below. This catalog provides access; it does not guarantee automatic discovery in every client.

Some skills require specific agent tools, connected services, local packages, fonts or external credentials. Copying a skill does not install those dependencies or grant tool access. Do not execute bundled scripts merely to validate this catalog. Repository and user instructions take precedence.

Source labels: shared = shared local install, codex = Codex local install, claude = Claude local install. These labels do not identify upstream authors. See each bundle for attribution/license terms; absence of a license file is not a grant of unrestricted reuse.

The manifest records snapshot hashes, file counts and source labels. Source-specific bundled skills (including system and synced skills) are included as requested, without enclosing per-user sync state.

## Catalog

| Skill bundle | Installed in | Files |
|---|---|---|
| [agent-browser](agent-browser/SKILL.md) | shared | 1 |
| [banner-design](banner-design/SKILL.md) | claude | 2 |
| [brainstorming](brainstorming/SKILL.md) | shared | 8 |
| [brand](brand/SKILL.md) | claude | 18 |
| [brandkit](brandkit/SKILL.md) | claude, shared | 1 |
| [cavecrew](cavecrew/SKILL.md) | shared | 2 |
| [caveman](caveman/SKILL.md) | shared | 2 |
| [caveman-commit](caveman-commit/SKILL.md) | shared | 2 |
| [caveman-compress](caveman-compress/SKILL.md) | shared | 10 |
| [caveman-discover](caveman-discover/SKILL.md) | shared | 1 |
| [caveman-evidence-review](caveman-evidence-review/SKILL.md) | shared | 1 |
| [caveman-explore](caveman-explore/SKILL.md) | shared | 3 |
| [caveman-help](caveman-help/SKILL.md) | shared | 2 |
| [caveman-learn](caveman-learn/SKILL.md) | shared | 6 |
| [caveman-manage](caveman-manage/SKILL.md) | shared | 1 |
| [caveman-optimize](caveman-optimize/SKILL.md) | shared | 1 |
| [caveman-review](caveman-review/SKILL.md) | shared | 2 |
| [caveman-setup](caveman-setup/SKILL.md) | shared | 1 |
| [caveman-stats](caveman-stats/SKILL.md) | shared | 2 |
| [claude-skill-creator](claude-skill-creator/SKILL.md) | claude | 18 |
| [create-statusline](create-statusline/SKILL.md) | codex | 4 |
| [design](design/SKILL.md) | claude | 35 |
| [design-mobile-apps](design-mobile-apps/SKILL.md) | shared | 7 |
| [design-system](design-system/SKILL.md) | claude | 27 |
| [design-taste-frontend](design-taste-frontend/SKILL.md) | claude, shared | 38 |
| [design-taste-frontend-v1](design-taste-frontend-v1/SKILL.md) | claude, shared | 1 |
| [diagnosing-superpowers](diagnosing-superpowers/SKILL.md) | shared | 20 |
| [dispatching-parallel-agents](dispatching-parallel-agents/SKILL.md) | shared | 1 |
| [docs](docs/SKILL.md) | claude | 1 |
| [docx](docx/SKILL.md) | claude | 61 |
| [domain-modeling](domain-modeling/SKILL.md) | shared | 4 |
| [executing-plans](executing-plans/SKILL.md) | shared | 3 |
| [find-skills](find-skills/SKILL.md) | shared | 1 |
| [finishing-a-development-branch](finishing-a-development-branch/SKILL.md) | shared | 1 |
| [frontend-design](frontend-design/SKILL.md) | shared | 2 |
| [full-output-enforcement](full-output-enforcement/SKILL.md) | claude, shared | 1 |
| [gpt-taste](gpt-taste/SKILL.md) | claude, shared | 1 |
| [grill-me](grill-me/SKILL.md) | shared | 2 |
| [grill-with-docs](grill-with-docs/SKILL.md) | shared | 2 |
| [grilling](grilling/SKILL.md) | shared | 2 |
| [hackathon-win](hackathon-win/SKILL.md) | claude, codex, shared | 42 |
| [high-end-visual-design](high-end-visual-design/SKILL.md) | claude, shared | 1 |
| [hyperframes](hyperframes/SKILL.md) | shared | 78 |
| [hyperframes-cli](hyperframes-cli/SKILL.md) | shared | 13 |
| [image-to-code](image-to-code/SKILL.md) | claude, shared | 1 |
| [imagegen](imagegen/SKILL.md) | codex | 12 |
| [imagegen-frontend-mobile](imagegen-frontend-mobile/SKILL.md) | claude, shared | 1 |
| [imagegen-frontend-web](imagegen-frontend-web/SKILL.md) | claude, shared | 1 |
| [import-memory](import-memory/SKILL.md) | claude | 1 |
| [improve-codebase-architecture](improve-codebase-architecture/SKILL.md) | shared | 3 |
| [industrial-brutalist-ui](industrial-brutalist-ui/SKILL.md) | claude, shared | 1 |
| [investigate-first](investigate-first/SKILL.md) | shared | 2 |
| [lean-build](lean-build/SKILL.md) | shared | 2 |
| [mainline-kernel-auditor](mainline-kernel-auditor/SKILL.md) | codex | 16 |
| [mainline-phone-porting](mainline-phone-porting/SKILL.md) | claude, codex | 32 |
| [media-use](media-use/SKILL.md) | shared | 122 |
| [migration](migration/SKILL.md) | shared | 2 |
| [minimalist-ui](minimalist-ui/SKILL.md) | claude, shared | 1 |
| [morning](morning/SKILL.md) | claude | 3 |
| [openai-docs](openai-docs/SKILL.md) | codex | 17 |
| [pdf](pdf/SKILL.md) | claude | 12 |
| [playwright-cli](playwright-cli/SKILL.md) | claude | 11 |
| [pptx](pptx/SKILL.md) | claude | 58 |
| [receiving-code-review](receiving-code-review/SKILL.md) | shared | 1 |
| [reddit-automation](reddit-automation/SKILL.md) | shared | 1 |
| [redesign-existing-projects](redesign-existing-projects/SKILL.md) | claude, shared | 1 |
| [requesting-code-review](requesting-code-review/SKILL.md) | shared | 2 |
| [reverse-engineer-anything](reverse-engineer-anything/SKILL.md) | claude | 7 |
| [review-agent](review-agent/SKILL.md) | codex | 2 |
| [safe-refactor](safe-refactor/SKILL.md) | shared | 2 |
| [skill-creator](skill-creator/SKILL.md) | codex | 9 |
| [skill-installer](skill-installer/SKILL.md) | codex | 8 |
| [slides](slides/SKILL.md) | claude | 6 |
| [stitch-design-taste](stitch-design-taste/SKILL.md) | claude, shared | 2 |
| [subagent-driven-development](subagent-driven-development/SKILL.md) | shared | 7 |
| [surgical-patch](surgical-patch/SKILL.md) | shared | 2 |
| [systematic-debugging](systematic-debugging/SKILL.md) | shared | 11 |
| [test-driven-development](test-driven-development/SKILL.md) | shared | 2 |
| [ui-styling](ui-styling/SKILL.md) | claude | 16 |
| [ui-ux-pro-max](ui-ux-pro-max/SKILL.md) | claude | 68 |
| [using-git-worktrees](using-git-worktrees/SKILL.md) | shared | 1 |
| [using-superpowers](using-superpowers/SKILL.md) | shared | 8 |
| [vercel-react-best-practices](vercel-react-best-practices/SKILL.md) | shared | 75 |
| [verification-before-completion](verification-before-completion/SKILL.md) | shared | 1 |
| [verify-and-stop](verify-and-stop/SKILL.md) | shared | 2 |
| [web-design-guidelines](web-design-guidelines/SKILL.md) | claude, shared | 1 |
| [writing-plans](writing-plans/SKILL.md) | shared | 1 |
| [writing-skills](writing-skills/SKILL.md) | shared | 7 |
| [xlsx](xlsx/SKILL.md) | claude | 53 |
