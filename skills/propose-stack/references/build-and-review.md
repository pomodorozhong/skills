# Build the stack and request a review

Read this after the user approves the plan (step 2 of [SKILL.md](../SKILL.md)) and before building anything. The rules in SKILL.md still apply: the `gh stack` requirements, running it non-interactively, the remote, finding the stack, and the working files.

## 3. Build the stack

- Fetch, then fast-forward the local default branch to `origin/<default>`, because `gh stack init` builds on the local branch: `git fetch origin <default>:<default>`, or `git merge --ff-only origin/<default>` where it is checked out. If it cannot fast-forward, stop and ask. Then run `git config rerere.enabled true` and start the stack with `gh stack init --base <default> <first branch>`. Follow the [commit](../../commit/SKILL.md) skill for staging, splitting, commit messages, and checks; it never pushes here.
- Build the PRs in order: commit each PR's work on its own branch, then `gh stack add <next branch>` to start the next one on top.
- Implement the approved plan only. If the plan turns out wrong (a PR is much bigger than expected, or needs a PR above it), stop and ask before changing the plan.

## 4. Check each layer

Then check each layer as [step 4 of SKILL.md](../SKILL.md#4-check-each-layer) describes.

## 5. Review request

Write each PR's title and body following [the rules below](#title-and-body), then fill in every section of [the review request template](../assets/review-request.md) and show it. For the template:

- The base is the stack's base commit (`git merge-base origin/<default> <bottom branch>`); count how far the default branch has moved since with `git rev-list --count <base>..origin/<default>`.
- Check results include checks that failed, were skipped, or were not run.
- **Details to check** are choices made while building that the plan did not settle and that could plausibly differ from the user's goal or taste, such as names, wording users will see, defaults, error behavior, file layout, and scope moved between PRs. For each, say what you chose and the main alternative.

Save each PR's body as `body-<position>.md` and the filled-in review request as `review.md` in the working files, replacing any earlier versions. Give `review.md`'s path in the reply.

Then create the review branch on top of the top PR branch: `git switch -c propose-stack/review-<summary> <top branch>`. Use plain `git`, not `gh stack add`: the review branch is not a layer, and `gh stack push` and `gh stack submit` must never push it.

Ask for feedback and stop. When the user answers, read [the fold and publish reference](fold-and-publish.md).

## Title and body

Use the repository's PR template if it has one; otherwise fill in [the PR body template](../assets/pr-body.md).

- **Title:** the concrete change in Conventional Commit style when that fits the repo. No issue references or positions in the title.
- **Body:** written for a reviewer who has not seen the conversation, from that PR's own commits and real results only. Never invent results or issue links.
- **Verification:** list commands actually run on that PR's branch and their outcomes, separately from checks not run and why. For user-visible changes, give reproducible steps with expected results, and mark which you ran (`Verified`) and which are left to the reviewer (`Reviewer follow-up`).
- **Issues:** each PR closes its own issue with `Closes #N` when it fully resolves it. GitHub links a closing keyword only while the PR targets the default branch, and closes the issue when that PR merges into it; a PR above the bottom targets another branch until the PRs below it merge. Use `Related to #N` with the relationship when a PR covers only part of an issue. Never close another PR's issue. Use `owner/repo#N` for other repositories. See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).
