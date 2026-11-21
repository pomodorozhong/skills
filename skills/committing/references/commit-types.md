# Choosing a commit type

Pick the type by the commit's main reason to change, as its user would see it. A user is whoever relies on the result: someone running the program, code that calls a library, or an agent following a skill.

## The types

| Type | Use when | Ask yourself |
| --- | --- | --- |
| `feat` | Users can do something new, or something they used to do now works differently or is gone. | Would the changelog tell users about it? |
| `fix` | Something behaved wrongly and now behaves as intended. | Was the old behavior a bug? |
| `perf` | The same behavior, measurably faster or lighter. | Is speed or resource use the only change? |
| `refactor` | The structure or names change and what everything does stays exactly the same. | Does everything work as before? A rename users must type differently is still `refactor`, marked breaking. |
| `docs` | Documentation for people changes, and nothing that runs or is followed does. | Is the file only read, never executed or followed? |
| `test` | Tests are added or changed, and the code under test is not. | Did only test files change? |
| `build` | The build, packaging, or dependencies change. | Is it about how the project is built or installed? |
| `ci` | The CI configuration or scripts change. | Does it only affect CI runs? |
| `chore` | Upkeep that fits nothing above, such as tool config or removing unused files. | Is it housekeeping with no effect on users? |
| `revert` | An earlier commit is undone. | Does it only undo a past commit? |

## Tricky cases

- **Removing a feature, command, or skill that people use:** `feat!` with a `BREAKING CHANGE:` footer. Removal changes behavior, so it is not `refactor`.
- **Removing dead code** that nothing calls: `refactor`. Removing unused files that are not code: `chore`.
- **Renaming something users call or type** (a command, a public function, a skill name): `refactor!` when it works exactly as before under the new name, with a `BREAKING CHANGE:` footer that gives the old and new names. If the rename also changes what it does, use `feat!`.
- **Files whose text is the product** (skill instructions, prompts, agent rules such as `AGENTS.md`): a change to what the agent does is `feat` or `fix`. Use `docs` only for text the agent does not act on, such as a README for people, and `refactor` only when the agent would behave exactly the same, such as moving steps into a reference file.
- **A fix that also adds an option:** pick the main reason. If the two parts could land on their own, split them into two commits.
- **Dependency bumps:** `build`, or `fix` when the bump is what fixes a user-visible bug.
- **Formatting or lint fixes only:** `chore`. Use `style` instead only if the repository's history already uses it.
- **Undoing an earlier commit:** `revert`, with the summary of the reverted commit, and a body that names its hash and says why it is undone. Use the type of the new work instead if the commit also replaces what it undoes.

## Breaking changes

Add `!` after the type or scope, plus a `BREAKING CHANGE:` footer, when users must change what they do: a removed or renamed command, option, function, or skill, a changed default they relied on, or a new requirement. Say in the footer what users need to do now.

Any type can be breaking. A breaking `refactor!` is a rename or move that works exactly as before; a breaking `feat!` changes or removes behavior.

For example, removing a skill:

```
feat(skills)!: remove the wrapping-up skill

writing-handoffs now covers everything wrapping-up did, and keeping both made agents pick the wrong one.

BREAKING CHANGE: wrapping-up is gone. Install writing-handoffs and use it instead.
```

Renaming a skill without changing what it does:

```
refactor(skills)!: rename commit to committing

Skill names now use the gerund form, like the rest of the collection.

BREAKING CHANGE: the commit skill is now committing. Reinstall it under the new name.
```
