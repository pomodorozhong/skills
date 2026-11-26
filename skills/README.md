# Skills

Each folder here is one skill: a `SKILL.md` plus any scripts, references, and assets it uses. To install them, see the [root README](../README.md#install).

## Git and GitHub workflow

| Skill | What it does | Needs | Try it |
| --- | --- | --- | --- |
| [`committing`](committing/SKILL.md) | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch, and leaves unrelated changes alone. | | "Commit these changes" in a repo with a diff |
| [`opening-prs`](opening-prs/SKILL.md) | Opens a GitHub PR after two approvals: a plan before any work, then the finished branch, title, and body before anything is pushed. | `committing`, `gh` | "Open a PR for #12" |
| [`proposing-stacks`](proposing-stacks/SKILL.md) | Proposes up to five PRs from a project's issues, milestones, handoff notes, and docs, builds them as a stack of branches with the [`gh stack`](https://github.com/github/gh-stack) extension, and publishes them as stacked PRs after three approvals: the plan, the review, and the push. Keeps the stack up to date after a PR in it merges or the default branch moves ahead. | `committing`, `gh stack` | "Propose a stack of PRs" |
| [`applying-github-repo-defaults`](applying-github-repo-defaults/SKILL.md) | Checks a GitHub repository's settings against a set of defaults (squash-only merging, deleting merged branches, a ruleset that protects the default branch, secret scanning, a read-only Actions token, a description) with a bundled script, and applies the fixes you approve in one go. Settings GitHub doesn't offer for the repo, such as rulesets on a free private repo, are reported, not fixed. Edit `assets/defaults.json` to change the defaults. | `gh` with admin access | "Check this repo's GitHub settings" |

## Project defaults

These set the tools and layout an agent reaches for when you haven't said otherwise.

| Skill | What it does | Needs | Try it |
| --- | --- | --- | --- |
| [`applying-python-defaults`](applying-python-defaults/SKILL.md) | Uses `uv` for Python projects, dependencies, scripts, tests, and tools, with Homebrew as the fallback. | | "Set up a Python project for this script" |
| [`applying-jupyter-defaults`](applying-jupyter-defaults/SKILL.md) | Writes notebooks that teach and render well on GitHub: Markdown next to the code it explains, static plots, few widgets. | `applying-python-defaults` | "Make a notebook that explains this dataset" |
| [`applying-web-defaults`](applying-web-defaults/SKILL.md) | Uses npm, Tailwind CSS, and a standard project layout for web projects such as Vite, React, or Next.js apps and static sites. | | "Start a small Vite site" |
| [`applying-macos-storage-defaults`](applying-macos-storage-defaults/SKILL.md) | Decides where a macOS app keeps its data, caches, logs, preferences, temporary files, and user files, and asks before migrating an old layout. | | "Where should this Mac app store its cache?" |

## Skill authoring

| Skill | What it does | Needs | Try it |
| --- | --- | --- | --- |
| [`auditing-skills`](auditing-skills/SKILL.md) | Audits skills in any repository (a project's `.claude/skills/`, a skills repo, a plugin, or `~/.claude/skills`) against Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Bundled scripts check what can be checked mechanically (frontmatter, links, reference depth) and whether the guide changed since its checklist, by comparing section hashes instead of re-reading it. Then a point-by-point review reports verdicts with `file:line` evidence, draft evals, and ranked fixes. Read-only until you pick the fixes. Install it with `-g` to audit project skills in any repository. | | "Audit the skills in this repo" |

## Dependencies

A skill that needs another one says so in its description. Install both together, for example `--skill opening-prs --skill committing`.
