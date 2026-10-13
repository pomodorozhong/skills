# Maintaining these skills

This guide covers editing, backing up, and installing the skills in this repository on your own machines. To only install them, see the [README](../README.md). The approach follows [Back up and install Codex and Claude Code skills from one Git repo](https://github.com/pomodorozhong/rabbit-holes/blob/master/topics/agent_skills/backup-and-restore.md).

## How it works

[`scripts/link.sh`](../scripts/link.sh) links each skill in `skills/` into the folders the agents read:

```text
~/.agents/skills/commit  -> ~/repo/skills/skills/commit   (Codex)
~/.claude/skills/commit  -> ~/repo/skills/skills/commit   (Claude Code)
```

Both agents read the repository's files, so an edit made anywhere, by you or by an agent, is already in the repository. To back it up, commit and push. Every skill lives in `skills/`, which is also what `npx skills add` installs for other people.

## Set up a machine

```bash
git clone https://github.com/pomodorozhong/skills.git ~/repo/skills
cd ~/repo/skills
scripts/link.sh --dry-run
scripts/link.sh
```

Read the dry run before linking. `+ mv` lines are existing folders that will be moved aside, and `replacing link` lines show where an existing link pointed. `link.sh` never deletes: moved folders go to a run folder, `~/skills-link-backup/<timestamp>-<pid>/`. It also moves old copies out of `~/.codex/skills`, which Codex still reads, so skills aren't listed twice.

Check that each skill points into the repository:

```bash
ls -l ~/.agents/skills ~/.claude/skills
```

Then start a new session and type `/` in Claude Code or `$` in Codex to see the skills.

The links depend on the repository's location. If you move it, run `scripts/link.sh` again from the new location.

## Edit, add, and remove skills

- **Edit:** change the files in place, then commit and push. The agents use the edit right away.
- **Add:** create `skills/<name>/SKILL.md`, then run `scripts/link.sh`.
- **Remove:** delete the skill's folder, then run `scripts/link.sh` to remove its links.
- **Sync from another machine:** `git pull`. Run `scripts/link.sh` too if skills were added or removed.

## Keep `main` checked out

The agents read whatever is checked out in this folder, and they pick up changes immediately, even in open sessions. Switching branches switches the skills every agent runs: an unmerged change disappears when you leave its branch, and a half-finished one goes into use when you check it out.

- **Keep `main` checked out here,** and run `git pull` after each merge.
- **Make changes in a separate worktree,** so this folder never leaves `main`:

  ```bash
  git worktree add ../skills-wip -b fix/my-skill
  ```

  Edit, commit, and push from `../skills-wip`. The agents keep running `main` until the pull request merges and you pull. Afterwards, remove it with `git worktree remove ../skills-wip`.
- **If you edited through the links,** the change is uncommitted on `main` here. Run `git switch -c <branch>`, commit, push, and switch back to `main`. The agents use the previous version until the pull request merges and you pull; the edit is safe on its branch.

To see which version the agents are running:

```bash
git -C ~/repo/skills status -sb
```

## Import skills you already have

For skills installed before this repository existed, copy them from the agents' folders into `skills/`:

```bash
scripts/import.sh
git status --short
```

The script reads `~/.agents/skills`, `~/.codex/skills`, and `~/.claude/skills`, skipping the folders the tools manage (`.system` and `synced`). It copies rather than moves, and never overwrites a skill already in the repository.

Each skill has one shared version, so a name is imported only when all its installed copies are identical, executable permissions included. Names listed under `Not imported, installed copies differ:` need a decision: keep one version (merging in anything you want from the others), move the other copies out of the agents' folders, and run `import.sh` again. If they're different skills that share a name, rename one first.

Before committing the imported skills:

- Remove skills written by other people, and install those with `npx skills add` instead.
- Remove skills you don't want public; this repository is public.
- Check each `SKILL.md` and helper script for secrets and machine-specific paths.

Then run `scripts/link.sh --dry-run` and `scripts/link.sh`, and commit.

## Undo a link run

Each run that changes something records its changes in `changes.log` in its run folder, and ends by printing the command to undo it. Preview, then undo:

```bash
scripts/link.sh --undo ~/skills-link-backup/20261014-043257-60234 --dry-run
scripts/link.sh --undo ~/skills-link-backup/20261014-043257-60234
```

Undo moves folders back, restores previous links, and removes the links the run made. A run that stopped partway can be undone the same way.

- **Undo the newest run first** when undoing several.
- **Newer changes are never overwritten.** Anything changed since the run is skipped with a `skip:` line, and the run folder is kept. Move the newer item aside and run the same command again; the retry picks up where the last attempt stopped.
- **After a full undo,** `changes.log` becomes `changes.log.undone`, and you can delete the run folder.

## Test the scripts

Run the tests after changing either script. They use temporary folders and never touch your installed skills, and they also check that every `bash` block in the README and this guide is valid.

```bash
python3 -m unittest discover tests
```
