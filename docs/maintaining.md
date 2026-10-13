# Maintaining these skills: backup and linking

For the repo owner. To just use the skills, see the [README](../README.md).

This repo is the installation: [`scripts/link.sh`](../scripts/link.sh) links each skill folder into the folders Codex (`~/.agents/skills`) and Claude Code (`~/.claude/skills`) read. Editing a skill anywhere, by hand or by an agent, edits it here, so there is nothing to copy. Backing up is commit and push. Based on [Back up and install Codex and Claude Code skills from one Git repo](https://github.com/pomodorozhong/rabbit-holes/blob/master/topics/agent_skills/backup-and-restore.md).

## Layout

- `skills/`: shared by every agent, and what `npx skills add` installs
- `codex-only/`, `claude-only/`: linked into one agent only (create when needed)
- `scripts/link.sh`: creates and prunes the links; safe to re-run
- `scripts/import.sh`: backs up skills already installed in the agents' folders into this repo

## Back up skills you already have

Run this when skills exist only in the agents' folders: a skill written or installed before this repo, or on a machine that was never linked. It copies, it doesn't move or link, so nothing changes for the agents until you run `link.sh`.

```bash
scripts/import.sh
git status --short
```

It reads `~/.agents/skills`, `~/.codex/skills`, and `~/.claude/skills`, and skips Codex's bundled `.system` and Claude Code's `synced` folders. A skill only one agent has, or both have identically, goes to `skills/`. A skill both have with different contents goes to both `codex-only/` and `claude-only/` and is printed as `DIFFERENT in each agent, review: <name>`: merge them into `skills/<name>` or keep both. It never overwrites a skill already in the repo.

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

The dry run prints every change first. `link.sh` never deletes: an existing skill folder it replaces is moved to `~/skills-link-backup/<timestamp>-<pid>/`, and an old copy in `~/.codex/skills` is moved there too so Codex doesn't list the skill twice.

Check with `ls -l ~/.agents/skills ~/.claude/skills`: each skill should point into this repo. Then start a new session and type `/` (Claude Code) or `$` (Codex).

Don't move or delete this folder after linking; the links point into it. If you do, re-run `scripts/link.sh` from the new location.

## Daily use

- **Edit a skill:** edit it in place, then commit and push.
- **Add a skill:** create `skills/<name>/SKILL.md`, then run `scripts/link.sh`.
- **Remove a skill:** delete its folder, then run `scripts/link.sh` to remove its links.
- **Get changes from another machine:** `git pull`. Run `scripts/link.sh` too if skills were added or removed.

## Gotcha: the checked-out branch is live

The links point at this folder's working tree, not at a branch. So `git switch` doesn't just change what you're editing: it changes which version of every skill your agents run, immediately, including in sessions that are already open (both agents pick up skill edits live).

Found while setting this up: the `wrap-up` change was committed on one branch, and switching to another branch to work on the README quietly put the old `wrap-up` back in front of both agents. Nothing looked wrong; the agents just followed the old instructions.

What it means in practice:

- **Branches undo unmerged work.** Switching to `main` or any other branch drops every skill change that isn't on it until you switch back or it merges.
- **A branch's experiment goes live.** Checking out a branch with a half-finished skill makes every agent use it, in every project.
- **Edits through the links land on whatever is checked out.** An agent editing `~/.claude/skills/<name>` edits this working tree, on the current branch.
- **A rebase, reset, or conflict mid-merge is live too.** Conflict markers in a `SKILL.md` are what the agents read until you resolve them.

How to work with it:

1. **Keep `main` checked out here** and `git pull` after merging, so the agents run what's merged.
2. **Change skills in a separate worktree** so this checkout never leaves `main`:

   ```bash
   git worktree add ../skills-wip -b fix/my-skill
   ```

   Edit, commit, and push there; the agents keep running `main` until the PR merges and you pull. Remove it afterwards with `git worktree remove ../skills-wip`.
3. **If you edited through the links** (the change is now uncommitted on `main` here), commit it the usual way: `git switch -c <branch>` carries the change over, commit and push, then `git switch main`. From that moment the agents run the old version again until the PR merges and you pull. That's expected, not a lost edit.
4. **To try a branch's version on purpose,** check it out here, and switch back to `main` when done.

Before trusting a skill's behavior, `git -C ~/repo/skills status -sb` shows which version the agents are running.

## Testing the scripts

```bash
python3 -m unittest discover tests
```

[`tests/test_scripts.py`](../tests/test_scripts.py) runs both scripts against throwaway repo and home folders with macOS's `/bin/bash`, so it never touches your real skills. It also syntax-checks the `bash` blocks in the README and this doc. Run it after changing either script.
