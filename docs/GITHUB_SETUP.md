# GitHub setup — owner checklist

The template is a ZIP, **not an already-created hosted repository**. You or your main agent must perform these steps after choosing the repo/account. Do not supply credentials in chat.

1. Create a GitHub repository (public/private based on event rules) and commit the starter tree.
2. Invite all four teammates as collaborators. Give the review agent a suitable, separately authenticated identity/integration **only if allowed**.
3. Enable PRs into `main` and prevent direct pushes. Configure a branch protection rule or repository ruleset:
   - Require a pull request before merging.
   - Require at least one **non-author** approval from a teammate/authorized reviewer.
   - Require passing `Repository health / verify` CI (check exact displayed name after its first run).
   - Dismiss stale approvals on code changes; protect against force-pushes/deletions.
   - Do not configure an administrator bypass for AI agents.
4. Use squash merges and optionally auto-delete merged branches; enable only after the rule is working.
5. Ensure GitHub Actions can read the repository. There is no paid AI reviewing job; the review agent is user-invoked.
6. Add app-specific checks in `project-checks.json` **before adding app source**.
7. Verify the gate using a tiny test PR: a failing check should block merging; a passing check plus required non-author review should permit merging.

**Identity detail:** Two AI agents sharing your GitHub identity are not two separate GitHub reviewers; GitHub forbids author self-approval. The review agent may still analyze, comment, request code changes, and merge PRs if actual GitHub branch protection rules are satisfied. A human teammate can provide the required separate approval.

**Permitted merge command for reviewer, after thorough review and checks:**

```bash
gh pr checks <PR_NUMBER> --required
gh pr merge <PR_NUMBER> --squash --delete-branch --match-head-commit <VERIFIED_HEAD_SHA>
```

Or use `python scripts/merge_checked.py <PR_NUMBER>` for a conservative dry-run, followed by `python scripts/merge_checked.py <PR_NUMBER> --execute --reviewed-sha <VERIFIED_HEAD_SHA>` to perform the merge after independent review.

Do not use `--admin` or `--auto` to hide an outstanding review problem. `--match-head-commit` prevents merging a PR that changed since review. A rejected PR stays open with explicit requested changes and a reason.

Official docs: [branch protection](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches), [PR reviews](https://docs.github.com/en/pull-requests/how-tos/review-pull-requests/reviewing-proposed-changes-in-a-pull-request), [gh pr merge](https://cli.github.com/manual/gh_pr_merge).

