# skills

My agent skills, shared by every agent. Each skill is a folder under `skills/` with a `SKILL.md`.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `wrap-up` | Ends a session: issue handoff notes, `.agents/next-steps.md`, docs, commit, parked approvals | "Let's wrap up" at the end of a session |

## Install

```bash
npx skills add pomodorozhong/skills --skill commit --skill wrap-up -g -y
```

This installs copies; re-run it to pick up changes pushed here.
