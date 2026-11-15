# Collect feedback, fold, and publish

Read this before acting on the user's answer to the review request (step 5 of [SKILL.md](../SKILL.md)): before committing the first fix in step 6, or before step 7's push question when the user had no feedback. The rules in SKILL.md still apply, including the working files; so do [the review request template](../assets/review-request.md) and [the title and body rules](build-and-review.md#title-and-body).

## 6. Collect feedback on the review branch

Review feedback can change a lot, so fixes collect on the review branch and are folded into the PRs once, in step 7. The PR branches do not change during this step.

- Commit each fix on the review branch as a fixup of a commit in the PR it belongs to: `git commit -m "fixup! $(git rev-parse <commit>)"`, where `<commit>` is that PR's commit the fix changes, or its last commit. Name the commit by its full hash, not with `--fixup`, which names it by subject: when two commits in the stack share a subject, the fold would squash the fix into the first one, possibly in another PR. Each fix commit belongs to one PR; split a fix that touches two. Follow the [commit](../../commit/SKILL.md) skill for staging and checks; the `fixup!` subjects disappear when the fixes are folded in.
- A fix is written on top of every PR, so it can accidentally depend on code from a PR above the one it belongs to. Make it use only code in its own PR or below, and say in the review when that is unclear.
- Run the checks ([step 4](build-and-review.md#4-check-each-layer)) on the review branch's tip.
- **Trial fold:** when this round has fixes for any PR below the top, fold them in a temporary detached worktree of the review branch's tip in the scratchpad: `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash --no-update-refs <base>`. Always pass `--no-update-refs`: with `rebase.updateRefs` set in the user's Git config, the trial would otherwise move the real PR branches. Folding removes only the fix commits, so PR k's new last commit is the commit at position (PR 1's commit count + … + PR k's commit count) in `git rev-list --reverse <base>..HEAD`; run the checks there, and remove the worktree. On a conflict, note the conflicting files and the PR the fix belongs to, run `git rebase --abort` in the trial worktree, and then remove it; `git worktree remove` refuses while the rebase is in progress. Report any conflict or failure in the review with the PR it belongs to.
- Show the same review as [step 5](build-and-review.md#5-review-request), with each PR's planned fixes, the trial fold's results, and what changed for each piece of feedback in the template's **Changes since last review** section. Update the titles and body files. Save it over the same review file.

Ask for more feedback, or whether the review is done, and stop. If the user gives more feedback, repeat this step. If the user had no feedback at all, there is nothing to fold: run `gh stack checkout <top branch>`, delete the review branch with `git branch -d`, and ask step 7's push question.

## 7. Fold the fixes and publish

### Fold the fixes into their PRs

- Before folding, record the review branch's tree (`git rev-parse <review branch>^{tree}`), and check with `git worktree list` that no PR branch is checked out in another worktree; `--update-refs` skips branches checked out elsewhere. If one is, stop and ask.
- On the review branch, run `GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash --update-refs <base>`, where `<base>` is the stack's base commit from `review.md`. It moves each fix next to its commit, squashes it in, and moves every PR branch to its rewritten last commit, without moving the stack onto a newer default branch. Nothing is pushed yet, so rewriting the branches is safe.
- On a conflict, resolve the files, stage them with `git add`, and run `git rebase --continue`; stop and ask about any conflict that needs a decision. `git rebase --abort` restores the review branch and every PR branch.
- Check that the top PR branch now has the recorded tree (`git rev-parse <top branch>^{tree}`) and that `git log <base>..<top branch>` lists no `fixup!` commits; if either fails, stop and show the difference. Then run `gh stack checkout <top branch>`, check that `gh stack view --json` marks no branch with `needsRebase` (if it does, run `gh stack rebase --no-trunk`), and delete the review branch with `git branch -d`.
- Repeat the checks (step 4) for every branch. Update the titles and body files from each PR's folded commits.
- Show the final review as in step 5, with each PR's new commit range and what folding changed. Save it over the same review file.

Ask: "Push these N branches and open the PRs?", naming the setting change too if it was approved, and stop. If the user gives more feedback, fix it on the PR's own branch (`gh stack checkout <branch>`, commit, then `gh stack rebase --upstack --no-trunk`), repeat the checks, and show the final review again.

### Publish and verify

- Immediately before publishing, confirm each branch tip still matches the last commit listed for it in the approved `review.md`, and that no PR exists for any of the branches and none of them exists on the remote yet (`git ls-remote --heads origin <branch>` prints nothing). `gh stack push` force-pushes with a lease, so it would overwrite a remote branch of the same name; if one exists, stop and ask. Any change needs a new approval. Do not rebase onto a newer default branch here; that changes what was approved.
- If the user approved turning on delete-branch-on-merge in the plan, turn it on first with `gh api -X PATCH repos/<owner>/<repo> -f delete_branch_on_merge=true` and check that it reads back `true`. If the call fails, such as without admin rights, report it and go on; the branches then stay on the remote until the clean-up.
- Push every branch with `gh stack push`.
- Open each PR bottom first with `gh pr create --base <branch below> --head <branch> --title "<approved title>" --body-file <working files>/body-<position>.md`, which holds the exact approved body. `gh stack submit --auto` would write its own titles and bodies, so the PRs are opened first. Add no labels, reviewers, or comments that were not shown.
- Check that every branch now has its open PR (`gh pr list --head <branch>`), then group them into a stack on GitHub with `gh stack submit --auto`. It finds the open PRs, so it creates none, keeps them ready for review, links them as a stack, and records each PR in the local stack. Do not use `gh stack link`, which is for branches managed by other tools and records nothing locally. If grouping fails, report it and leave the PRs open; exit code 9 means stacked PRs are not turned on for the repository, so the PRs stay an ordinary chain of PRs, each based on the one below.
- Fetch each PR and check its base, head, commit tip, title, and body, and that `gh stack view --json` lists every branch in order with its PR number; report any branch whose `pr` is missing. Check the grouping on GitHub too: `gh api repos/<owner>/<repo>/pulls/<N> --jq .stack` gives each PR's `position` and the stack's `size` and `number`, and is `null` for a PR that is not in a stack. For each PR, also check that `closingIssuesReferences` lists no issue its body does not close, and report what it lists; GitHub's docs do not say whether it is filled in for PRs above the bottom.
- Reply with every PR and the state of its checks, say that the PRs are open for review rather than drafts, and say that the stack must be rebased before it can merge whenever the default branch moves ahead of it.
- If publishing fails partway, keep every local branch and the approved drafts, report what was pushed and opened, and keep the request open.

Opening the PRs does not authorize merging, force-pushing, or further changes. For merging and keeping the stack up to date afterwards, read [the update reference](update-stack.md).
