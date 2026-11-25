---
name: applying-github-repo-defaults
description: Check a GitHub repository's settings against a set of defaults (squash-only merging, deleting merged branches, a default-branch ruleset, secret scanning, a read-only Actions token, a description) and apply the fixes the user approves. Use when a repository was just created or first worked on, or when the user asks to check, audit, or fix a repo's GitHub settings. Needs `gh` signed in with admin access to the repository.
---

# GitHub repo defaults

Check one repository's GitHub settings against the defaults in [assets/defaults.json](assets/defaults.json) and [assets/ruleset.json](assets/ruleset.json), and change only what the user approves. Checking changes nothing; every change to a setting needs approval, because repository settings affect everyone who uses the repository.

## 1. Check

Find the repository as `<owner>/<repo>`: from the user, or from `gh repo view --json nameWithOwner -q .nameWithOwner` in the current checkout. The script lives in this skill's own `scripts/` folder; run it with that folder's full path from wherever you are:

```bash
python3 <this skill's folder>/scripts/check_repo.py <owner>/<repo>
```

The script reads the settings with `gh api` and prints each setting that is not `ok`:

- `differs`: the current and wanted values, the reason, a `fix:` command, and sometimes a `note:`, such as what an update to an existing ruleset keeps. Show the note to the user with the row.
- `unavailable`: GitHub doesn't offer the setting for this repository, such as rulesets on a private repository on a free plan, or doesn't show it to you, such as security settings for someone without admin access. The note says which. Report it; there is nothing to fix.

Exit status 0 means nothing differs, 1 means something differs, and 2 means the repository couldn't be read; report the error instead of guessing. Add `--json` for machine-readable output.

## 2. Ask once

If nothing differs, say so, list any unavailable settings, and stop.

Otherwise show one table with a row per differing setting: the setting, its current value, the wanted value, and the reason. Then ask once for the whole list: "Apply these changes to `<owner>/<repo>`?" The user may approve all, some, or none. A `description` fix needs the text from the user; offer a one-line draft from the README, and use only text the user approved.

Never apply a change the user didn't approve, and never change a setting the script didn't report.

## 3. Apply and check again

Run each approved `fix:` command exactly as printed, in the order printed; the one exception is the `description` command, where the text the user approved replaces the placeholder inside the single quotes, with each `'` in the text written as `'\''` so the shell passes it unchanged. A ruleset fix that uses `PUT` updates an existing ruleset with the file the check just wrote, which keeps that ruleset's other rules and bypass actors; if that file is gone, run the check again first. The script prints `allow_squash_merge` before the other merge settings, because GitHub refuses to turn off every merge method at once. If a command fails, report its error and go on with the rest.

Then run the check again and report what changed, what still differs, and what is unavailable.

## Changing the defaults

To change what the skill checks, edit [assets/defaults.json](assets/defaults.json): each entry has the wanted value (`want`) and a one-line reason (`why`). Under `repo`, any top-level field of the [repository API](https://docs.github.com/rest/repos/repos#update-a-repository) works, such as `has_wiki`. The ruleset the check expects, and creates when it is missing, is [assets/ruleset.json](assets/ruleset.json).
