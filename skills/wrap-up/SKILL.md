---
name: wrap-up
description: Preserve agent session continuity with issue handoff notes, a concrete resume point and ranked work in .agents/next-steps.md, pending approvals in .agents/pending.md, durable docs, and verified Git checkpoints. Use when the user says "wrap up", "let's stop here", "end the session", or similar.
---

# Wrap up

Leave the project so the next session can resume without this conversation. GitHub issues hold work details and history; `.agents/next-steps.md` holds the current resume point and ranked work; `.agents/pending.md` holds specific requests awaiting approval. Lasting knowledge goes in the docs folder.

**Docs folder:** use `docs/`, unless the repo already has a `doc/` folder; then use `doc/` and do not create `docs/`. Below, `<docs>` means that folder.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure. Skip remote updates that cannot run, but still save a local resume point, ranked work, and pending requests. Include enough local context to resume without opening an issue, and identify any issue updates still to post.

## 1. Review the session

Go back over the conversation and the diff since the session started, and list:

- **Done:** what changed, with commit hashes once committed, and which issues it covers.
- **Decided:** choices the user made, and why.
- **Learned:** facts found along the way (constraints, pitfalls, results).
- **Open:** anything unresolved, unclear, or half-finished, including questions the user did not answer.

Inspect the working tree, including untracked source files. Identify which session changes are committed, uncommitted, or available remotely; a saved handoff file does not preserve unsaved source work.

## 2. Update the issues

- **Issues worked on:** comment on each with what the next session needs: what was done, what was tried and failed, what is left. Decisions the user made go on the issue they belong to. Remove `needs-decision` once its questions are answered. Comments on these issues need no approval.
- **New work found** (bugs, ideas, follow-ups, unanswered questions): draft an issue for each, with a title, labels, milestone and a body that stands alone. Label open questions `needs-decision`. Drafts awaiting approval go to `.agents/pending.md` (step 5). Apply existing user authorization when available.
- **Half-finished work:** record the branch, any PR, and what remains in the issue handoff and local resume point, even if the branch is unpushed. Park a push or draft PR request only when the required authorization is missing.
- **Dependencies:** when one issue can't start before another, record it on the issue ("Blocked by #N").
- **Milestones:** each milestone's description says what it is for, what it waits on and why, and when it is done. If the session changed the order between milestones, update the affected descriptions. If a milestone has no open issues left, close it within existing authorization or park the closure request in `.agents/pending.md`.

Never put local paths with personal IDs (such as a Steam ID) in an issue or comment.

## 3. Maintain `.agents/next-steps.md`

Put a compact `Resume` block before the ranked list. Record the active task, branch and PR when present, last relevant code commit, actual state, verification commands and observed results, and one concrete next action. Include checks not run and why, a failed approach worth avoiding, and relevant pending-item IDs when useful. Omit fields that do not apply.

```markdown
# Next steps

## Resume

- Task: #11 Clarify import review wording
- Branch: codex/import-review
- Code checkpoint: <last relevant code commit>
- State: wording changed; regression test still needed
- Verification: `npm test -- import-review` passed; integration tests not run
- Next action: add a regression test for an unchanged import
- Avoid repeating: changing the label alone missed the empty-result case
- Pending: P-02 in pending.md blocks pushing only

## Ranked work

1. #11 Finish the regression test and review
2. #8 Decide the redesign direction (blocks #9–#15)
3. #1 First run on the real data folder (shows which stops need a region, before #12)
```

- Describe the observed state. Say "implemented; awaiting review/merge" for unmerged work. Do not write the file as though the PR has already merged.
- Keep the ranked list to one line per issue or local task, with an optional short reason. Drop closed or completed items, add new ones, and re-order by priority. Put blocking decisions before dependent work; keep unrelated unblocked work visible.
- Replace stale resume context instead of accumulating a session log. Detailed history belongs on the issue; order between milestones belongs in their descriptions. If no task is in progress, say so and identify the next unblocked task.
- Refresh the resume point and relevant pending requests after a substantial work chunk, decision, or blocker, and before switching tasks or wrapping up. These file checkpoints do not require a separate commit every time.

## 4. Move long-term knowledge into `<docs>/`

Durable knowledge goes in `<docs>/`: architecture, decisions and their reasons, workflow assumptions, gotchas, and user-facing behavior (`README.md`).

- Update the existing doc that covers the topic; create a new one only when none fits, and link it from the folder's index (`<docs>/README.md`), creating the index if needed.
- Fix any doc statements that this session made stale.

## 5. Maintain `.agents/pending.md`

Read the current file on the selected task's branch and preserve unresolved requests. Keep it separate from the ranked work so full drafts do not obscure the next action.

- Give each request a stable ID such as `P-02`; keep that ID while it remains unresolved. Record the proposed action, its scope, why approval is needed, and exactly what it blocks. Include issue drafts in full; identify the branch and intended changes for pushes or PRs.
- Apply available user authorization without asking again for the same scope. A pending entry is a request, not evidence of approval. If authorization is unavailable or the action exceeds its approved scope, obtain approval before that action.
- Approved: perform the action and remove the entry after success. If it fails, retain the entry with the failure and next action. Rejected: remove it. Unanswered: keep it. Preserve resulting decisions in the relevant issue or durable doc.
- A request blocks only the dependent action. Continue independent, authorized work; do not make all pending requests a prerequisite for starting a session.
- Save additions and resolutions through ordinary file edits and commits. Do not require a special commit message, a parking branch, a rebase, or a force push to manage this file. Clearly marked pending proposals may remain when a PR merges.

Use `# Pending` as the heading and omit resolved entries from the current file. Git retains their history. If no requests remain, an existing file may say "None"; do not create an empty file just for the wrap-up.

## 6. Make sure `AGENTS.md` supports resuming

Read [the session-continuity template](assets/agents-session-continuity.md) and the project's root `AGENTS.md` when present. The template supplies the reusable startup, checkpoint, and session-end instructions.

- If `AGENTS.md` is missing, create it with the template's section.
- Otherwise, reconcile the relevant existing instructions with the template. Update equivalent sections in place instead of appending duplicate rules, and remove superseded continuity instructions that conflict with the revision.
- Preserve unrelated guidance and explicit project preferences; adapt the section names and placement to the existing document. Copy the applicable text into the project so its instructions travel with the repository.
- Check for relevant template changes on each wrap-up. If the project's instructions already provide the same behavior, leave the file untouched. Repeated runs should not add sections or churn wording.
- Include any resulting `AGENTS.md` change in the normal save step below.

## 7. Save, verify, and report

- Use the `commit` skill to checkpoint the session's intended source and handoff changes on a suitable feature branch. Preserve unrelated work. Include relevant source changes in appropriate atomic commits; use `docs:` for handoff-only updates to `.agents/next-steps.md`, `.agents/pending.md`, `<docs>/`, and `AGENTS.md`. Commit only when there are changes, whether or not a branch was created this session. After any branch-safety move, refresh the resume branch and relevant code checkpoint before saving the handoff.
- If unfinished source changes remain uncommitted, record the files and what remains to make a checkpoint in the resume block, and report them. Do not imply that committing the handoff also saved those changes in Git. Keep enough resume context to find any work that exists only locally.
- Push only within the user's existing authorization; otherwise keep the scoped push request in `.agents/pending.md`. Creating a PR needs its own authorization. Do not automatically open a PR just for handoff docs. Pushing a handoff commit on a feature branch also publishes its preceding unpushed commits; it cannot sync only the handoff files.
- Before reporting, inspect the final working tree and confirm which commits were pushed. Distinguish committed local work, uncommitted work, and work retrievable on another computer. Report any remaining local changes after resolving pending actions too.
- Use the reply template below. Ask about relevant requests that still need approval unless the user said they have to go; resolve their answers using step 5 and save the resulting file updates normally.

## Final reply template

Before writing the final wrap-up reply, read and fill in [the reply template](assets/wrap-up-reply.md). This plain Markdown asset is shared by Codex and Claude Code.

- For session task bullets, use a past-tense verb and a task type in Title Case for each bold label, such as `Filed Issue`, `Updated PR`, `Posted Handoff Notes`, or `Committed Changes`. Repeat task bullets as needed.
- Make every issue and PR mention a Markdown link, including repeated mentions and items under `Next`. Link directly to the comment when reporting a handoff note.
- Keep task details concise and include relevant commit hashes and parked-item status. Report decisions or unresolved questions as task bullets, such as `Recorded Decision` or `Raised Clarification`, when relevant; omit empty categories.
- Give commits their own `## Commits` section between `## In this session we...` and `## Next`. List exactly one commit per Markdown bullet/line, with its short hash, subject, and concise purpose. Never combine multiple commits into one line. If no commits were made, use one line: `No commits were made.`
- Include `## Handoff` with the explicit resume branch, saved-state and push status, any uncommitted work, and pending IDs with their scope and blockers. State when another computer cannot retrieve some work yet. Omit empty optional entries.
- List the next 2–4 concrete tasks in priority order, with one line per bullet. If fewer exist, list only those; if none remain, say so in a single bullet.
