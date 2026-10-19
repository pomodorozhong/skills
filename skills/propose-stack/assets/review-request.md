## Review request: [N] PRs on `[stack branch]`

Base `[short hash]`; `[default]` has moved [K] commits since.

[Stack summary: the goal these PRs move toward, in one to three sentences.]

## Branches

| # | Branch | Title | Issue | Depends on | Commits | Checks (rebuilt on `[default]`) |
|---|--------|-------|-------|------------|---------|---------------------------------|
| 1 | `[branch]` | [title] | Closes [#[N] [issue title]](https://github.com/[owner]/[repo]/issues/[N]) | None | `[first]..[last]` ([count]) | [check] ✅ [check] ❌ [failure] [check] ⏭️ [reason] |
| 2 | `[branch]` | [title] | Related to [#[N] [issue title]](https://github.com/[owner]/[repo]/issues/[N]) | 1 | `[first]..[last]` ([count]) | [check] ✅ |

## Changes since last review

[Step 6 only.]

- [Feedback]: [what changed, and in which PR]

## Differences from the approved plan

- **1:** [difference and why] / None.

## Details to check

- **[#]: [choice]:** chose [what you chose]; main alternative [alternative].

## Review steps

Most important first.

### [#]. [title]

```bash
git worktree add --detach [scratchpad]/pr-[#] [base]
git -C [scratchpad]/pr-[#] cherry-pick [prerequisite commits] [own commits]
[command to run]
```

Look at: [what to check, most important first].

## PR bodies (exact text)

### 1. [title]

Commits: `[short hash]` [subject], `[short hash]` [subject]

````markdown
[body]
````

### 2. [title]

[Same as above.]

[Question: step 5 asks for feedback; step 6 asks "Push these N branches and open the PRs?"]
