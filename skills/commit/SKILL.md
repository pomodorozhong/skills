---
name: commit
description: Commit changes in any git repo as atomic Conventional Commits. Use whenever you are about to run `git commit` (including "commit this", "commit after each step", "make atomic commits", "split into commits", or finishing a task that should be committed), and as the last step of wrap-up. Never commits on main or master, or on a branch whose PR already merged — it checks out or creates a feature branch first.
---

# Commit

Follow these steps every time, before every `git commit`.

## 1. Never commit on the default branch or a finished branch

Check the current branch:

```bash
git branch --show-current
```

If it is `main` or `master` (or the repo's default branch, from `git symbolic-ref --short refs/remotes/origin/HEAD`), do not commit there:

- If a branch for this work already exists (this session created one, or the user named one), check it out: `git switch <branch>`. Uncommitted changes carry over.
- Otherwise create one from the current state: `git switch -c <branch>`.

Otherwise, check that the branch is still open. A PR can merge at any point in the session, and `git branch --merged` misses squash merges, so ask GitHub:

```bash
gh pr list --head <branch> --state all --json number,state --jq '.[] | "#\(.number) \(.state)"'
```

If its PR is `MERGED` or `CLOSED`, commits there would never land. Start a new branch from the up-to-date default branch instead: `git fetch origin && git switch -c <new-branch> origin/<default>`. Uncommitted changes carry over; on a conflict, stash them first and pop them on the new branch. Then delete the finished local branch (`git branch -D <branch>`) once nothing on it is unmerged. With no GitHub remote, use `git branch --merged origin/<default>` instead.

Branch names: `<type>/<short-kebab-summary>`, using the same type as the commit (`feat/wishlist-per-profile`, `fix/pinch-zoom-tiles`, `docs/ui-redesign-plan`). For a multi-step task, use one branch for the whole task, not one per step.

After switching, confirm with `git branch --show-current` before committing.

## 2. Survey and split the changes

Run `git status --short`, `git diff --stat`, and read the full diff, including untracked files. Leave out anything that should not be committed: scratch output, build output, secrets, or local machine files. Ask the user if unsure.

If the changes do one thing, make one commit with only the files that belong to it. If they mix several things, split them into atomic commits:

- One commit = one reason to change: a feature, a fix, a refactor, a docs update. Its tests and docs go in the same commit.
- Order commits so each one builds and passes tests on its own. Backend or library pieces usually go before the UI that uses them, and docs that describe the result go last.
- Split a file across commits when its hunks belong to different units. Do not split so finely that a commit is broken or meaningless; when code is too entangled to separate cleanly, keep it in one commit and say why in the body.

Partial staging without interactive `git add -p`:

- Hunks: take `git diff -- <file>`, keep the wanted hunks, and apply them with `git apply --cached --recount -`.
- Lines inside one hunk: write the intermediate file version to the scratchpad, then `git update-index --cacheinfo 100644,$(git hash-object -w <tmp-file>),<path>`.

Check `git diff --cached --stat` before each commit.

## 3. Write Conventional Commit messages

```
<type>(<scope>): <summary>

<body: what changed and why>

<trailers>
```

- Types: `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `build`, `ci`, `chore`. Use `!` after the scope plus a `BREAKING CHANGE:` footer for breaking changes.
- Scope: optional; the area touched, following the existing history (`git log --oneline -20`).
- Summary: imperative mood, lowercase, no trailing period, at most ~72 characters.
- Body: explain the reason and the user-visible effect, not a file list. Reference issues as `#N` where relevant. Optional for trivial changes.

## 4. Verify

Run the project's checks if it documents them (in its README, `AGENTS.md`, or `CLAUDE.md`). Skip suites the change cannot affect and say so.

- One commit: run the checks on the working tree before committing.
- Several commits: check each one on its own in a temporary detached worktree in the scratchpad, then remove the worktree. Symlink installed dependency folders (such as `node_modules`) into it rather than reinstalling. If a commit fails on its own, fix the split (only unpushed commits may be rewritten) and re-check.

## 5. Pushing

Push only when the user asks, and push the feature branch (`git push -u origin <branch>`), never `main` or `master`. If the user asks to push "without a PR", push the branch and stop; don't merge it into the default branch unless they say so.

Right before pushing, or before handing the user a push command, repeat step 1's merged check. If the branch's PR has merged since the commits were made, move the new commits to a fresh branch from the up-to-date default branch with `git cherry-pick`, and push that branch instead.

## 6. Report

List the new commits (`git log --oneline`) with one line each on what they contain, and the verification result.
