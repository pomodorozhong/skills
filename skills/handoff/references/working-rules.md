# Handoff working rules

The short block in [the AGENTS.md template](../assets/agents-handoff.md) holds the rules every session follows on every task. These are the details for specific moments: starting on a branch, creating one, editing `HANDOFF.md`, and resolving a conflict in it.

## Approval requests

Each request has a stable ID (`P-01`), the proposed action and scope, why approval is needed, and what it blocks. Requests that belong to a branch, such as a push or PR, go in its subsection; others, such as issue drafts, go under `Pending`.

## Start of a session

- To resume an issue from another computer, find its branch with `gh issue develop --list <N>`, fetch it, and read that branch's `HANDOFF.md`. Preserve local changes when switching checkouts.
- When comparing the code checkpoint with `git log`, list the commits made after it, skipping the branch's own `docs:` commits that only touch `HANDOFF.md` or the docs folder.
- Verify issue and PR status when GitHub is available; the AGENTS.md block covers commits on a merged or closed branch. A subsection whose PR has merged or closed is stale: remove it in your next `docs:` commit, moving anything unresolved to the issue or to `Pending`.
- Handle only the approvals the chosen action needs, and continue other authorized work.

## Creating a branch

- Create each work branch from its primary issue: `gh issue develop <N> --name <type>/<summary> --base <default branch> --checkout` (or `--worktree <path>`). This creates the branch on GitHub at once, so it needs the same authorization as a push; without it, create the branch locally and link it when pushing is approved. If the work has no issue yet, create the branch locally, add an issue draft to its subsection's pending requests, and link the branch once the issue is filed. The PR may close other issues too; list each with `Closes #N`.
- Link a branch to an issue only when its PR will fully resolve that issue: when the PR merges, GitHub closes every issue linked to its branch, even if the body says `Related to #N`. A branch that only advances an issue, or only carries a handoff, is created locally and stays unlinked.
- With no work branch, commit `HANDOFF.md` on the next task's branch, created as above.

## Editing `HANDOFF.md`

- Keep subsections in alphabetical order. Remove subsections whose PR has merged or closed.
- The branch subsection records: task and issue, PR, code checkpoint, observed state, verification run and results, one concrete next action, and when useful: checks not run, approaches to avoid, and pending IDs with what they block. Describe unmerged work as awaiting review or merge.
- History and decisions belong on the issue; lasting knowledge belongs in the docs folder. Never write local paths containing personal IDs.

## Resolving a conflict

On a rebase conflict in `HANDOFF.md`, keep the incoming version of this branch's subsection and the base's version of everything else.
