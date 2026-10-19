# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `handoff` | Keeps a root `HANDOFF.md` current so any session, worktree, or computer can resume: per-branch state, ranked work, pending approvals, issue handoffs, and verified Git checkpoints. Uses `commit` and `open-pr` | "Let's wrap up" at the end of a session |
| `open-pr` | Opens a GitHub PR after two approvals: a plan before any work, then the finished branch, title, and body before anything is pushed. Uses `commit` | "Open a PR for #12" |
| `propose-stack` | Proposes up to five PRs from a project's issues, milestones, `HANDOFF.md`, and docs, builds them together on one stack branch, and publishes each as its own branch and PR against the default branch after three approvals: the plan, the review, and the push. Rebuilds a dependent PR after the PR it needs is squash-merged. Uses `commit` | "Propose a stack of PRs" |

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
