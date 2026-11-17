---
name: auditing-skills
description: Audit Agent Skills (folders with a SKILL.md) in any repository or skills folder against Anthropic's skill authoring best practices, and report each point with a verdict, file:line evidence, draft evals, and a ranked list of fixes. Use when the user asks to audit, review, lint, or check a skill, a project's skills (such as .claude/skills), or a skills repository, asks how their skills could be improved, or asks whether they follow the best practices. Not for writing a new skill from scratch.
---

# Audit skills

Check skills against [Anthropic's skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices) and report what to improve. The skills can live anywhere: a project's `.claude/skills/`, a skills repository, a plugin, or the user's personal skills folder. The audit is read-only: change nothing until the user picks the fixes.

The two scripts below live in this skill's own `scripts/` folder; run them with that folder's full path from wherever the skills being audited are.

Track these steps in the app's task list, or copy this checklist into your reply and tick it off:

```
Audit progress:
- [ ] 1. Find the skills and their rules
- [ ] 2. Check the guide is unchanged
- [ ] 3. Run the script checks
- [ ] 4. Read and judge each skill
- [ ] 5. Check the evals
- [ ] 6. Report
```

## 1. Find the skills and their rules

- Audit the skills the user names. Otherwise audit every skill in the current repository: step 3's script finds them at any depth from the repository root, including `.claude/skills/`, `.agents/skills/`, `skills/`, and plugin folders, and skips dependencies, build output, and worktrees.
- Read the repository's README, `AGENTS.md` or `CLAUDE.md`, contributing docs, and tests. They may set rules that override or add to the guide, such as "each skill can be installed on its own" or an approval rule for dependencies between skills.
- Note how each skill is used, because some points depend on it: a project skill that stays in its repository may link to the repository's docs, while a skill that is published or installed elsewhere must hold everything it needs. Note which agents load the skills (Claude Code, Codex, the API).

## 2. Check the guide is unchanged

[The checklist](references/checklist.md) is built from a snapshot of the guide. Check whether the guide changed since, without reading it:

```bash
python3 <this skill's folder>/scripts/check_guide.py
```

- **Up to date** (exit 0): audit with the checklist.
- **Changed** (exit 1): it lists the sections added, removed, or changed. Rerun with `--show` to print only those sections, read them, and audit any new or changed point too. Say in the report that the checklist needs updating. When working in this skill's own source repository, offer to update the checklist and then run `--update` to record the new snapshot; never run `--update` without updating the checklist first.
- **Could not fetch** (exit 2): audit with the checklist, and say in the report which snapshot date it used.

## 3. Run the script checks

```bash
python3 <this skill's folder>/scripts/check_skills.py <repository root, skills folder, or skill folder>
```

It decides the rules a script can: frontmatter limits, `SKILL.md` length, broken links, links into another skill or out of the skill folder, files reachable only through another reference or not at all, scripts no instruction names, long references without a table of contents, Windows paths, dated wording, identical files across skills, and missing evals. `--json` prints the findings as JSON. Exit code 1 means a hard rule is broken.

Use the findings as evidence for the checklist points, not as the audit itself: the script cannot judge content, and its wording checks are heuristics, so confirm each one by reading before reporting it. If Python 3 is not available, make the same checks by reading.

## 4. Read and judge each skill

Read every file of each skill in full, with line numbers: `SKILL.md`, references, assets, scripts, and agent metadata. Then go through [the checklist](references/checklist.md) point by point and give each a verdict:

- ✅ follows it
- ⚠️ partly, or a trade-off worth a look
- ❌ misses it
- N/A does not apply, with a few words on why

Back every ⚠️ and ❌ with `file:line` evidence and a concrete fix. When the repository's own rules or the way the skill is used (step 1) explain a choice, such as a project skill linking to the repository's docs, or a template copied so each skill installs on its own, name the trade-off instead of calling it a miss.

## 5. Check the evals

The guide asks for at least three evaluation scenarios per skill. Look for them in each skill's `evals/` folder and in the repository's tests. For each skill with fewer, draft three in the report, in the format of [this skill's own evals](evals/evals.json): two that exercise the skill's riskiest steps, and one near-miss request that should not trigger it. Write them to files only if the user asks.

## 6. Report

Fill in [the report template](assets/report.md) and show the whole report in the final message. Rank the fixes by impact for the effort: first what makes a skill fail, skip a step, or trigger at the wrong time; wording polish last. Then ask which fixes to make.

When the user picks fixes, make them under the repository's own rules (for example, propose a dependency change before making it), rerun step 3, and say what changed in the findings.
