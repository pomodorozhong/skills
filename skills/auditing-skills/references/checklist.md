# Skill audit checklist

A snapshot of [Anthropic's skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices), turned into points to check. The snapshot's date and hashes are in [guide-snapshot.json](guide-snapshot.json); `scripts/check_guide.py` says whether the guide has changed since. "Script" marks what `scripts/check_skills.py` checks; judge the rest by reading.

## Contents

- Core principles: 1–3
- Skill structure: 4–6
- Progressive disclosure: 7–9
- Workflows and feedback loops: 10–11
- Content: 12–13
- Common patterns: 14–16
- Evaluation and iteration: 17–19
- Anti-patterns: 20–21
- Skills with code: 22–25
- Beyond the guide: 26–27

## Core principles

1. **Concise.** Every paragraph earns its tokens; nothing explains what Claude already knows (what a PDF is, how git works, generic good practice). Look for background paragraphs, restated rules, and long rules that load on every run but serve only one path; move those behind a link.
2. **Degrees of freedom match the risk.** Fragile, order-sensitive work (migrations, history rewrites, publishing, deleting) gets exact commands and "do not change this" guardrails. Work with many good answers (reviews, layout, writing) gets heuristics, not scripts. Flag both mismatches: loose prose for a fragile step, rigid steps for a judgment call.
3. **Works on every model it targets.** Would Haiku find enough guidance, and does Opus get over-explained? Long conditional procedures are the usual Haiku risk. Note whether anything shows the skill was tried on more than one model.

## Skill structure

4. **Frontmatter (script).** `name`: at most 64 characters, lowercase letters, numbers, and hyphens, no XML tags, no "anthropic" or "claude". `description`: not empty, at most 1,024 characters, no XML tags.
5. **Naming.** Consistent pattern across the collection (gerund such as `processing-pdfs`, noun phrase, or action); not vague (`helper`, `utils`) or generic (`documents`). Weigh any rename against breaking installs.
6. **Description triggers well.** Says what the skill does and when to use it, in third person or as a plain statement, never "I" or "you" (script checks the voice and a when-clause). Includes the words a user would actually type (file types, tools, phrases). Holds only what helps choose the skill; process details belong in the body. Clear about near-misses it should not take.

## Progressive disclosure

7. **SKILL.md is an overview (script checks length).** Body under 500 lines; details that only some runs need live in separate files, organized by domain or by task, and the files are named for what they hold.
8. **References one level deep (script).** Every reference and asset is linked straight from `SKILL.md`, and every script is named by some instruction. A reference that sends the reader on to another reference risks a partial read; each reference should be complete for the step that loads it. Links into other skills' folders break when skills are installed separately, so name the other skill instead. Links out to the repository's own files are fine for a project skill that stays in its repository, but not for one published or installed elsewhere.
9. **Contents for long references (script).** A reference over 100 lines starts with a table of contents.

## Workflows and feedback loops

10. **Clear steps.** Multi-step work is numbered, in order, with a stop point at every approval. Long or multi-turn workflows give a checklist Claude copies and ticks off, so steps are not skipped and a later session can see where things stand.
11. **Feedback loops.** Quality-critical work runs a validator, fixes, and repeats until it passes: tests, a verification script, a re-read against a style guide, a check after publishing. Flag workflows that end without checking their result.

## Content

12. **Nothing goes out of date (script checks dated wording).** No logic keyed to a date ("until some month, use the old API"); old ways live in an "Old patterns" section. Also watch notes about current gaps in third-party docs or tools that will stop being true.
13. **One term per concept.** The same thing is always called the same name across `SKILL.md` and its files.

## Common patterns

14. **Templates.** Output with a fixed shape (reports, PR bodies, replies) has a template, as strict or as flexible as the use needs. Copies of one template across skills are kept in sync (script notes identical files).
15. **Examples.** Where style matters (commit messages, titles, reports), give concrete input and output pairs, not only a description of the style.
16. **Branching workflows.** Decision points route clearly ("Creating? → … Editing? → …"); large branches move into their own files.

## Evaluation and iteration

17. **Evals first (script counts them).** At least three scenarios per skill, each with a query, any files, and the expected behaviors, ideally with a no-skill baseline. Include one near-miss request that should not trigger the skill.
18. **Built from real use.** Rules trace back to observed failures, not imagined ones. Commit history and issues are evidence.
19. **Navigation works.** Files Claude never opens may be unneeded or poorly linked; a reference read on every run may belong in `SKILL.md`. Look for that from transcripts or tests when available.

## Anti-patterns

20. **No Windows paths (script).** Forward slashes only.
21. **One default, not a menu.** A single recommended tool or approach, with a named escape hatch, instead of a list of equal options.

## Skills with code

22. **Scripts for deterministic work.** Steps that should always run the same way (parsing, validating, sorting, rewriting a marked block, arithmetic on commit positions) are bundled scripts, not commands Claude rebuilds each time. Instructions say whether to run a script or read it. Scripts handle their own errors with clear messages and explain their constants.
23. **Verifiable intermediate outputs.** Batch, destructive, or high-stakes work writes a plan file first, validates it, then executes and verifies.
24. **Dependencies stated.** Required tools and packages (and versions) are named, checked, and installed only with approval; nothing assumes they are present.
25. **MCP tools fully named.** `ServerName:tool_name`, never a bare tool name.

## Beyond the guide

26. **Repository rules.** The repository's own rules for skills (step 1 of the skill), such as standalone installs or approval for dependencies between skills, are followed, and its tests cover what they can. A project skill does not repeat what the repository's always-loaded `CLAUDE.md` or `AGENTS.md` already says, and does not contradict it.
27. **Agent metadata.** When the repository targets other agents too (for example Codex `agents/openai.yaml`), each skill has the metadata the others have, and it agrees with the frontmatter.
