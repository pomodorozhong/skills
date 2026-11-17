# Project layout

How to organize files in a project. Avoid a flat layout, where many unrelated files sit side by side in one folder, and avoid deep nesting, where files are buried many folders down. [The skill](../SKILL.md) says when to read this.

## 1. Choose the layout in this order

1. **The project's existing layout.** Follow it in new code, even when it differs from this guide. Do not move files to match this guide unless the user asks; see [section 6](#6-change-an-existing-layout).
2. **The framework's conventions.** Some frameworks give folders meaning, such as `app/` in Next.js, `src/routes/` in SvelteKit, and `pages/` in Nuxt and Astro. Use those folders as the framework documents them, and apply the rules below to the code around them.
3. **The defaults in this guide,** for anything the first two leave open.

## 2. Keep the root for project files

The project root holds only what applies to the whole project: the manifest and lockfile, tool and framework config, `README`, `LICENSE`, CI config, and ignore files. Source code goes under `src/`. Other top-level folders each have one clear job:

- `public/` for static files served as they are (favicon, robots.txt, images referenced by URL);
- `docs/` for documentation longer than the README;
- `scripts/` for development and maintenance scripts that are not part of the app;
- `tests/` only for tests that span the whole app, such as end-to-end tests. Unit tests sit next to their code (see [section 4](#4-rules-for-every-folder)).

## 3. Grow the structure in stages

**Stage 1: group by type.** A new project starts with a few folders under `src/`, one per kind of code:

```text
src/
  components/
  lib/
  styles/
  main.ts
```

Add a type folder only when there is a file to put in it. Do not create empty folders in advance.

**Stage 2: group by feature.** Switch when either of these happens:

- a type folder holds more than about 10 files, or needs its own subfolders;
- a change to one feature regularly touches files in three or more type folders.

Then move each feature's code into its own folder, and keep only shared code in the type folders:

```text
src/
  features/
    auth/
      login-form.tsx
      login-form.test.tsx
      use-session.ts
      api.ts
    settings/
      ...
  components/   # used by two or more features
  lib/          # framework-independent helpers used by two or more features
  styles/       # global styles and design tokens
  main.ts
```

A file moves out of a feature folder into a shared folder only when a second feature needs it.

## 4. Rules for every folder

- **About 10 files at most.** When a folder grows past that, group its files into subfolders by feature or purpose. Count source files; a test or style file next to its source file does not count.
- **Three or four levels at most under `src/`.** If a path gets deeper, flatten the inner levels or split the feature.
- **Keep related files together.** A component's test, styles, and stories sit next to it with the same base name (`login-form.tsx`, `login-form.test.tsx`, `login-form.module.css`). Do not mirror `src/` in a separate test tree.
- **Name folders for what is inside.** No catch-all folders such as `misc/`, `common/`, `helpers/`, or `stuff/`. If `lib/` grows, split it by topic (`lib/dates/`, `lib/http/`).
- **One naming style.** Use the project's existing style for file and folder names; in a new project, use kebab-case (`user-profile/`, `format-date.ts`), unless the framework expects another style.
- **Few index files.** Add an `index.ts` that re-exports a folder's contents only when the folder is a feature with a clear public interface. Do not add one to every folder.

## 5. Other kinds of projects

The same rules apply outside web apps. Map the stages to the ecosystem's own conventions:

- **Libraries:** the public entry point at the top of `src/`, internal modules in folders under it.
- **Monorepos:** one folder per package or app under `packages/` or `apps/`, each with its own layout following this guide.
- **Other languages:** use the ecosystem's standard layout first, such as `src/<package>/` for Python or `cmd/` and `internal/` for Go, then apply sections 3 and 4 inside it.

## 6. Change an existing layout

Reorganizing breaks imports, makes history harder to follow, and conflicts with other open branches, so:

1. Propose the new layout to the user first, with the files that would move. Wait for approval.
2. Do the moves in their own commit, separate from other changes, with `git mv` so history follows the files.
3. Update imports, path aliases, and config that names paths (bundler, test runner, linter, `tsconfig.json`).
4. Run the build, tests, and checks, and fix anything the moves broke before committing.

## 7. Check before finishing

- No new file was added to a folder that already had about 10 source files.
- No new folder is deeper than four levels under `src/`.
- Tests and styles sit next to the code they belong to.
- Nothing new sits at the project root except project-wide files.
