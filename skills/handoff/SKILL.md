---
name: handoff
description: Keep a project's HANDOFF.md current so any session, worktree, or computer can resume work, with issue handoff notes, ranked work, pending approvals, durable docs, and verified Git checkpoints. Use when the user says "wrap up", "let's stop here", "end the session", "hand off", or similar, and when the user accepts a branch's work before its PR merges.
---

# Handoff

Leave the project so the next session can resume without this conversation. `HANDOFF.md` at the repository root holds the resume point for each active branch, the ranked work, and pending approval requests. GitHub issues hold work details and history. Lasting knowledge goes in the docs folder.

The rules for `HANDOFF.md` that every session follows live in [the AGENTS.md template](assets/agents-handoff.md); read it first. This skill adds the end-of-session and before-merge procedures. [An example `HANDOFF.md`](assets/HANDOFF.md) shows the format.

**Docs folder:** use `docs/`, unless the repo already has a `doc/` folder; then use `doc/` and do not create `docs/`. Below, `<docs>` means that folder.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure. Skip remote updates that cannot run, but still update `HANDOFF.md`. Include enough context there to resume without opening an issue, and list the issue updates still to post.

## 1. Review the session

Go back over the conversation and the diff since the session started, and list:

- **Done:** what changed, with commit hashes once committed, and which issues it covers.
- **Decided:** choices the user made, and why.
- **Learned:** facts found along the way (constraints, pitfalls, results).
- **Open:** anything unresolved, unclear, or half-finished, including questions the user did not answer.

Inspect the working tree, including untracked source files. Identify which session changes are committed, uncommitted, or available remotely; a saved `HANDOFF.md` does not preserve unsaved source work.

## 2. Update the issues

- **Issues worked on:** comment on each with what the next session needs: what was done, what was tried and failed, what is left. Decisions the user made go on the issue they belong to. Remove `needs-decision` once its questions are answered. Comments on these issues need no approval.
- **Branch link:** make sure each work branch is linked to its primary issue (`gh issue develop --list <N>`). If it is not, say so in the comment and name the branch.
- **New work found** (bugs, ideas, follow-ups, unanswered questions): draft an issue for each, with a title, labels, milestone and a body that stands alone. Label open questions `needs-decision`. Apply existing user authorization when available; otherwise add the draft to `Pending` (step 3).
- **Dependencies:** when one issue can't start before another, record it on the issue ("Blocked by #N").
- **Milestones:** each milestone's description says what it is for, what it waits on and why, and when it is done. If the session changed the order between milestones, update the affected descriptions. If a milestone has no open issues left, close it within existing authorization or add the closure request to `Pending`.

Never put secrets or local paths containing personal IDs in an issue or comment.

## 3. Update `HANDOFF.md`

Create it from the example's headings if it is missing. If `.agents/next-steps.md` or `.agents/pending.md` exist from the older workflow, move their content into the matching sections, delete them, and delete `.agents/` if nothing else is in it.

- **This branch's subsection:** replace it with the current state, following the template's field list. Replace stale content instead of adding to it. On the default branch with no work branch, there is no subsection; see step 7.
- **Ranked work:** one line per issue or local task, with an optional short reason. Drop closed items, add new ones, and re-order only when priorities changed. Put blocking decisions before dependent work; keep unrelated unblocked work visible. If nothing is in progress, the top item is the next task.
- **Pending:** give each request a stable ID (`P-01`), kept while it is unresolved. Record the proposed action, its scope, why approval is needed, and exactly what it blocks. Include issue drafts in full. Requests that belong to this branch, such as a push or PR, go in its subsection; others go under `Pending`.
- **Resolve requests:** apply available authorization without asking again for the same scope. Approved: perform the action and remove the entry after success; if it fails, keep it with the failure and next action. Rejected: remove it. Unanswered: keep it. Record resulting decisions on the relevant issue or in `<docs>/`.
- **Cleanup:** remove subsections of other branches whose PR has merged or closed.

## 4. Move long-term knowledge into `<docs>/`

Durable knowledge goes in `<docs>/`: architecture, decisions and their reasons, workflow assumptions, gotchas, and user-facing behavior (`README.md`).

- Update the existing doc that covers the topic; create a new one only when none fits, and link it from the folder's index (`<docs>/README.md`), creating the index if needed.
- Fix any doc statements that this session made stale.

## 5. Keep `AGENTS.md` in sync

Read [the AGENTS.md template](assets/agents-handoff.md) and the project's root `AGENTS.md`.

- If `AGENTS.md` is missing, create it with the template, including its `handoff` start and end markers.
- If the markers are present, replace everything between them with the current template. Leave the rest of the file alone.
- If they are absent, insert the template once, after the project overview. Remove older continuity instructions it supersedes, including a `session-continuity` marked section and rules about `.agents/next-steps.md`, `.agents/pending.md`, or parked pending items. Do not rewrite, shorten, or reword unrelated sections; keep their examples and reasons.
- Put project-specific additions outside the markers. If the copy already matches the template, leave the file untouched.

## 6. Before merge

When the user accepts a branch's work and its PR is ready to merge, run only this step and step 7:

- Remove the branch's subsection and its resolved pending requests, and update `Ranked work` to read as it will after the merge.
- Move anything still unresolved from the subsection to the issue or to `Pending`.

## 7. Save, verify, and report

- Use the `commit` skill. Put `HANDOFF.md`, `<docs>/`, and `AGENTS.md` updates in a `docs:` commit on the work branch, separate from source commits. Commit only when there are changes.
- **No work branch** (on the default branch): create the next ranked task's branch from its issue as the template describes, and commit there. If there is no next task, leave the changes uncommitted and report them.
- If unfinished source changes remain uncommitted, note the files in the branch subsection and report them. Do not imply that committing `HANDOFF.md` also saved them.
- Push only within the user's existing authorization; otherwise record the push request in the branch subsection. Creating a PR needs its own authorization. Pushing also publishes the branch's earlier unpushed commits.
- Before reporting, inspect the final working tree and confirm which commits were pushed. Say plainly when another computer cannot retrieve the handoff or the work yet.
- Use the reply template below; it lists requests still awaiting approval. If the user answers afterwards, resolve them as in step 3 and save the result normally.

## Final reply template

Before writing the final reply, read and fill in [the reply template](assets/handoff-reply.md). This plain Markdown asset is shared by Codex and Claude Code.

- **Verdict first:** open with one bold line saying whether it is safe to stop: "Safe to stop: everything is pushed." or "Not safe yet:" followed by what exists only on this computer (unpushed commits, uncommitted files). Then name the branch and PR to resume from. Do not restate the branch's `HANDOFF.md` subsection; it is the record.
- **Needs you:** each request still awaiting approval, with its ID, proposed action, and what it blocks, plus any question the user has not answered. Omit the section when nothing needs the user.
- **Done:** one plain past-tense bullet per change, decision, or filed item. Link directly to the comment when reporting a handoff note.
- **Commits:** exactly one commit per bullet, with its short hash and subject; never combine commits on one line. Omit the section when no commits were made.
- **Next:** the next 2–4 concrete tasks in priority order, one per bullet. If fewer exist, list only those; if none remain, say so in a single bullet.
- Make every issue and PR mention a Markdown link, including repeated mentions. Scale to the session: a small session may be just the verdict line and `Next`.
