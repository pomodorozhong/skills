---
name: propose-stack
description: Read a project's goals, plans, and progress (open issues, milestones, HANDOFF.md, README, docs), propose up to five PRs, build them together on one stack branch, and publish each as its own branch and PR against the default branch after the user approves the plan, reviews the work, and approves the final branches. Also rebuilds a dependent PR after the PR it needs is squash-merged. Use when the user asks what to work on next as PRs, asks for a stack of PRs, or asks to update a PR after the one it depends on merges.
---

# Propose a stack

Find the next few pieces of work from the project's own records, propose them as a set of PRs, build them together on one stack branch, and then rebuild each PR as its own branch from the default branch. Every PR targets the default branch and is squash-merged on its own. The user gives three answers before anything is pushed: the plan, review feedback on the built work, and the final publish approval. Approving the plan or giving feedback never authorizes a push.

Ask for each answer in chat and wait for a reply; silence is not approval. If the session ends before the user answers, keep the open request in the reply.

Show everything the user needs to decide (the plan, the questions, each PR's title and body, the review steps) in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

**A PR this skill opened has merged:** if the user asks to update the remaining PRs, or this skill starts while a dependent PR it opened waits on one that has merged, go to [After a prerequisite merges](#after-a-prerequisite-merges).

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure, say which, and propose from the local docs only. Do not publish without GitHub.

## 1. Gather context

Read, and change nothing:

- `README`, `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, contributing docs, and the docs folder (`docs/` or `doc/`), including roadmaps, plans, and changelogs.
- Open issues with their labels, milestones, and comments; read closed issues only when an open one depends on them. Note `needs-decision` labels and "Blocked by #N" notes.
- Milestones and their descriptions: what each is for, what it waits on, and its due date.
- Open PRs and remote branches, so the proposal does not repeat work already in flight.
- Recent history on the default branch (`git log --oneline -30`), after fetching it.

If a search or listing fails, say so instead of claiming there is nothing.

## 2. Propose the stack

Pick up to five PRs that move the project toward its stated next goal, usually the earliest open milestone or the top of `HANDOFF.md`'s ranked work. Propose fewer when the work does not split naturally; never pad the stack.

**Prefer independent PRs.** Each PR will be its own branch from the default branch, so a PR that needs another PR's code must carry that PR's commits until it merges, then be rebuilt. Choose and cut the work so most PRs stand alone. Order the PRs on the stack branch so anything a PR needs comes before it: foundations (data models, library code, refactors that make room) first, and the features, UI, and docs that use them later.

For each PR, show:

- Position, a working title, and the issue it covers, with whether it fully resolves it (`Closes`) or only part of it (`Related to`).
- The change: what will behave differently, and which files or components it touches.
- **Independent**, or **depends on** the earlier PRs it needs, and what it needs from them.
- Rough size, and the checks that will be run.

Then show:

- Why these PRs, and the candidates you left out with one line each on why.
- The stack branch (`stack/<summary>`) and the branch names the PRs will get, following the repo's conventions in its `AGENTS.md` or contributing docs (default `<type>/<summary>`).
- Assumptions.
- **Questions:** three to five, only about choices that are costly to change once built: public APIs and names, data and file formats, new dependencies, scope boundaries between PRs, dependencies between PRs, and behavior users will rely on. Give your recommended answer for each. Skip anything cheap to change during review.

Stop and wait for answers and "go". Apply precise edits without asking again; show the revised plan for substantive ones.

## 3. Build on the stack branch

- Create the stack branch from the up-to-date default branch and record that base commit. Follow the [commit](../commit/SKILL.md) skill for staging, splitting, commit messages, and checks; it never pushes here.
- Build the PRs in order. Each PR is one contiguous run of commits, and no commit belongs to two PRs.
- Keep a **PR map**: the base commit, and for each PR its position, title, branch name, the PRs it depends on, and its commits (short hash and subject). Save it as `propose-stack/<stack branch>.md` in the Git common directory (`git rev-parse --git-common-dir`), which is never committed and is shared by worktrees.
- Implement the approved plan only. If the plan turns out wrong (a PR is much bigger than expected, or needs a PR it was not planned to depend on), stop and ask before changing the plan.

## 4. Trial rebuild

Check that each PR works as its own branch before showing it for review:

- In a temporary detached worktree in the scratchpad, for each PR, start from the recorded base commit and cherry-pick the commits of the PRs it depends on, in stack order, then its own commits.
- Run the project's checks on the result, and record its tree hash (`git rev-parse HEAD^{tree}`) in the PR map. Remove the worktree afterwards.
- If an independent PR fails to apply or fails checks alone, it depends on something the plan missed. Stop and report it with a proposed fix: move the shared piece into an earlier PR, or mark the dependency.

## 5. Review request

Write each PR's title and body following [the rules below](#title-and-body), then show:

- The stack branch, its base commit, and how far the default branch has moved since (`git rev-list --count <base>..origin/<default>`).
- For each PR: its title, independent or what it depends on, commits (short hash and subject), the trial rebuild's check results (including failed, skipped, or not run), and full body.
- **Review steps:** how to try each PR on its own (the cherry-pick commands from step 4 on a detached base, then the commands to run and what to look at), most important first.
- **Details to check:** choices made while building that the plan did not settle and that could plausibly differ from the user's goal or taste, such as names, wording users will see, defaults, error behavior, file layout, and scope moved between PRs. For each, say what you chose and the main alternative.
- Differences from the approved plan.

Ask for feedback and stop.

## 6. Apply feedback and final review

- Put each fix in the PR it belongs to: commit it as a `fixup!` of a commit in that PR, then fold it in with `git rebase -i --autosquash`. The stack branch is never pushed, so rewriting it is safe.
- Repeat the trial rebuild (step 4) for every changed PR and every PR that depends on one. Update the PR map, titles, and bodies.
- Show the same review as step 5, plus what changed for each piece of feedback.

Ask: "Push these N branches and open the PRs?" and stop. If the user gives more feedback, repeat this step.

## 7. Publish and verify

- Immediately before publishing, confirm the stack branch tip and PR map still match what was approved, and that none of the PR branch names exists locally, on the remote, or as an open PR. Any change needs a new approval.
- Rebuild each PR branch exactly as in the trial: from the recorded base commit, cherry-pick the commits of the PRs it depends on, then its own. Confirm each branch's tree hash matches the one recorded in the PR map. Do not rebase onto a newer default branch here; that changes what was approved.
- Push every branch without force. Open each PR with `gh pr create --base <default> --head <branch> --body-file <file>` holding the exact approved body, independent PRs first. Open a dependent PR as a draft (`--draft`) so it cannot be squash-merged before the PRs it needs, which would merge their changes too. Add no labels, reviewers, or comments that were not shown.
- Once all are open, fill the real PR numbers into each body's **Stack** section with `gh pr edit --body-file`. That is the only change allowed to an approved body.
- Fetch each PR and check its base, head, commit tip, title, body, draft status, and that `closingIssuesReferences` lists only the issues its body closes.
- Reply with every PR as a Markdown link and the state of its checks, and say which merge order the dependent PRs need. Then propose deleting the local stack branch, the local PR branches, and the PR map; delete only with the user's approval.
- If publishing fails partway, keep every local branch and the approved drafts, report what was pushed and opened, and keep the request open.

Opening the PRs does not authorize merging, force-pushing, or further changes.

## After a prerequisite merges

A squash merge puts a PR's changes on the default branch as one new commit, so a dependent PR still carries the original commits and its diff still shows them. Rebuild it without them.

1. **Find what changed:** fetch, read the Stack sections of the open PRs this skill opened, and list each dependent PR whose prerequisites have merged. If a dependent PR merged before what it depends on, or a prerequisite was closed without merging, stop and ask.
2. **Rebuild locally:** for each such PR, start from the up-to-date default branch and cherry-pick the commits of any prerequisites still unmerged, in stack order, then its own commits (the PR map lists them; without it, take them from the PR's commit list). Resolve conflicts, and stop and ask about any that needs a decision. Run the checks.
3. **Approval:** for each PR, show the old and new tip, the commits now on the branch, the check results, and the conflicts resolved, plus whether it can leave draft (all its prerequisites merged). Ask: "Force-push these N branches?" and stop.
4. **Publish:** immediately before, confirm each remote branch still has its old tip. Push each with `git push --force-with-lease=<branch>:<old tip>`. Update the Stack sections to mark the merged PRs, and mark a PR ready for review (`gh pr ready`) only when all its prerequisites have merged.
5. **Verify:** check each PR's tip and diff against the default branch, and reply with the PRs as Markdown links.

## Title and body

Use the repository's PR template if it has one, plus a Stack section; otherwise fill in [the PR body template](assets/pr-body.md).

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references or positions in the title.
- **Body:** written for a reviewer who has not seen the conversation, from that PR's own commits and real results only. Never invent results or issue links.
- **Stack:** list every PR built in the same stack, marking this one and any that merged. Say whether this PR is independent; if not, name the PRs it depends on, that it must merge after them, and that until they merge its diff also shows their changes. Before publishing, write the positions and titles; real numbers are filled in after the PRs open.
- **Verification:** list commands actually run on that PR's rebuilt branch and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** every PR targets the default branch, so each closes its own issue with `Closes #N` when it fully resolves it. Use `Related to #N` with the relationship when a PR covers only part of an issue. Never close a prerequisite's issue from a dependent PR. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
