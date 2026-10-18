<!-- handoff:start (from the handoff skill; edit the skill's template, not this copy) -->
## Handoff

`HANDOFF.md` at the repository root is how sessions resume. It has three sections: `In progress` (one `### <branch>` subsection per active branch, holding its state and its own approval requests), `Ranked work`, and `Pending` (approval requests not tied to a branch). A pending entry, such as `P-01`, records a request, not approval.

- **Start of a session:** read `HANDOFF.md` and the subsection named after `git branch --show-current`; no subsection means nothing is in progress on this branch. Compare its code checkpoint with `git log`, re-check verification that later commits may have made stale, and run the project's documented checks before building on it. If this branch's PR has merged or closed, apply the `commit` skill's branch-safety rules before new commits or pushes. To pick new work, start from the default branch's `Ranked work`.
- **Edit only this branch's subsection,** plus `Ranked work` and `Pending` when they actually change. Keep it current rather than a log, and never write secrets.
- **Commit `HANDOFF.md`** only before a push and at wrap-up, as a `docs:` commit on the work branch. Never commit it on the default branch.
- **PRs:** use the `open-pr` skill. **End of a session:** use the `handoff` skill.
- **Before creating a branch, editing `HANDOFF.md`, or resolving a conflict in it,** read the `handoff` skill's working rules (`references/working-rules.md` in that skill).
<!-- handoff:end -->
