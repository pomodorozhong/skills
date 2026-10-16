# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `handoff` | Keeps a root `HANDOFF.md` current so any session, worktree, or computer can resume: per-branch state, ranked work, pending approvals, issue handoffs, and verified Git checkpoints. Also opens PRs after you approve a plan and then the finished branch | "Let's wrap up" at the end of a session, or "Open a PR for #12" |

## Install

Pick skills interactively:

```bash
npx skills add pomodorozhong/skills
```

Or install specific ones for all your agents:

```bash
npx skills add pomodorozhong/skills --skill commit --skill handoff -g -y
```

`-g` installs for your user rather than the current project. To update, run the command again.

## Maintaining

How I back up and link these skills: [docs/maintaining.md](docs/maintaining.md).
