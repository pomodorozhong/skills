---
name: opening-prs
description: Turn a requested change into a GitHub PR with two approvals, a detailed plan before any work and the finished branch, title, and body before anything is pushed. Use whenever a PR is about to be opened: when the user asks to open, file, create, or make a PR, approves or edits a PR draft, or before running `gh pr create`, even if a draft was written earlier without this skill. Not for PRs opened by another skill that has its own approval steps. Requires `committing` installed alongside this skill.
---

# Open a PR

Turn a requested change into a GitHub PR with two approvals: the user approves a detailed plan before any work, then approves the finished branch before anything is pushed. Approving the plan never authorizes a push.

Ask for each approval in chat and wait for a reply; silence is not approval. An unanswered request stays open: name it again in any later status or closing report until the user answers.

**Already approved:** if the user already approved this exact branch tip and a body this skill wrote and showed in a step 4 summary (for example, in a recorded pending request), go straight to step 5. Approval of a draft written without this skill doesn't count; start at step 1.

## 1. Gather context

A PR draft written earlier without this skill is not approved: start here, and in step 4 rewrite it following [Title and body](#title-and-body), keeping any wording or changes the user asked for.

- Read the branch's linked issue (`gh issue develop --list <N>`) and the working tree, commits, and full diff against the default branch.
- Fetch the default branch and report how far the branch is behind and ahead (`git rev-list --left-right --count origin/<default>...HEAD`).
- Check whether this branch already has a PR, including merged or closed ones. If an open PR covers the same work, show it and ask before making another.
- List the issues that merging will close: those linked to the branch (`gh issue develop --list <N>`) and those named with `Closes #N`. GitHub closes linked issues on merge whatever the body says.
- Search issues, closed ones included, for other related issues and read the likely matches. If the search fails, say so instead of claiming there are none.
- Change nothing in this step.

## 2. Plan approval (only when work is missing)

If the changes already exist, skip to step 4.

Otherwise show a plan detailed enough to catch a wrong task before any work starts:

- The change: what will behave differently, and which files or components it touches.
- The issue it covers, and whether it fully resolves it.
- The branch: reuse the current one, or create one following the repo's conventions in its `AGENTS.md` or contributing docs (default `<type>/<summary>`, linked to its issue only if the PR will fully resolve it). Pick the type with the `committing` skill's commit type guide and give a one-line reason, since the branch, the commits, and the title all use it.
- The checks that will be run.
- Assumptions, and questions that block the plan.

Stop and wait for "go" or edits. Apply precise edits without asking again; show the revised plan for substantive ones.

## 3. Build

- Implement the approved plan only. Load the `committing` skill before the first commit, then follow it for staging, splitting, commit messages, and branch safety.
- Preserve unrelated changes. If the branch's PR has merged or closed, follow the committing skill's fresh-branch rule.
- Rebase only unpublished commits, and only when it helps; being behind the default branch is not a reason by itself.
- Run the project's documented checks on the final branch. Report failures; do not bypass hooks.

## 4. Publish approval

Write the title and body following [the rules below](#title-and-body), then show:

- Branch, base, and how far behind and ahead.
- Commits (short hash and subject).
- Check results, including failed, skipped, or not run.
- Differences from the approved plan.
- Draft or ready status.
- The issues that merging will close, including ones closed only by a branch link. If the PR won't fully resolve one of them, say so and propose removing the branch link before publishing (the `deleteLinkedBranch` GraphQL mutation, or the issue's Development sidebar).
- The title and full body.

Show all of this in the closing message text of the turn, followed by the question. Never leave it above a box or panel that may hide it.

Ask: "Push and open this PR?" and stop.

## 5. Publish and verify

- Immediately before publishing, confirm the branch tip still matches what was approved and that no PR for this branch exists now. Any change to the branch needs a new approval.
- Push without force. Create the PR with `gh pr create --body-file <file>` holding the exact approved body. Add no labels, reviewers, or comments that were not shown.
- Fetch the PR and check its base, head, commit tip, title, and body, and that `closingIssuesReferences` lists only the issues shown for approval. Reply with the PR as a Markdown link and the state of its checks.
- If publishing fails, keep the local branch and the approved draft, and report the failure with the request still open.

Opening a PR does not authorize merging, force-pushing, or further changes.

## Title and body

Use the repository's PR template if it has one; otherwise fill in [the PR body template](assets/pr-body.md).

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references in the title. Check the type with the `committing` skill's commit type guide even when the branch and commits already exist; if the commits or branch name use another type, say so in the step 4 summary and propose fixing them.
- **Body:** written for a reviewer who has not seen the conversation, from the final diff and real results only. Never invent results or issue links.
- **Verification:** list commands actually run and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** use `Closes #N` only when the PR fully resolves the issue and targets the default branch; otherwise use `Related to #N` with the relationship, and make sure the branch isn't linked to that issue. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
