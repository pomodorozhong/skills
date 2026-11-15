# Migrating a storage layout

How to move an existing app's stored data to the layout [the skill](../SKILL.md) describes. Read this only after the user has approved a cleanup or migration.

Treat the migration as a first-class part of the work:

- inventory existing locations and versions;
- define the old-to-new mapping and compatibility behavior;
- preserve existing user files and saved project paths;
- make the migration idempotent, recoverable, and explicit;
- handle missing, read-only, partial, and interrupted migrations;
- add tests for fresh installs, upgrades, custom paths, and existing projects;
- document what is safe to delete and what is not.
