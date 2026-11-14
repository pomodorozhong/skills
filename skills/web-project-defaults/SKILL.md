---
name: web-project-defaults
description: Apply npm-first tooling, Tailwind CSS, and project layout defaults when creating, configuring, or maintaining web projects, such as a frontend app, a static site, or a project with a `package.json` (Vite, React, Next.js, and similar). Use when package management, build scripts, local serving, styling, or file organization choices are in scope and the user has not requested a conflicting stack.
---

# Web Project Defaults

Use npm as the default toolchain whenever the project supports it:

- Manage dependencies and lockfiles with npm. Put repeatable build, development, check, test, and serving commands in `package.json` scripts.
- Commit `package-lock.json`. Use `npm install` when adding or changing dependencies, and `npm ci` for clean, repeatable installs such as CI or a fresh checkout.
- Serve projects through an npm script. Use the framework's own development server when there is one (for example `npm run dev` for Vite). For a static site without a framework server, prefer a local `serve` development dependency and expose it as `npm run serve`; do not use Python's HTTP server.
- Prefer locally installed CLI dependencies over global installs or recurring `npx` downloads. One-off scaffolding commands, such as `npm create vite@latest`, are fine.
- Respect the Node.js version the project declares in `.nvmrc`, `.node-version`, or the `engines` field of `package.json`. Do not change it unless the user asks.
- Do not mix package managers or lockfiles. If the project already uses pnpm, Yarn, or Bun (shown by its lockfile or the `packageManager` field), keep using it for scripts and builds, and do not migrate unless the user asks. Before installing, adding, or removing dependencies with that manager, pause and consult the user.

Use Tailwind CSS as the default styling system for new projects, or when the user asks for it:

- Keep an existing project's styling system, such as plain CSS, CSS Modules, Sass, CSS-in-JS, or a component framework like Bootstrap. Do not add Tailwind to it unless the user asks.
- Install and build Tailwind through npm using the integration appropriate for the project's framework and Tailwind version.
- Prefer Tailwind utilities for layout, spacing, typography, responsive behavior, and interaction states.
- Keep custom CSS when it materially improves clarity or is needed for bespoke geometry, animation, browser behavior, or third-party integration.
- Avoid CDN-based Tailwind in maintained projects unless the user specifically requests a no-build prototype.

Organize files as [the project layout guide](references/project-layout.md) describes: follow the existing and framework layouts first, avoid both flat folders and deep nesting, and propose any reorganization before moving files. Read it before creating a project or adding files or folders.

After setup or changes, run the relevant npm build and checks. When serving behavior changes, start the npm server in the background, verify that the page and generated assets respond successfully, and then stop the server unless the user wants it left running.
