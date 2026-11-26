# Agent instructions

Each skill under `skills/` is a folder of its own and installs without broken files: it never links into another skill's folder.

## Skill dependencies

A skill may depend on another skill outright, with no fallback for when the other one isn't installed. Fallback paths bloat a skill and make its behavior less predictable.

State each dependency at the end of the depending skill's description, in this wording: "Requires `<skill>` installed alongside this skill." List it in the Needs column of [skills/README.md](skills/README.md) too.

Never add or remove a dependency between skills (an instruction to use another skill, or a "Requires" note) silently. Propose it first with the reason, and make it only after the user approves.
