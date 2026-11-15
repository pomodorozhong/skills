---
name: macos-application-data-storage
description: "Design or review file storage for macOS apps: where app data, caches, logs, preferences, temporary files, and user-owned files go (~/Library/Application Support, Caches, Logs, UserDefaults, sandbox containers), and when to ask before migrating a legacy layout. Use when creating a macOS app, designing its storage, or changing code that decides where it stores files, not for a feature that only reads or writes a file."
---

# macOS application data storage

Use this skill when creating a macOS application, designing its storage model, or changing storage code in an existing application. Do not activate it for an unrelated feature that merely happens to read or write a file.

## Start with ownership and lifetime

Classify every stored item before choosing a path:

- User-owned content: recordings, documents, media, exports, and other files the user expects to find and manage. Keep these in the user-selected project/content location. Do not hide them in the app container just because the app created them.
- Durable app-managed state: databases, job records, imported working copies, indexes, migrations, and other state needed by the app but not intended as user documents. Store it under the per-user Application Support directory.
- Regenerable data: thumbnails, previews, waveform envelopes, downloaded models, and derived indexes. Store it under the per-user Caches directory and make deletion safe.
- Logs: diagnostic logs under the per-user Logs directory, or use the platform's unified logging system for a native macOS app. Never treat logs as user documents.
- Preferences: small settings only, using UserDefaults or the platform preferences mechanism. Do not put media, databases, caches, or job payloads in preferences.
- Short-lived intermediates: use the system temporary directory and clean them up when possible. Never use a repository `tmp/` directory as an application-wide temporary store.

On macOS, the conventional roots are:

```text
~/Library/Application Support/<app-namespace>
~/Library/Caches/<app-namespace>
~/Library/Logs/<app-namespace>
```

For a packaged GUI application, prefer a stable reverse-DNS bundle identifier as the namespace when appropriate. For a Python or other cross-platform application, use a platform-aware path library rather than hardcoding macOS paths, and inject the path provider so tests can use temporary directories.

If the application is sandboxed, use the container locations provided by the OS and entitlements. Do not manually pretend to be sandboxed by inventing a container path.

## Preserve user-owned paths

User-selected source and export paths are part of the project model, not disposable app state.

- Keep source files where the user opened or saved them unless the user explicitly requests an import or move.
- If outputs are naturally project artifacts, a clearly named directory beside the source—such as `exports/`—is a reasonable default.
- Offer an explicit custom output directory when large files or shared volumes make the default unsuitable.
- Resolve and validate custom paths, create directories on demand, and report actionable errors for read-only or unavailable volumes.
- Save the chosen path with the project/session when future actions must continue using it.
- Do not silently redirect an existing project because a new default or command-line option changed. Existing saved paths should win; migration must be explicit.

## Use one path policy

Centralize path decisions in one resolver or service. Callers should ask for categories such as `app_data`, `cache`, `logs`, `temp`, or `project_exports` instead of rebuilding paths independently.

The resolver should:

1. Apply the platform convention and a stable app namespace.
2. Create directories only when needed.
3. Keep durable, regenerable, and temporary data separate.
4. Support dependency injection or an equivalent override for tests and embedding.
5. Distinguish a user override from a fallback. A fallback must never overwrite or conceal the user's explicit choice.

## Existing applications: prompt before broadening scope

When the current task changes storage, first inspect the existing path policy and classify its directories. Look for repository-relative `tmp/`, `cache/`, `logs/`, or `uploads/` paths, hardcoded home-directory paths, media stored in preferences, and generated artifacts mixed with user documents.

If the application is not following the categories above, explicitly prompt the user to consider reworking the storage code before implementing the requested storage change. Use a concise choice such as:

> The existing app stores [items] under [current path], which mixes [lifetime/ownership categories] and does not follow the macOS layout. Since this task already changes storage, should we include a cleanup/migration, or keep the scope limited and preserve the current layout for now?

Do not silently expand the task or migrate data. If the user declines, keep the requested change focused and document the known layout debt. If the user approves, treat migration as a first-class part of the work:

- inventory existing locations and versions;
- define the old-to-new mapping and compatibility behavior;
- preserve existing user files and saved project paths;
- make the migration idempotent, recoverable, and explicit;
- handle missing, read-only, partial, and interrupted migrations;
- add tests for fresh installs, upgrades, custom paths, and existing projects;
- document what is safe to delete and what is not.

## Verification checklist

Before handing off storage work, verify that:

- no application-owned runtime files are written into the repository or current working directory;
- caches and temporary files can be deleted without losing user content;
- logs do not contain secrets or large payloads by default;
- custom paths work with paths that contain spaces, on removable volumes, and in read-only failure cases;
- existing projects retain their recorded paths;
- path resolution is testable without mutating the real home directory;
- the implementation uses the host platform's conventions and does not assume macOS paths on other platforms.
