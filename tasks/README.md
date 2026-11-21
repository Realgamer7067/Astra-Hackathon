# Markdown task marketplace

This directory is the team's **Git-native task board**, not a GitHub Issues board. Status = directory; one card per task. Card format is `tasks/_TEMPLATE.md`.

Commands:

```bash
python scripts/tasks.py list
python scripts/tasks.py new TASK-001 --title "User onboarding"

# Fill the new card with a concrete outcome and acceptance criteria first.
python scripts/tasks.py move TASK-001 --to ready
python scripts/tasks.py claim TASK-001 --owner alice
python scripts/tasks.py move TASK-001 --to review
# After the feature PR merges, record the PR reference in the card.
python scripts/tasks.py move TASK-001 --to done
```

The `new` command writes an **incomplete skeleton**. The main agent must fill its acceptance criteria and scope before promoting it to ready. All new cards start in `planned/`; use `move TASK-001 --to ready` after the plan and dependencies are approved.

**Claim safely:** pull current main, verify card is still ready, move one task card to active with your name, open a small claim PR and get it merged. Or have the coordinator batch all team claims. Do not treat an unmerged local claim as authoritative; competing claims must be resolved before implementation.

Task IDs are unique across all directories. Move cards to `done` only after their PR merges and is verified.

