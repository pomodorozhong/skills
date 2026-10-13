---
name: wrap-up
description: End a work session by leaving handoff notes on the GitHub issues that were worked on, parking anything that needs the user's approval (new issues, pushes) in .agents/pending.md, re-ranking the issue list in .agents/next-steps.md, moving long-term knowledge into the docs folder, and committing. Use when the user says "wrap up", "let's stop here", "end the session", or similar.
---

# Wrap up

Leave the project so the next session can pick up without this conversation. Work items and their context live in GitHub issues; `.agents/next-steps.md` only ranks them; anything meant to last goes in the docs folder.

**Docs folder:** use `docs/`, unless the repo already has a `doc/` folder; then use `doc/` and do not create `docs/`. Below, `<docs>` means that folder.

**No GitHub remote** (`gh repo view` fails): say so, skip steps 2 and 3, and do the rest.

## 1. Review the session

Go back over the conversation and the diff since the session started, and list:

- **Done:** what changed, with commit hashes once committed, and which issues it covers.
- **Decided:** choices the user made, and why.
- **Learned:** facts found along the way (constraints, pitfalls, results).
- **Open:** anything unresolved, unclear, or half-finished, including questions the user did not answer.

## 2. Update the issues

- **Issues worked on:** comment on each with what the next session needs: what was done, what was tried and failed, what is left. Decisions the user made go on the issue they belong to. Remove `needs-decision` once its questions are answered. Comments on these issues need no approval.
- **New work found** (bugs, ideas, follow-ups, unanswered questions): draft an issue for each, with a title, labels, milestone and a body that stands alone. Label open questions `needs-decision`. Drafts go to `pending.md` (step 7), not straight to GitHub.
- **Half-finished work:** pushing the branch and opening a draft PR that links the issue goes to `pending.md` too, so nothing in progress lives only on this machine once the user approves it.
- **Dependencies:** when one issue can't start before another, record it on the issue ("Blocked by #N").
- **Milestones:** each milestone's description says what it is for, what it waits on and why, and when it is done. If the session changed the order between milestones, update the affected descriptions. If a milestone has no open issues left, closing it goes to `pending.md`.

Never put local paths with personal IDs (such as a Steam ID) in an issue or comment.

## 3. Re-rank `.agents/next-steps.md`

The ranked list of what to do next, one line per issue, with an optional short reason when the order isn't obvious:

```markdown
# Next steps

1. #8 Decide the redesign direction (blocks #9–#15)
2. #1 First run on the real data folder (shows which stops need a region, before #12)
3. #11 Save import review shows "Apply" when nothing changed
```

- Drop closed issues, add new ones, and re-order by priority. `needs-decision` issues that block the next work go first.
- Keep the reason to a clause. Anything longer belongs in a comment on the issue; order between milestones belongs in the milestone descriptions.

## 4. Move long-term knowledge into `<docs>/`

Durable knowledge goes in `<docs>/`: architecture, decisions and their reasons, workflow assumptions, gotchas, and user-facing behavior (`README.md`).

- Update the existing doc that covers the topic; create a new one only when none fits, and link it from the folder's index (`<docs>/README.md`), creating the index if needed.
- Fix any doc statements that this session made stale.

## 5. Make sure `AGENTS.md` points here

If `AGENTS.md` at the repo root has no "Start of a session" section, add one: resolve any parked pending items first, then read `.agents/next-steps.md`, check the top issue is still open (`gh issue view`), propose it to the user, and end sessions with the `wrap-up` skill. Otherwise change nothing.

## 6. Commit

Commit only if files changed (`.agents/next-steps.md`, `<docs>/`, `AGENTS.md`). Use the `commit` skill, as a `docs:` commit on the current branch, so it lands with that branch's PR. If that branch's PR has already merged or closed (the `commit` skill checks), or the changes don't fit its theme, commit on a new `docs/<summary>` branch from the up-to-date default branch instead. If no branch was made this session, leave the changes uncommitted and say so; the next branch picks them up.

## 7. Park what needs approval, then ask

Everything else is saved by now, so the user can leave at any point from here without losing anything.

1. Write each item that needs the user's approval (issue drafts in full, pushes, draft PRs, milestones to close) to `.agents/pending.md`, under a `# Pending (from YYYY-MM-DD)` heading.
2. Commit it on its own as `chore: park pending items`, with no other file in that commit. No other commit may touch `pending.md`. If no branch was made this session, create `chore/pending-YYYY-MM-DD` from the default branch for it.
3. Report in a few lines: the issues commented on, the commits made, the top of `.agents/next-steps.md` (especially any `needs-decision` issue), and the parked items.
4. Ask about the parked items, unless the user said they have to go. Whatever they answer, resolve it as below.

## Resolving pending items

Used at the end of a wrap-up when the user answers, and at the start of the next session when they didn't.

- **Find it:** `git log --branches --source --format='%h %S %s' --grep='^chore: park pending items$'`. Read the file from that commit (`git show <hash>:.agents/pending.md`), whichever branch is checked out.
- **Go through each item** with the user: do what they approve, edit what they change, drop what they reject. Before a parked push, check again that the branch's PR hasn't merged in the meantime (the `commit` skill's merged check); if it has, move the commits to a new branch from the default branch instead.
- **Clean up:** remove the pending commit from its branch with `git rebase --onto <hash>^ <hash> <branch>`, or delete the branch if it is a `chore/pending-*` branch with nothing else on it. If items remain unresolved, park them again as one new pending commit, so there is never more than one.
- **Already pushed:** removing the commit then needs `git push --force-with-lease`; ask before pushing. Never merge a PR while its branch still has a pending commit.
