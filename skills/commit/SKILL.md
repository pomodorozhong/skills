---
name: commit
description: Create atomic Conventional Commits while preserving unrelated work and checking branch safety. Use whenever preparing or making a commit.
---

# Commit

## 1. Branch safety

- Before each commit and immediately before pushing, confirm the current and default branches and check the PR status with the hosting service when available. Local merge checks can miss squash merges.
- Reuse a suitable active feature branch or create one. Never commit or push new work directly to `main`, `master`, or the repository's default branch.
- If the branch's PR has merged or closed, start a fresh branch from the updated default branch and carry over the intended work, preserving unrelated changes and existing history.

## 2. Survey and split the changes

Run `git status --short`, `git diff --stat`, and read the full diff, including untracked files. Leave out anything that should not be committed: scratch output, build output, secrets, or local machine files. Ask the user if unsure.

If the changes do one thing, make one commit with only the files that belong to it. If they mix several things, split them into atomic commits:

- One commit = one reason to change: a feature, a fix, a refactor, a docs update. Its tests and docs go in the same commit.
- Order commits so each one builds and passes tests on its own. Backend or library pieces usually go before the UI that uses them, and docs that describe the result go last.
- Split a file across commits when its hunks belong to different units. Do not split so finely that a commit is broken or meaningless; when code is too entangled to separate cleanly, keep it in one commit and say why in the body.

## 3. Write Conventional Commit messages

```
<type>(<scope>): <summary>

<body: what changed and why>
```

- Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`. Use `!` after the scope plus a `BREAKING CHANGE:` footer for breaking changes.
- Scope: optional; the area touched, following the existing history (`git log --oneline -20`).
- Summary: imperative mood, lowercase, no trailing period, at most ~72 characters.
- Body: explain the reason and the user-visible effect, not a file list. Reference issues as `#N` where relevant. Optional for trivial changes.

## 4. Verify

Run the project's checks if it documents them (in its README, `AGENTS.md`, or `CLAUDE.md`). Skip suites the change cannot affect and say so.

- One commit: run the checks on the working tree before committing.
- Several commits: check each one on its own in a temporary detached worktree in the scratchpad, then remove the worktree. Reuse installed dependency folders only when they match the tested commit's dependency manifests and lockfiles; otherwise install that commit's dependencies. If a commit fails on its own, fix the split (only unpushed commits may be rewritten) and re-check.

## 5. Push and cleanup

- Push only when authorized by the user, and push the feature branch, never `main` or `master`. A push request does not authorize creating a PR or merging.
- If the branch's PR has merged since the commits were made, move the new commits to a fresh branch from the up-to-date default branch with `git cherry-pick`, and push that branch instead.
- After a successful push, delete a local branch retired during this work only when all of its work is merged or preserved on the pushed branch.

## 6. Report

Report the new commit hashes and subjects, verification results, and whether the work was pushed.
