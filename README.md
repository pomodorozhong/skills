# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `wrap-up` | Ends a session: issue handoff notes, `.agents/next-steps.md`, docs, commit, parked approvals | "Let's wrap up" at the end of a session |

## Install

Pick skills interactively:

```bash
npx skills add pomodorozhong/skills
```

Or install specific ones for all your agents:

```bash
npx skills add pomodorozhong/skills --skill commit --skill wrap-up -g -y
```

`-g` installs for your user rather than the current project. To update, run the command again.

## Maintaining

How I back up and link these skills: [docs/maintaining.md](docs/maintaining.md).
