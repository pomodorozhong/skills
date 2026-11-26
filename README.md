# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

Nine skills, in three groups. The full list, with what each one needs and a prompt to try it, is in [skills/README.md](skills/README.md).

- **Git and GitHub workflow:** `committing`, `opening-prs`, `proposing-stacks`, `applying-github-repo-defaults`
- **Project defaults:** `applying-python-defaults`, `applying-jupyter-defaults`, `applying-web-defaults`, `applying-macos-storage-defaults`
- **Skill authoring:** `auditing-skills`

## Install

Pick skills interactively:

```bash
npx skills add pomodorozhong/skills
```

Or install specific ones for all your agents:

```bash
npx skills add pomodorozhong/skills --skill committing --skill opening-prs --skill proposing-stacks --skill auditing-skills -g -y
```

`-g` installs for your user rather than the current project. To update, run the command again.

## Maintaining

How I back up and link these skills: [docs/maintaining.md](docs/maintaining.md).
