# Maintaining these skills: backup and linking

For the repo owner. To just use the skills, see the [README](../README.md).

This repo is the installation: [`scripts/link.sh`](../scripts/link.sh) links each skill folder into the folders Codex (`~/.agents/skills`) and Claude Code (`~/.claude/skills`) read. Editing a skill anywhere, by hand or by an agent, edits it here, so there is nothing to copy. Backing up is commit and push. Based on [Back up and install Codex and Claude Code skills from one Git repo](https://github.com/pomodorozhong/rabbit-holes/blob/master/topics/agent_skills/backup-and-restore.md).

## Layout

- `skills/`: every skill, linked into both agents, and what `npx skills add` installs. There are no per-agent folders: one version of each skill, for everyone.
- `scripts/link.sh`: creates and prunes the links; safe to re-run, and each run can be undone
- `scripts/import.sh`: backs up skills already installed in the agents' folders into this repo

## Back up skills you already have

Run this when skills exist only in the agents' folders: a skill written or installed before this repo, or on a machine that was never linked. It copies, it doesn't move or link, so nothing changes for the agents until you run `link.sh`.

```bash
scripts/import.sh
git status --short
```

It reads `~/.agents/skills`, `~/.codex/skills`, and `~/.claude/skills`, and skips Codex's bundled `.system` and Claude Code's `synced` folders. A skill goes to `skills/` when every installed copy of it is identical (files, contents, and executable bits), including when only one folder has it. It never overwrites a skill already in the repo.

When a name's copies differ, for example Codex and Claude Code each have their own `commit`, it is skipped and listed under `Not imported, installed copies differ:`. Decide which version to keep, merging the changes you want into it, move the other copies out of the agents' folders, and run `import.sh` again. If they are really different skills that share a name, rename one first.

Then, before linking and committing:

- **Delete other people's skills** from the repo (`import.sh` copies everything it finds); reinstall those with `npx skills add` instead.
- **Delete skills you don't want public:** this repo is public.
- **Check each `SKILL.md` and helper script** for secrets, private examples, and machine-specific paths.

Then run `scripts/link.sh --dry-run` and `scripts/link.sh` so the agents use the repo copies, and commit.

## Set up a machine

```bash
git clone https://github.com/pomodorozhong/skills.git ~/repo/skills
cd ~/repo/skills
scripts/link.sh --dry-run
scripts/link.sh
```

The dry run prints every change first. `link.sh` never deletes: an existing skill folder it replaces is moved to `~/skills-link-backup/<timestamp>-<pid>/`, and an old copy in `~/.codex/skills` is moved there too so Codex doesn't list the skill twice. A run that changes something ends with the command to undo it.

Check with `ls -l ~/.agents/skills ~/.claude/skills`: each skill should point into this repo. Then start a new session and type `/` (Claude Code) or `$` (Codex).

Don't move or delete this folder after linking; the links point into it. If you do, re-run `scripts/link.sh` from the new location.

## Daily use

- **Edit a skill:** edit it in place, then commit and push.
- **Add a skill:** create `skills/<name>/SKILL.md`, then run `scripts/link.sh`.
- **Remove a skill:** delete its folder, then run `scripts/link.sh` to remove its links.
- **Get changes from another machine:** `git pull`. Run `scripts/link.sh` too if skills were added or removed.

## Undo a link run

Each run that changes something writes its run folder, `~/skills-link-backup/<timestamp>-<pid>/`, with a `changes.log` of every link it made, link it replaced (with the old target), and folder it moved aside. The last line of the run prints the exact command:

```bash
scripts/link.sh --undo ~/skills-link-backup/20261014-043257-60234 --dry-run
scripts/link.sh --undo ~/skills-link-backup/20261014-043257-60234
```

Preview first: the dry run lists every change and every `skip:`. Undo puts back the moved folders and the old links, and removes the links it made.

- **Undo the newest run first** when undoing several.
- **It never overwrites newer changes.** If something has changed since the run (a new folder where the original goes, a link pointing elsewhere), that item is skipped with `skip:`, the run folder is kept, and the undo exits with an error. Move the newer thing aside and run the same command again. A retry leaves already-restored folders alone and resumes an interrupted restoration of an old link.
- **A run that failed partway can be undone too:** it records each change before making it.
- **After a full undo,** `changes.log` becomes `changes.log.undone`, and the run folder can be deleted.

## Testing the scripts

```bash
python3 -m unittest discover tests
```

[`tests/test_scripts.py`](../tests/test_scripts.py) runs both scripts against throwaway repo and home folders with macOS's `/bin/bash`, so it never touches your real skills. It also syntax-checks the `bash` blocks in the README and this doc. Run it after changing either script.
