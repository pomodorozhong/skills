---
name: propose-stack
description: Read a project's goals, plans, and progress (open issues, milestones, HANDOFF.md, README, docs), propose up to five PRs, build them as a stack of branches with `gh stack`, and publish them as a stacked set of PRs on GitHub after the user approves the plan, reviews the work, and approves the final branches. Also shows an overview of the current stack, and rebases the stack after a PR in it merges. Use when the user asks what to work on next as PRs, asks for a stack of PRs, asks to see the stack overview or status, or asks to update the remaining PRs after one merges.
---

# Propose a stack

Find the next few pieces of work from the project's own records, propose them as a set of PRs, and build them as a stack with the `gh stack` extension: each PR is its own branch built on the one below it, each PR targets the branch below it, and the bottom PR targets the default branch. GitHub shows the PRs as one stack and merges them bottom first. The user gives three answers before anything is pushed: the plan, review feedback on the built work, and the final publish approval. Approving the plan or giving feedback never authorizes a push.

Ask for each answer in chat and wait for a reply; silence is not approval. If the session ends before the user answers, keep the open request in the reply.

Show everything the user needs to decide (the plan, the questions, each PR's title and body, the review steps) in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

**Link every issue and PR:** whenever a message to the user mentions an issue or PR, write it as a Markdown link to its full URL with its title, such as `[#12 Add export](https://github.com/<owner>/<repo>/issues/12)`, taking the owner and repository from the remote it belongs to. This covers the proposal, the review, and the publish report. Never write a bare `#N`. PR and commit bodies on GitHub keep the plain `#N` form, which GitHub links itself and needs for closing keywords.

**Requires `gh stack`:** before running any `gh stack` command, check `gh stack --version`. If the extension is missing, stop and propose installing it with `gh extension install github/gh-stack`; install only with the user's approval.

**A PR in the stack has merged:** if the user asks to update the remaining PRs, or this skill starts while a stack it opened has a merged PR, go to [After a PR merges](#after-a-pr-merges).

**Stack overview:** if the user asks to see the stack, its overview, status, or where things stand ("show me the stack overview"), reply by filling in [the review request template](assets/review-request.md) with the stack's current state. Start from the saved `review.md` when there is one, but refresh anything that has changed since it was written from `gh stack view --json` and `git` (commits, check results, how far the default branch has moved, PR numbers and states once published), and save the refreshed version over it. Fill in only what exists so far: before step 5, mark the sections that come later as not yet reached rather than inventing them. Showing the overview answers no open question; end with whatever request is still open.

**GitHub unavailable:** distinguish a missing GitHub remote from an authentication or network failure, say which, and propose from the local docs only. Do not publish without GitHub.

**Working files:** everything this skill writes goes in `.agents/propose-stack/<summary>/` in the worktree that holds the stack, where `<summary>` names the stack's goal in a few words: the review request (`review.md`) and each PR's body (`body-<position>.md`). `gh stack` itself tracks the branches and their order. Keep the folder out of Git without ignoring the rest of `.agents/`: if `git ls-files .agents/propose-stack` lists anything, stop and ask where to write; otherwise, before the first write, add `/.agents/propose-stack/` to `info/exclude` in the Git common directory if it is missing, and confirm with `git check-ignore`. Only the temporary worktrees used for checks go in the scratchpad.

## 1. Gather context

Read, and change nothing:

- `README`, `AGENTS.md`, `CLAUDE.md`, `HANDOFF.md`, contributing docs, and the docs folder (`docs/` or `doc/`), including roadmaps, plans, and changelogs.
- Open issues with their labels, milestones, and comments; read closed issues only when an open one depends on them. Note `needs-decision` labels and "Blocked by #N" notes.
- Milestones and their descriptions: what each is for, what it waits on, and its due date.
- Open PRs, remote branches, and existing stacks (`gh stack view`), so the proposal does not repeat work already in flight.
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
- **Questions:** three to five, only about choices that are costly to change once built: public APIs and names, data and file formats, new dependencies, scope boundaries between PRs, stack order, and behavior users will rely on. Give your recommended answer for each. Skip anything cheap to change during review.

Stop and wait for answers and "go". Apply precise edits without asking again; show the revised plan for substantive ones.

## 3. Build the stack

- Fetch the default branch, then start the stack with `gh stack init --base <default> <first branch>`. Follow the [commit](../commit/SKILL.md) skill for staging, splitting, commit messages, and checks; it never pushes here.
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
- **Review steps:** how to try each PR (check out its branch in a detached worktree, then the commands to run and what to look at), most important first.
- **Details to check:** choices made while building that the plan did not settle and that could plausibly differ from the user's goal or taste, such as names, wording users will see, defaults, error behavior, file layout, and scope moved between PRs. For each, say what you chose and the main alternative.
- Differences from the approved plan.

Save each PR's body as `body-<position>.md` and the filled-in review request as `review.md` in the working files, replacing any earlier versions. The body files are the only saved copy of the bodies: in the saved `review.md`, each body section gives its file's path instead of the text. Give `review.md`'s path in the reply.

Ask for feedback and stop.

## 6. Apply feedback and final review

- Put each fix in the PR it belongs to: check out that branch (`gh stack checkout <branch>`), commit the fix there, then run `gh stack rebase --upstack` to carry it into every branch above. Nothing is pushed yet, so rewriting the branches is safe.
- Repeat the checks (step 4) for every changed branch and every branch above it. Update the titles and body files.
- Show the same review as step 5, plus what changed for each piece of feedback in the template's **Changes since last review** section. Save it over the same review file.

Ask: "Push these N branches and open the PRs?" and stop. If the user gives more feedback, repeat this step.

## 7. Publish and verify

- Immediately before publishing, confirm each branch tip still matches the last commit listed for it in the approved `review.md`, and that no PR exists for any of the branches. Any change needs a new approval. Do not rebase onto a newer default branch here; that changes what was approved.
- Push every branch with `gh stack push`.
- Open each PR bottom first with `gh pr create --base <branch below> --head <branch> --title "<approved title>" --body-file <working files>/body-<position>.md`, which holds the exact approved body. Open every PR ready for review, not as a draft. Add no labels, reviewers, or comments that were not shown.
- Group them into a stack on GitHub with `gh stack link <PR numbers, bottom first>`. If linking fails, report it and leave the PRs open.
- Fetch each PR and check its base, head, commit tip, title, and body, and that `gh stack view` shows all of them in order. For the bottom PR, also check that `closingIssuesReferences` lists only the issues its body closes; the others target a branch, so GitHub fills that in only once they are retargeted.
- Reply with every PR and the state of its checks. Keep the local branches and the stack's local tracking: [After a PR merges](#after-a-pr-merges) needs them.
- If publishing fails partway, keep every local branch and the approved drafts, report what was pushed and opened, and keep the request open.

Opening the PRs does not authorize merging (`gh stack merge`), force-pushing, or further changes.

## After a PR merges

A squash merge puts a PR's changes on the default branch as one new commit, so the branches above it still carry its original commits. Rebase them onto the updated default branch.

1. **Find what changed:** check out the stack and run `gh stack view` to see which PRs merged. If a PR was closed without merging, stop and ask.
2. **Rebase locally:** note each remaining branch's current tip, then run `gh stack rebase`, which fetches and rebases the remaining branches onto the default branch, dropping the merged commits. Resolve conflicts with `gh stack rebase --continue`, and stop and ask about any that needs a decision. Run the checks on each rebased branch. Do not use `gh stack sync`, which pushes without asking.
3. **Approval:** for each remaining PR, show the old and new tip, the commits now on the branch, the check results, and the conflicts resolved. Ask: "Force-push these N branches?" and stop.
4. **Publish:** push with `gh stack push`, whose per-branch `--force-with-lease` refuses to overwrite a branch that changed on the remote since the rebase fetched it.
5. **Verify:** check each PR's tip, base, and diff, and reply with the PRs.
6. **Clean up:** once every PR in the stack has merged, propose `gh stack unstack --local` and deleting the local branches and the working files; do it only with the user's approval.

## Title and body

Use the repository's PR template if it has one; otherwise fill in [the PR body template](assets/pr-body.md). Do not list the other PRs in the stack; GitHub shows the stack on each PR.

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references or positions in the title.
- **Body:** written for a reviewer who has not seen the conversation, from that PR's own commits and real results only. Never invent results or issue links.
- **Verification:** list commands actually run on that PR's branch and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** each PR closes its own issue with `Closes #N` when it fully resolves it; GitHub closes it when the PR's changes reach the default branch. Use `Related to #N` with the relationship when a PR covers only part of an issue. Never close another PR's issue. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
