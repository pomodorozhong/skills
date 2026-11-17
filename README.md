# skills

Agent skills I use with Claude Code and Codex. Each one is a folder under `skills/` with a `SKILL.md`, so they work with any agent that reads that format.

## Skills

| Skill | What it does | Try it |
| --- | --- | --- |
| `auditing-skills` | Audits skills in any repository (a project's `.claude/skills/`, a skills repo, a plugin, or `~/.claude/skills`) against Anthropic's [skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Bundled scripts check what can be checked mechanically (frontmatter, links, reference depth, evals) and whether the guide changed since its checklist, by comparing section hashes instead of re-reading it. Then a point-by-point review reports verdicts with `file:line` evidence, draft evals, and ranked fixes. Read-only until you pick the fixes | "Audit the skills in this repo" |
| `committing` | Commits as atomic Conventional Commits, never on `main`/`master` or a merged branch | "Commit these changes" in a repo with a diff |
| `writing-handoffs` | Keeps a root `HANDOFF.md` current so any session, worktree, or computer can resume: per-branch state, ranked work, pending approvals, issue handoffs, stale branch cleanup, and verified Git checkpoints. Uses `committing` and `opening-prs` | "Let's wrap up" at the end of a session |
| `opening-prs` | Opens a GitHub PR after two approvals: a plan before any work, then the finished branch, title, and body before anything is pushed. Uses `committing` | "Open a PR for #12" |
| `proposing-stacks` | Proposes up to five PRs from a project's issues, milestones, `HANDOFF.md`, and docs, builds them as a stack of branches with the [`gh stack`](https://github.com/github/gh-stack) extension, and publishes them as stacked PRs after three approvals: the plan, the review, and the push. Keeps the stack up to date after a PR in it merges or the default branch moves ahead. Uses `committing`; needs `gh stack` | "Propose a stack of PRs" |

At wrap-up, `writing-handoffs` deletes local branches that are already merged (including squash merges), left over, or superseded, and asks before deleting remote branches. To keep merged branches from piling up on GitHub in the first place, turn on **Settings → General → Pull Requests → Automatically delete head branches** in each repository, or run `gh repo edit --delete-branch-on-merge`.

## Install

Pick skills interactively:

```bash
npx skills add pomodorozhong/skills
```

Or install specific ones for all your agents:

```bash
npx skills add pomodorozhong/skills --skill committing --skill writing-handoffs --skill opening-prs --skill proposing-stacks --skill auditing-skills -g -y
```

`-g` installs for your user rather than the current project. To update, run the command again. Install `auditing-skills` with `-g` to audit project skills in any other repository.

## Maintaining

How I back up and link these skills: [docs/maintaining.md](docs/maintaining.md).
