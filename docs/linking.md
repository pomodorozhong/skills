# Maintaining these skills: the linking flow

For the repo owner. To just use the skills, see the [README](../README.md).

This repo is the installation: [`scripts/link.sh`](../scripts/link.sh) links each skill folder into the folders Codex (`~/.agents/skills`) and Claude Code (`~/.claude/skills`) read. Editing a skill anywhere, by hand or by an agent, edits it here, so there is nothing to copy. Backing up is commit and push. Based on [Back up and install Codex and Claude Code skills from one Git repo](https://github.com/pomodorozhong/rabbit-holes/blob/master/topics/agent_skills/backup-and-restore.md).

## Layout

- `skills/`: shared by every agent, and what `npx skills add` installs
- `codex-only/`, `claude-only/`: linked into one agent only (create when needed)
- `scripts/link.sh`: creates and prunes the links; safe to re-run

## Set up a machine

```bash
git clone https://github.com/pomodorozhong/skills.git ~/repo/skills
cd ~/repo/skills
scripts/link.sh --dry-run
scripts/link.sh
```

The dry run prints every change first. `link.sh` never deletes: an existing skill folder it replaces is moved to `~/skills-link-backup/<timestamp>-<pid>/`, and an old copy in `~/.codex/skills` is moved there too so Codex doesn't list the skill twice.

Check with `ls -l ~/.agents/skills ~/.claude/skills`: each skill should point into this repo. Then start a new session and type `/` (Claude Code) or `$` (Codex).

Don't move or delete this folder after linking; the links point into it. If you do, re-run `scripts/link.sh` from the new location.

## Daily use

- **Edit a skill:** edit it in place, then commit and push.
- **Add a skill:** create `skills/<name>/SKILL.md`, then run `scripts/link.sh`.
- **Remove a skill:** delete its folder, then run `scripts/link.sh` to remove its links.
- **Get changes from another machine:** `git pull`. Run `scripts/link.sh` too if skills were added or removed.

## The checked-out branch is live

The agents read the skills from this folder as it is on disk, so whichever branch is checked out is the version they use. Keep `main` checked out here, and merge skill branches promptly.
