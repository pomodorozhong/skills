---
name: commit
description: Create atomic Conventional Commits while preserving unrelated work and checking branch safety. Use whenever preparing or making a commit.
---

# Commit

## Branch safety

- Before each commit and immediately before pushing, confirm the current and default branches and check the PR status with the hosting service when available. Local merge checks can miss squash merges.
- Reuse a suitable active feature branch or create one. Never commit or push new work directly to `main`, `master`, or the repository's default branch.
- If the branch's PR has merged or closed, start a fresh branch from the updated default branch and carry over the intended work, preserving unrelated changes and existing history.

## Commits

- Review tracked and untracked changes. Stage only the intended work and inspect the staged diff before each commit.
- Split independent changes into atomic commits, keeping relevant tests and documentation with the change they support. Each commit should stand on its own.
- Use Conventional Commit messages (`<type>(<scope>): <summary>`) following repository conventions. Keep the subject concise; add a body when it helps explain the reason or resulting behavior.

## Verification

Before committing, run checks relevant to the changes. For split commits, verify each independently using checks appropriate to its contents. Report failures and skipped checks.

## Push and cleanup

- Push only when authorized by the user. A push request does not authorize creating a PR or merging.
- After a successful push, delete a local branch retired during this work only when all of its work is merged or preserved on the pushed branch.

Report the new commit hashes and subjects, verification results, and whether the work was pushed.
