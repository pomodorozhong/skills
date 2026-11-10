---
name: propose-stack
description: Read a project's goals, plans, and progress (open issues, milestones, HANDOFF.md, README, docs), propose up to five PRs, build them as a stack of branches with `gh stack`, and publish them as a stacked set of PRs on GitHub after the user approves the plan, reviews the work, and approves the final branches. Also shows an overview of the current stack, and keeps it up to date after a PR in it merges or the default branch moves ahead. Use when the user asks what to work on next as PRs, asks for a stack of PRs, asks to see the stack overview or status, or asks to update the remaining PRs after one merges or the stack falls behind.
---

# Propose a stack

Find the next few pieces of work from the project's own records, propose them as a set of PRs, and build them as a stack with the `gh stack` extension: each PR is its own branch built on the one below it, each PR targets the branch below it, and the bottom PR targets the default branch. GitHub shows the PRs as one stack and merges them bottom first. The user gives three answers before anything is pushed: the plan, review feedback on the built work, and the final publish approval. Approving the plan or giving feedback never authorizes a push.

Ask for each answer in chat and wait for a reply; silence is not approval. If the session ends before the user answers, keep the open request in the reply.

Show everything the user needs to decide (the plan, the questions, each PR's title and body, the review steps) in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

**Link every issue and PR:** whenever a message to the user mentions an issue or PR, write it as a Markdown link to its full URL with its title, such as `[#12 Add export](https://github.com/<owner>/<repo>/issues/12)`, taking the owner and repository from the remote it belongs to. This covers the proposal, the review, and the publish report. Never write a bare `#N`. PR and commit bodies on GitHub keep the plain `#N` form, which GitHub links itself and needs for closing keywords.

**Requires `gh stack`:** before running any `gh stack` command, check `gh stack --version` and that `git --version` is 2.36 or later. If the extension is missing, stop and propose installing it with `gh extension install github/gh-stack`; install only with the user's approval.

**Run `gh stack` non-interactively:** some commands open a prompt or a full-screen view in a terminal and wait forever. Read the stack only with `gh stack view --json`, never bare `gh stack view`; use each branch's `needsRebase`, `isMerged`, and `pr` (`number`, `state`) fields. Always name the branch for `init`, `add`, and `checkout`, always pass `--auto` to `gh stack submit`, and never run `gh stack modify` or `gh stack switch`. Set `git config rerere.enabled true` before the first `gh stack init`, which otherwise asks before turning it on.

**The remote:** this skill calls the remote the PRs target `origin`; if it has another name, use that. If the repository has more than one remote and `git config remote.pushDefault` is unset, pass `--remote origin` to every `gh stack push`, `gh stack submit`, and `gh stack rebase`, and say in the proposal that `gh stack checkout` needs `remote.pushDefault` set to `origin`; set it only with the user's approval.

**The stack has changed on GitHub:** if the user asks to update the remaining PRs, or this skill starts while a stack it opened has a merged PR or a branch that `gh stack view --json` marks with `needsRebase`, go to [Keep the stack up to date](#keep-the-stack-up-to-date).

**Stack overview:** if the user asks to see the stack, its overview, status, or where things stand ("show me the stack overview"), reply by filling in [the review request template](assets/review-request.md) with the stack's current state. Start from the saved `review.md` when there is one, but refresh anything that has changed since it was written from `gh stack view --json` and `git` (commits, check results, how far the default branch has moved, PR numbers and states once published), and save the refreshed version over it. Fill in only what exists so far: before step 5, mark the sections that come later as not yet reached rather than inventing them. Showing the overview answers no open question; end with whatever request is still open.

**Same repository only:** GitHub stacks need every branch in the repository the PRs target; cross-fork stacks are not supported. If the branches would be pushed to a fork of the repository the PRs target, say so and stop before proposing.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure, say which, and propose from the local docs only. Do not publish without GitHub.

**Working files:** everything this skill writes goes in `.agents/propose-stack/<summary>/` in the worktree that holds the stack, where `<summary>` is the bottom branch's name with each `/` replaced by `-`, so a later session can find the folder from the bottom branch that `gh stack view --json` shows: the review request (`review.md`) and each PR's body (`body-<position>.md`). Keep the folder out of Git without ignoring the rest of `.agents/`: if `git ls-files .agents/propose-stack` lists anything, stop and ask where to write; otherwise, before the first write, add `/.agents/propose-stack/` to `info/exclude` in the Git common directory if it is missing, and confirm with `git check-ignore`. Only the temporary worktrees used for checks go in the scratchpad.

## 1. Gather context

Read, and change nothing:

- `README`, `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, contributing docs, and the docs folder (`docs/` or `doc/`), including roadmaps, plans, and changelogs.
- Open issues with their labels, milestones, and comments; read closed issues only when an open one depends on them. Note `needs-decision` labels and "Blocked by #N" notes.
- Milestones and their descriptions: what each is for, what it waits on, and its due date.
- Open PRs and remote branches, so the proposal does not repeat work already in flight. Other stacks show up here as open PRs whose bases are each other's branches. `gh stack view --json` shows only the stack of the checked-out branch, and exits with code 2 when that branch is in none.
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
- That stacked PRs must be turned on for the repository on GitHub, and that if they are not, this shows only when the PRs are grouped at publish time.
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

Ask for feedback and stop.

## 6. Apply feedback and final review

- Put each fix in the PR it belongs to: check out that branch (`gh stack checkout <branch>`), commit the fix there, then run `gh stack rebase --upstack` to carry it into every branch above. Nothing is pushed yet, so rewriting the branches is safe.
- Repeat the checks (step 4) for every changed branch and every branch above it. Update the titles and body files.
- Show the same review as step 5, plus what changed for each piece of feedback in the template's **Changes since last review** section. Save it over the same review file.

Ask: "Push these N branches and open the PRs?" and stop. If the user gives more feedback, repeat this step.

## 7. Publish and verify

- Immediately before publishing, confirm each branch tip still matches the last commit listed for it in the approved `review.md`, and that no PR exists for any of the branches and none of them exists on the remote yet (`git ls-remote --heads origin <branch>` prints nothing). `gh stack push` force-pushes with a lease, so it would overwrite a remote branch of the same name; if one exists, stop and ask. Any change needs a new approval. Do not rebase onto a newer default branch here; that changes what was approved.
- Push every branch with `gh stack push`.
- Open each PR bottom first with `gh pr create --base <branch below> --head <branch> --title "<approved title>" --body-file <working files>/body-<position>.md`, which holds the exact approved body. `gh stack submit --auto` would write its own titles and bodies, so the PRs are opened first. Add no labels, reviewers, or comments that were not shown.
- Check that every branch now has its open PR (`gh pr list --head <branch>`), then group them into a stack on GitHub with `gh stack submit --auto`. It finds the open PRs, so it creates none, keeps them ready for review, links them as a stack, and records each PR in the local stack. Do not use `gh stack link`, which is for branches managed by other tools and records nothing locally. If grouping fails, report it and leave the PRs open; exit code 9 means stacked PRs are not turned on for the repository, so the PRs stay an ordinary chain of PRs, each based on the one below.
- Fetch each PR and check its base, head, commit tip, title, and body, and that `gh stack view --json` lists every branch in order with its PR number; report any branch whose `pr` is missing. For each PR, also check that `closingIssuesReferences` lists no issue its body does not close, and report what it lists; GitHub's docs do not say whether it is filled in for PRs above the bottom.
- Reply with every PR and the state of its checks, say that the PRs are open for review rather than drafts, and say that the stack must be rebased before it can merge whenever the default branch moves ahead of it.
- If publishing fails partway, keep every local branch and the approved drafts, report what was pushed and opened, and keep the request open.

Opening the PRs does not authorize merging, force-pushing, or further changes. If the user later asks to merge, use `gh stack merge <PR number> --yes`, which merges that PR and every unmerged PR below it; `gh pr merge` cannot merge a stack.

## Keep the stack up to date

When PRs at the bottom merge (merging a PR also lands every unmerged PR below it), GitHub rebases the remaining branches itself so the lowest open PR targets the default branch, and the local branches fall behind the remote. GitHub's docs suggest `gh stack sync` here; this skill runs its steps separately so that no force-push happens before the user approves it. A stack also needs a linear history to merge: it loses it when the default branch moves ahead or a lower branch gets new commits, and `gh stack view --json` then marks the branches with `needsRebase`. Rebase locally as below rather than with the **Rebase stack** button on GitHub: GitHub's docs disagree on whether that button signs its commits.

1. **Find what changed:** check out the stack. Before fetching, note each remaining branch's local tip and its remote-tracking tip (`origin/<branch>`). Then fetch, fast-forward the local default branch to `origin/<default>` as in step 3 of the build (stop and ask if it cannot fast-forward), and run `gh stack view --json` to see which PRs merged and which branches need a rebase. Its PR states are only open, merged, and queued, so check each remaining PR with `gh pr view` too. If a PR was closed without merging, which blocks every PR above it, or a branch is marked `isQueued`, stop and ask. For each merged PR, check that every issue its body closes is now closed; GitHub's stack docs do not say how closing keywords behave for PRs above the bottom. Report any left open and propose closing them; close them only with the user's approval.
2. **Catch up with GitHub:** for each branch whose remote tip changed, such as after GitHub's own rebase, move the local branch to the new remote tip only if its local tip equals the remote-tracking tip noted before fetching, so it holds nothing unpushed: `git branch -f <branch> origin/<branch>`, or `git reset --hard origin/<branch>` for the checked-out branch when its working tree is clean. If it holds unpushed commits, stop and ask. This needs no push.
3. **Rebase only if needed:** if `gh stack view --json` still marks a branch with `needsRebase`, note each remaining branch's current tip, then run `gh stack rebase`, which fetches and rebases the remaining branches onto the default branch, dropping the merged commits. If it exits with code 7, a rebase is already in progress: stop and ask. On a conflict (exit code 3), resolve the files, stage them with `git add`, and run `gh stack rebase --continue`; stop and ask about any conflict that needs a decision, and if the user wants to start over, `gh stack rebase --abort` restores every branch. If it reports that the stack's base branch was deleted and asks to drop commits from an old base that did not merge, stop and ask; pass `--accept-base-change` only with the user's approval. Run the checks on each rebased branch. Do not use `gh stack sync`, which pushes without asking. If nothing needs a rebase, skip to step 6.
4. **Approval:** for each rebased PR, show the old and new tip, the commits now on the branch, the check results, and the conflicts resolved. Ask: "Force-push these N branches?" and stop.
5. **Publish:** push with `gh stack push`, whose per-branch `--force-with-lease` refuses to overwrite a branch that changed on the remote since the rebase fetched it.
6. **Verify:** check each PR's tip, base, and diff, and that `gh stack view --json` marks no branch with `needsRebase`, and reply with the PRs.
7. **Clean up:** once every PR in the stack has merged, propose `gh stack unstack --local` and deleting the local branches and the working files; do it only with the user's approval.

## Title and body

Use the repository's PR template if it has one; otherwise fill in [the PR body template](assets/pr-body.md).

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references or positions in the title.
- **Body:** written for a reviewer who has not seen the conversation, from that PR's own commits and real results only. Never invent results or issue links.
- **Verification:** list commands actually run on that PR's branch and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** each PR closes its own issue with `Closes #N` when it fully resolves it. GitHub links a closing keyword only while the PR targets the default branch, and closes the issue when that PR merges into it; a PR above the bottom targets another branch until the PRs below it merge. Use `Related to #N` with the relationship when a PR covers only part of an issue. Never close another PR's issue. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
