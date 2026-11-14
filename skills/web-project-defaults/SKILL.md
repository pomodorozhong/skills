---
name: web-project-defaults
description: Apply npm-first tooling and Tailwind CSS defaults when creating, configuring, or maintaining web projects. Use when package management, build scripts, local serving, or styling choices are in scope and the user has not requested a conflicting stack.
---

# Web Project Defaults

Use npm as the default toolchain whenever the project supports it:

- Manage dependencies and lockfiles with npm. Put repeatable build, development, check, test, and serving commands in `package.json` scripts.
- Serve projects through an npm script. For a static site without a framework server, prefer a local `serve` development dependency and expose it as `npm run serve`; do not use Python's HTTP server.
- Prefer locally installed CLI dependencies over global installs or recurring `npx` downloads.
- Do not mix package managers or lockfiles. Preserve an established non-npm package manager when changing it would be disruptive, unless the user asks to migrate.

Use Tailwind CSS as the default styling system:

- Install and build Tailwind through npm using the integration appropriate for the project's framework and Tailwind version.
- Prefer Tailwind utilities for layout, spacing, typography, responsive behavior, and interaction states.
- Keep custom CSS when it materially improves clarity or is needed for bespoke geometry, animation, browser behavior, or third-party integration.
- Avoid CDN-based Tailwind in maintained projects unless the user specifically requests a no-build prototype.

After setup or changes, run the relevant npm build and checks. When serving behavior changes, start the npm server and verify that the page and generated assets respond successfully.
