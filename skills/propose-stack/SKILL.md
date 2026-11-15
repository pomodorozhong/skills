---
name: propose-stack
description: Read a project's goals, plans, and progress (open issues, milestones, HANDOFF.md, README, docs), propose up to five PRs, build them as a stack of branches with `gh stack`, and publish them as a stacked set of PRs on GitHub after the user approves the plan, reviews the work, and approves the final branches. Also shows an overview of the current stack, and keeps it up to date after a PR in it merges or the default branch moves ahead. Use when the user asks what to work on next as PRs, asks for a stack of PRs, asks to see the stack overview or status, asks to update the remaining PRs after one merges or the stack falls behind, or asks to merge the stack or part of it.
---

# Propose a stack

Find the next few pieces of work from the project's own records, propose them as a set of PRs, and build them as a stack with the `gh stack` extension: each PR is its own branch built on the one below it, each PR targets the branch below it, and the bottom PR targets the default branch. GitHub shows the PRs as one stack and merges them bottom first. The user gives three answers before anything is pushed: the plan, review feedback on the built work, and the final publish approval. Approving the plan or giving feedback never authorizes a push.

Ask for each answer in chat and wait for a reply; silence is not approval. If the session ends before the user answers, keep the open request in the reply.

Show everything the user needs to decide (the plan, the questions, each PR's title and body, the review steps) in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

**Link every issue and PR:** whenever a message to the user mentions an issue or PR, write it as a Markdown link to its full URL with its title, such as `[#12 Add export](https://github.com/<owner>/<repo>/issues/12)`, taking the owner and repository from the remote it belongs to. This covers the proposal, the review, and the publish report. Never write a bare `#N`. PR and commit bodies on GitHub keep the plain `#N` form, which GitHub links itself and needs for closing keywords.

**Requires `gh stack`:** before running any `gh stack` command, check `gh stack --version` and that `git --version` is 2.38 or later (`gh stack` needs 2.36; folding review fixes in step 7 uses `git rebase --update-refs`, added in 2.38). If the extension is missing, stop and propose installing it with `gh extension install github/gh-stack`; install only with the user's approval.

**Run `gh stack` non-interactively:** some commands open a prompt or a full-screen view in a terminal and wait forever. Read the stack only with `gh stack view --json`, never bare `gh stack view`; use each branch's `needsRebase`, `isMerged`, and `pr` (`number`, `state`) fields. Always name the branch for `init`, `add`, and `checkout`, always pass `--auto` to `gh stack submit`, and never run `gh stack modify` or `gh stack switch`. Set `git config rerere.enabled true` before the first `gh stack init`, which otherwise asks before turning it on.

**The remote:** this skill calls the remote the PRs target `origin`; if it has another name, use that. If the repository has more than one remote and `git config remote.pushDefault` is unset, pass `--remote origin` to every `gh stack push`, `gh stack submit`, and `gh stack rebase`, and say in the proposal that `gh stack checkout` needs `remote.pushDefault` set to `origin`; set it only with the user's approval.

**Merging, or the stack has changed on GitHub:** if the user asks to merge the stack or part of it, or to update the remaining PRs, or this skill starts while a stack it opened (see [Finding the stack](#propose-a-stack)) has a merged PR or a branch that `gh stack view --json` marks with `needsRebase`, read and follow [the update reference](references/update-stack.md).

**Stack overview:** if the user asks to see the stack, its overview, status, or where things stand ("show me the stack overview"), reply by filling in [the review request template](assets/review-request.md) with the stack's current state. Start from the saved `review.md` when there is one, but refresh anything that has changed since it was written from `gh stack view --json` and `git` (commits, check results, how far the default branch has moved, and each PR's link and state, open, queued, merged, or closed, in the **PR** column once published), and save the refreshed version over it. Fill in only what exists so far: before step 5, mark the sections that come later as not yet reached rather than inventing them. Showing the overview answers no open question; end with whatever request is still open.

**Same repository only:** GitHub stacks need every branch in the repository the PRs target; cross-fork stacks are not supported. If the branches would be pushed to a fork of the repository the PRs target, say so and stop before proposing.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure, say which, and propose from the local docs only. Do not publish without GitHub.

**Finding the stack:** `gh stack view --json` reads only the stack of the checked-out branch and exits with code 2 when that branch is in none, such as on the default branch or on the review branch. Then look for the folders in `.agents/propose-stack/`: each is named after its stack's bottom branch (see below). While the review branch is checked out (steps 5 and 6), the PR branches do not change, so take their state from `git` and the saved `review.md`. Otherwise, if the working tree is clean, run `gh stack checkout <bottom branch>` and say which branch you switched from; if it is not clean, stop and ask.

**Working files:** everything this skill writes goes in `.agents/propose-stack/<summary>/` in the worktree that holds the stack, where `<summary>` is the bottom branch's name with each `/` replaced by `-`, so a later session can find the folder from the bottom branch that `gh stack view --json` shows (it keeps merged branches, marked `isMerged`): the review request (`review.md`) and each PR's body (`body-<position>.md`). The review branch is `propose-stack/review-<summary>`; it is local only and never pushed. Keep the folder out of Git without ignoring the rest of `.agents/`: if `git ls-files .agents/propose-stack` lists anything, stop and ask where to write; otherwise, before the first write, add `/.agents/propose-stack/` to `info/exclude` in the Git common directory if it is missing, and confirm with `git check-ignore`. Only the temporary worktrees used for checks and trial folds go in the scratchpad.

## 1. Gather context

Read, and change nothing:

- `README`, `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, contributing docs, and the docs folder (`docs/` or `doc/`), including roadmaps, plans, and changelogs.
- Open issues with their labels, milestones, and comments; read closed issues only when an open one depends on them. Note `needs-decision` labels and "Blocked by #N" notes.
- Milestones and their descriptions: what each is for, what it waits on, and its due date.
- Open PRs and remote branches, so the proposal does not repeat work already in flight. `gh stack view --json` shows only the stack of the checked-out branch, and exits with code 2 when that branch is in none; list the repository's other stacks with `gh api repos/<owner>/<repo>/stacks`.
- Whether stacked PRs are turned on for the repository: the same `gh api repos/<owner>/<repo>/stacks` call returns `404 Not Found` when they are not.
- Recent history on the default branch (`git log --oneline -30`), after fetching it.

If a search or listing fails, say so instead of claiming there is nothing.

## 2. Propose the stack

Pick up to five PRs that move the project toward its stated next goal, usually the earliest open milestone or the top of `HANDOFF.md`'s ranked work. Propose fewer when the work does not split naturally; never pad the stack.

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
- **Questions:** three to five, only about choices that are costly to change once built: public APIs and names, data and file formats, new dependencies, scope boundaries between PRs, stack order, and behavior users will rely on. Give your recommended answer for each. Skip anything cheap to change during review.

Stop and wait for answers and "go". Apply precise edits without asking again; show the revised plan for substantive ones.

## 3. Build the stack

- Fetch, then fast-forward the local default branch to `origin/<default>`, because `gh stack init` builds on the local branch: `git fetch origin <default>:<default>`, or `git merge --ff-only origin/<default>` where it is checked out. If it cannot fast-forward, stop and ask. Then run `git config rerere.enabled true` and start the stack with `gh stack init --base <default> <first branch>`. Follow the [commit](../commit/SKILL.md) skill for staging, splitting, commit messages, and checks; it never pushes here.
- Build the PRs in order: commit each PR's work on its own branch, then `gh stack add <next branch>` to start the next one on top.
- Implement the approved plan only. If the plan turns out wrong (a PR is much bigger than expected, or needs a PR above it), stop and ask before changing the plan.

## 4. Check each layer

Check that each PR works with only the PRs below it before showing it for review:

- For each branch, bottom first, check out its tip in a temporary detached worktree in the scratchpad, run the project's checks, and note the results for the review. Remove the worktree afterwards. The separate worktree makes the checks see only the committed tip, not uncommitted fixes or untracked files left in the stack's worktree.
- If a branch fails its checks, fix it on that branch. If it fails because it needs something from a PR above it that the plan missed, stop and report it with a proposed fix: move the shared piece lower, or reorder the stack.

## 5. Review request

Write each PR's title and body following [the rules below](#title-and-body), then show the following, filling in [the review request template](assets/review-request.md):

- The stack's base commit (`git merge-base origin/<default> <bottom branch>`), and how far the default branch has moved since (`git rev-list --count <base>..origin/<default>`).
- For each PR, in stack order from the bottom: its title, branch, commit range and count, the check results (including failed, skipped, or not run), and full body.
- **Review steps:** how to try each PR (check out its branch in a detached worktree, then the commands to run and what to look at).
- **Details to check:** choices made while building that the plan did not settle and that could plausibly differ from the user's goal or taste, such as names, wording users will see, defaults, error behavior, file layout, and scope moved between PRs. For each, say what you chose and the main alternative.
- Differences from the approved plan.

Save each PR's body as `body-<position>.md` and the filled-in review request as `review.md` in the working files, replacing any earlier versions. Give `review.md`'s path in the reply.

Then create the review branch on top of the top PR branch: `git switch -c propose-stack/review-<summary> <top branch>`. Use plain `git`, not `gh stack add`: the review branch is not a layer, and `gh stack push` and `gh stack submit` must never push it.

Ask for feedback and stop.

## 6. Collect feedback on the review branch

Before committing the first fix, read [the fold and publish reference](references/fold-and-publish.md) and follow its step 6. In short: commit each fix on the review branch as a `fixup!` of a commit in the PR it belongs to, leave the PR branches unchanged, check the review branch's tip and a trial fold, and show the updated review. Ask for more feedback, or whether the review is done, and stop.

## 7. Fold the fixes and publish

Follow step 7 of [the fold and publish reference](references/fold-and-publish.md), reading it first if this session has not. In short: fold the fixes into their PRs with `git rebase --autosquash --update-refs`, check every branch again, and show the final review. Ask: "Push these N branches and open the PRs?" and stop. Only after that approval, push with `gh stack push`, open each PR with its approved title and body, group them with `gh stack submit --auto`, and check the result on GitHub.

Opening the PRs does not authorize merging, force-pushing, or further changes. For merging, and for keeping the stack up to date after a PR merges or the default branch moves ahead, read [the update reference](references/update-stack.md).

## Title and body

Use the repository's PR template if it has one; otherwise fill in [the PR body template](assets/pr-body.md).

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references or positions in the title.
- **Body:** written for a reviewer who has not seen the conversation, from that PR's own commits and real results only. Never invent results or issue links.
- **Verification:** list commands actually run on that PR's branch and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** each PR closes its own issue with `Closes #N` when it fully resolves it. GitHub links a closing keyword only while the PR targets the default branch, and closes the issue when that PR merges into it; a PR above the bottom targets another branch until the PRs below it merge. Use `Related to #N` with the relationship when a PR covers only part of an issue. Never close another PR's issue. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
