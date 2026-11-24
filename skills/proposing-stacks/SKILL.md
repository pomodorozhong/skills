---
name: proposing-stacks
description: Propose the next few PRs from a project's issues, milestones, and handoff notes, build them as a stack of branches with `gh stack`, and publish them as stacked PRs on GitHub. Use when the user asks what to work on next as PRs or for a stack of PRs, or asks to show, update, or merge an existing stack, such as after a PR in it merges or the stack falls behind. Not for opening a single PR.
---

# Propose a stack

Find the next few pieces of work from the project's own records, propose them as a set of PRs, and build them as a stack with the `gh stack` extension: each PR is its own branch built on the one below it, each PR targets the branch below it, and the bottom PR targets the default branch. GitHub shows the PRs as one stack and merges them bottom first. The user gives three answers before anything is pushed: the plan, review feedback on the built work, and the final publish approval. Approving the plan or giving feedback never authorizes a push.

Ask for each answer in chat and wait for a reply; silence is not approval. An unanswered request stays open: name it again in any later status or closing report until the user answers.

Show everything the user needs to decide (the plan, the questions, each PR's title and body, the review steps) in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

**Link every issue and PR:** whenever a message to the user mentions an issue or PR, write it as a Markdown link to its full URL with its title, such as `[#12 Add export](https://github.com/<owner>/<repo>/issues/12)`, taking the owner and repository from the remote it belongs to. This covers the proposal, the review, and the publish report. Never write a bare `#N`. PR and commit bodies on GitHub keep the plain `#N` form, which GitHub links itself and needs for closing keywords.

**Requires `gh stack`:** before running any `gh stack` command, check `gh stack --version` and that `git --version` is 2.38 or later (`gh stack` needs 2.36; folding review fixes in step 7 uses `git rebase --update-refs`, added in 2.38). If the extension is missing, stop and propose installing it with `gh extension install github/gh-stack`; install only with the user's approval.

**Run `gh stack` non-interactively:** some commands open a prompt or a full-screen view in a terminal and wait forever. Read the stack only with `gh stack view --json`, never bare `gh stack view`; use each branch's `needsRebase`, `isMerged`, and `pr` (`number`, `state`) fields. Always name the branch for `init`, `add`, and `checkout`, always pass `--auto` to `gh stack submit`, and never run `gh stack modify` or `gh stack switch`. Set `git config rerere.enabled true` before the first `gh stack init`, which otherwise asks before turning it on.

**The remote:** this skill calls the remote the PRs target `origin`; if it has another name, use that. If the repository has more than one remote and `git config remote.pushDefault` is unset, pass `--remote origin` to every `gh stack push`, `gh stack submit`, and `gh stack rebase`, and say in the proposal that `gh stack checkout` needs `remote.pushDefault` set to `origin`; set it only with the user's approval.

**Merging, or the stack has changed on GitHub:** if the user asks to merge the stack or part of it, or to update the remaining PRs, or this skill starts while a stack it opened (see **Finding the stack** below) has a merged PR or a branch that `gh stack view --json` marks with `needsRebase`, read and follow [the update reference](references/update-stack.md).

**Stack overview:** if the user asks to see the stack, its overview, status, or where things stand ("show me the stack overview"), read and follow [the overview reference](references/overview.md).

**Same repository only:** GitHub stacks need every branch in the repository the PRs target; cross-fork stacks are not supported. If the branches would be pushed to a fork of the repository the PRs target, say so and stop before proposing.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure, say which, and propose from the local docs only. Do not publish without GitHub.

**Finding the stack:** `gh stack view --json` reads only the stack of the checked-out branch and exits with code 2 when that branch is in none, such as on the default branch or on the review branch. Then look for the folders in `.agents/propose-stack/`: each is named after its stack's bottom branch (see below). While the review branch is checked out (steps 5 and 6), the PR branches do not change, so take their state from `git` and the saved `review.md`. Otherwise, if the working tree is clean, run `gh stack checkout <bottom branch>` and say which branch you switched from; if it is not clean, stop and ask.

**Working files:** everything this skill writes goes in `.agents/propose-stack/<summary>/` in the worktree that holds the stack, where `<summary>` is the bottom branch's name with each `/` replaced by `-`, so a later session can find the folder from the bottom branch that `gh stack view --json` shows (it keeps merged branches, marked `isMerged`): the review request (`review.md`) and each PR's body (`body-<position>.md`). The review branch is `propose-stack/review-<summary>`; it is local only and never pushed. Keep the folder out of Git without ignoring the rest of `.agents/`: if `git ls-files .agents/propose-stack` lists anything, stop and ask where to write; otherwise, before the first write, add `/.agents/propose-stack/` to `info/exclude` in the Git common directory if it is missing, and confirm with `git check-ignore`. Only the temporary worktrees used for checks and trial folds go in the scratchpad.

## 1. Gather context

Read, and change nothing:

- `README`, `AGENTS.md`, `CLAUDE.md`, the handoff notes (`HANDOFF.md`, or wherever the session's instructions say they are kept), contributing docs, and the docs folder (`docs/` or `doc/`), including roadmaps, plans, and changelogs.
- Open issues with their labels, milestones, and comments; read closed issues only when an open one depends on them. Note `needs-decision` labels and "Blocked by #N" notes.
- Milestones and their descriptions: what each is for, what it waits on, and its due date.
- Open PRs and remote branches, so the proposal does not repeat work already in flight. `gh stack view --json` shows only the stack of the checked-out branch, and exits with code 2 when that branch is in none; list the repository's other stacks with `gh api repos/<owner>/<repo>/stacks`.
- Whether stacked PRs are turned on for the repository: the same `gh api repos/<owner>/<repo>/stacks` call returns `404 Not Found` when they are not.
- Whether GitHub deletes a PR's branch when the PR merges: `gh api repos/<owner>/<repo> --jq .delete_branch_on_merge`.
- Recent history on the default branch (`git log --oneline -30`), after fetching it.

If a search or listing fails, say so instead of claiming there is nothing.

## 2. Propose the stack

Pick up to five PRs that move the project toward its stated next goal, usually the earliest open milestone or the top of the handoff notes' ranked work. Propose fewer when the work does not split naturally; never pad the stack.

**Order the stack.** A PR can use everything below it and nothing above it. Put anything a PR needs below it: foundations (data models, library code, refactors that make room) before the features, UI, and docs that use them. Among PRs that do not need each other, put the simplest first (fewest lines and files changed), so the bottom of the stack can be reviewed and merged soonest.

For each PR, show:

- Position, a working title, and the issue it covers, with whether it fully resolves it (`Closes`) or only part of it (`Related to`).
- The change: what will behave differently, and which files or components it touches.
- What it needs from the PRs below it, or that it needs nothing from them.
- Rough size, and the checks that will be run.

Then show:

- Why these PRs, and the candidates you left out with one line each on why.
- The branch name each PR will get, following the repo's conventions in its `AGENTS.md` or contributing docs (default `<type>/<summary>`).
- Assumptions.
- That the build turns on `git rerere` (Git remembers how conflicts were resolved) in this repository's local Git config, as `gh stack init` requires.
- Whether stacked PRs are turned on for the repository on GitHub. If they are not, say that the PRs can still be opened as an ordinary chain of PRs, each based on the one below, but GitHub will not show or merge them as a stack.
- If `delete_branch_on_merge` is `false`, a question recommending turning on **Automatically delete head branches**, so GitHub deletes each remote branch as its PR merges. The setting covers every PR in the repository, not just this stack. Changing a repository setting is outward-facing and needs its own yes, separate from the push approval; say nothing about the setting when it is already on.
- **Questions:** three to five, only about choices that are costly to change once built: public APIs and names, data and file formats, new dependencies, scope boundaries between PRs, stack order, and behavior users will rely on. Give your recommended answer for each. Skip anything cheap to change during review.

Stop and wait for answers and "go". Apply precise edits without asking again; show the revised plan for substantive ones.

## 3. Build the stack

Once the user says "go", read [the build and review reference](references/build-and-review.md) and follow its steps 3 and 5, with step 4 below between them. In short: fast-forward the local default branch, turn on `git rerere`, and build each PR on its own branch with `gh stack init` and `gh stack add`, implementing the approved plan only. If the plan turns out wrong, stop and ask before changing it.

## 4. Check each layer

Check that each PR works with only the PRs below it before showing it for review:

- For each branch, bottom first, check out its tip in a temporary detached worktree in the scratchpad, run the project's checks, and note the results for the review. Remove the worktree afterwards. The separate worktree makes the checks see only the committed tip, not uncommitted fixes or untracked files left in the stack's worktree.
- If a branch fails its checks, fix it on that branch. If it fails because it needs something from a PR above it that the plan missed, stop and report it with a proposed fix: move the shared piece lower, or reorder the stack.

## 5. Review request

Write each PR's title and body (use the repository's PR template if it has one, otherwise [the PR body template](assets/pr-body.md)), fill in [the review request template](assets/review-request.md), save it and the bodies in the working files, and create the local review branch `propose-stack/review-<summary>` on top of the top PR branch with plain `git`. Ask for feedback and stop.

## 6. Collect feedback on the review branch

Before acting on the user's answer to any review round, read [the fold and publish reference](references/fold-and-publish.md) if this session has not, and follow its step 6, which collects the fixes on the review branch and leaves the PR branches unchanged. Ask for more feedback, or whether the review is done, and stop. If the user had no feedback at all, follow the reference's no-feedback path.

## 7. Fold the fixes and publish

Follow step 7 of [the fold and publish reference](references/fold-and-publish.md), reading it first if this session has not. It folds the fixes into their PRs and shows the final review, then asks: "Push these N branches and open the PRs?", naming the delete-branch-on-merge setting change too if it was approved. Stop there; push, change the setting, or open PRs only after that approval.

Opening the PRs does not authorize merging, force-pushing, or further changes. For merging, and for keeping the stack up to date after a PR merges or the default branch moves ahead, read [the update reference](references/update-stack.md).
