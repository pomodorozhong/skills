# skills

My agent skills, shared by every agent. Each skill is a folder under `skills/` with a `SKILL.md`.

This repo is the installation: `link.sh` links each skill folder into the folders Codex (`~/.agents/skills`) and Claude Code (`~/.claude/skills`) read. Editing a skill anywhere, by hand or by an agent, edits it here, so there is nothing to copy. Backing up is commit and push. Based on [Back up and install Codex and Claude Code skills from one Git repo](https://github.com/pomodorozhong/rabbit-holes/blob/master/topics/agent_skills/backup-and-restore.md).

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `commit` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `wrap-up` | Ends a session: issue handoff notes, `.agents/next-steps.md`, docs, commit, parked approvals | "Let's wrap up" at the end of a session |

## Set up a machine

```bash
git clone https://github.com/pomodorozhong/skills.git ~/repo/skills
cd ~/repo/skills
./link.sh --dry-run
./link.sh
```

The dry run prints every change first. `link.sh` never deletes: an existing skill folder it replaces is moved to `~/skills-link-backup/<timestamp>-<pid>/`, and an old copy in `~/.codex/skills` is moved there too so Codex doesn't list the skill twice. Re-running it is safe.

Check with `ls -l ~/.agents/skills ~/.claude/skills`: each skill should point into this repo. Then start a new session and type `/` (Claude Code) or `$` (Codex).

Don't move or delete this folder after linking; the links point into it. If you do, re-run `./link.sh` from the new location.

## Daily use

- **Edit a skill:** edit it in place, then back it up:

  ```bash
  git add -A && git commit -m "chore: update skills" && git push
  ```

- **Add a skill:** create `skills/<name>/SKILL.md`, then run `./link.sh`.
- **Remove a skill:** delete its folder, then run `./link.sh` to remove its links.
- **Get changes from another machine:** `git pull`. Run `./link.sh` too if skills were added or removed.

Skills for one agent only go in `codex-only/` or `claude-only/` instead of `skills/`.

## Install copies instead

For a machine where you only use the skills and won't edit them, or where symlinks don't work:

```bash
npx skills add pomodorozhong/skills --skill commit --skill wrap-up -g -y
```

These copies don't follow the repo. Re-run the command to update, and don't edit them: changes there never reach this repo.
