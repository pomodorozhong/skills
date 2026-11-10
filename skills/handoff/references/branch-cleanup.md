# Branch cleanup

Every wrap-up sorts the local branches, deletes the stale ones that are safe to lose, and asks once about the rest. [Step 4 of the skill](../SKILL.md#4-clean-up-branches) says what needs approval.

Do not use `git branch --merged`. A squash merge puts a branch's changes on the default branch as one new commit, so the branch never looks merged to Git.

## 1. Refresh

- `git fetch --prune`, so remote-tracking branches deleted on GitHub disappear.
- `git worktree prune`, so worktrees whose folders are gone stop holding their branches.
- If the default branch is not checked out in any worktree, fast-forward it: `git fetch origin <default>:<default>`. Git refuses this when the update is not a fast-forward; then leave the branch alone and report it.

## 2. Protected branches

Never delete, and skip from the sort below:

- the current branch and the default branch;
- a branch with an open PR;
- a branch named in `HANDOFF.md`'s In progress section;
- a branch checked out in any worktree (`git worktree list --porcelain`).

## 3. Sort every other local branch

Check the classes in this order and take the first that fits. `<default>` is the default branch after step 1.

- **Merged:** a PR from the branch was merged (`gh pr list --state merged --head <branch> --json number,headRefOid,mergeCommit`). If the branch tip equals the PR's `headRefOid`, it is merged. If the tip differs, compare it with the squash commit: `git diff --quiet <mergeCommit> <branch> -- . ':!HANDOFF.md'`. No difference means merged; any difference means the branch gained work after the merge, so treat it as unique work.
- **Handoff-only:** every commit past the default branch (`git log <default>..<branch> --name-only`) touches only `HANDOFF.md` or files in `<docs>/`, and no In progress subsection refers to the branch.
- **Superseded:** the branch's tree matches the default branch or a branch that survives this cleanup, ignoring `HANDOFF.md` (`git diff --quiet <other> <branch> -- . ':!HANDOFF.md'`). This is typical of `backup/*` and `temp/*` branches left by a rebuild.
- **Closed without merging:** a PR from the branch was closed without merging. Always ask; the user may want to reopen it.
- **Unique work:** anything else. Keep it and list it with its commits past the default branch, so the user can decide.

Without GitHub, only Handoff-only and Superseded can be decided. Keep the other branches and say they were not checked.

## 4. Delete and record

- Before deleting, record each branch as `name sha` (`git rev-parse <branch>`). Delete with `git branch -D <branch>`, since Git cannot see squash merges and `-d` would refuse.
- Report each deleted branch as `name sha`. Restore one with `git branch <name> <sha>`.
- Remote branches: for each deleted local branch whose remote branch still exists, and for remote-only branches that sort the same way, propose `git push origin --delete <branch>`. This needs approval, together with the closed and unique branches, in one list.

## 5. Worktrees

List worktrees whose folders still exist and that belong to other sessions or another checkout, with their path, branch, and whether they have uncommitted changes. Never remove them; another session may still be using one.

## Stop stale remote branches at the source

GitHub can delete a PR's head branch when the PR merges: **Settings → General → Pull Requests → Automatically delete head branches**, or `gh repo edit --delete-branch-on-merge`. When it is off, merged branches stay on the remote until someone deletes them. Suggest turning it on when cleanup finds merged remote branches; changing it is a repository setting and needs the user's approval.
