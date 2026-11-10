# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `handoff` | Keeps a root `HANDOFF.md` current so any session, worktree, or computer can resume: per-branch state, ranked work, pending approvals, issue handoffs, stale branch cleanup, and verified Git checkpoints. Uses `commit` and `open-pr` | "Let's wrap up" at the end of a session |
| `open-pr` | Opens a GitHub PR after two approvals: a plan before any work, then the finished branch, title, and body before anything is pushed. Uses `commit` | "Open a PR for #12" |
| `propose-stack` | Proposes up to five PRs from a project's issues, milestones, `HANDOFF.md`, and docs, builds them as a stack of branches with the [`gh stack`](https://github.com/github/gh-stack) extension, and publishes them as stacked PRs after three approvals: the plan, the review, and the push. Rebases the rest of the stack after a PR in it merges. Uses `commit`; needs `gh stack` | "Propose a stack of PRs" |

At wrap-up, `handoff` deletes local branches that are already merged (including squash merges), left over, or superseded, and asks before deleting remote branches. To keep merged branches from piling up on GitHub in the first place, turn on **Settings → General → Pull Requests → Automatically delete head branches** in each repository, or run `gh repo edit --delete-branch-on-merge`.

## Install

Pick skills interactively:

```bash
npx skills add pomodorozhong/skills
```

Or install specific ones for all your agents:

```bash
npx skills add pomodorozhong/skills --skill commit --skill handoff --skill open-pr --skill propose-stack -g -y
```

`-g` installs for your user rather than the current project. To update, run the command again.

## Maintaining

How I back up and link these skills: [docs/maintaining.md](docs/maintaining.md).
