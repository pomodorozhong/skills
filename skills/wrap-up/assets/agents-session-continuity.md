## Session continuity

### Start of a session

- Follow the user's selected task and identify its branch or PR. When choosing new work, start with the default branch's `.agents/next-steps.md` and follow its issue or PR references to in-progress branches. Do not guess based on which branch was pushed most recently.
- On the selected branch, read `.agents/next-steps.md` and relevant entries in `.agents/pending.md` if present. On another computer, fetch the identified remote branch when available before inspecting its files. Preserve local changes when selecting a checkout; an unpushed handoff is available only on its originating computer.
- Compare the recorded code checkpoint and state with the actual checkout and working tree. Verify issue and PR status when GitHub is available, and reassess verification made stale by intervening changes. If the PR has merged or closed, apply the `commit` skill's branch-safety rules before new commits or pushes.
- Apply available user authorization and handle only approvals needed for the chosen action. A pending entry records a request, not approval. Continue independent authorized work. If no task was assigned, propose the highest-priority unblocked item.

### During work

- Refresh the resume point and relevant pending requests after a substantial work chunk, decision, or blocker, and before switching tasks or pushing. Record the observed state and a concrete next action; identify uncommitted files when relevant. These file updates do not require a separate commit every time.
- Keep the handoff current instead of accumulating a session log. Detailed work history belongs on the issue; lasting knowledge belongs in the project's docs folder. Keep enough local context to resume when GitHub is unavailable.

### End of a session

- Use the `wrap-up` skill to finalize the handoff, resolve relevant pending requests, checkpoint intended changes, and report what is committed, uncommitted, and retrievable on another computer. Push only within the user's authorization.
