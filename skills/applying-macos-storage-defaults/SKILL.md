---
name: applying-macos-storage-defaults
description: "Design or review file storage for macOS apps: where app data, caches, logs, preferences, temporary files, and user-owned files go (~/Library/Application Support, Caches, Logs, UserDefaults, sandbox containers), and when to ask before migrating a legacy layout. Use when creating a macOS app, designing its storage, or changing code that decides where it stores files, not for a feature that only reads or writes a file."
---

# macOS application data storage

## Start with ownership and lifetime

Classify every stored item before choosing a path:

- User-owned content: recordings, documents, media, exports, and other files the user expects to find and manage. Keep these in the user-selected project/content location. Do not hide them in the app container just because the app created them.
- Durable app-managed state: databases, job records, imported working copies, indexes that cannot be rebuilt from data the app still has, migrations, and other state needed by the app but not intended as user documents. Store it under the per-user Application Support directory.
- Regenerable data: thumbnails, previews, waveform envelopes, and indexes that can be rebuilt from data the app still has. Store it under the per-user Caches directory and make deletion safe. The system may delete Caches contents when disk space runs low, so keep only data whose loss costs a rebuild, not a feature. Large downloads the app needs to work offline, such as models, belong in Application Support with an explicit way for the user to remove them. Exclude them from backups, because Time Machine backs up Application Support: set `URLResourceValues.isExcludedFromBackup` in a native app, or run `tmutil addexclusion` on the folder in a cross-platform app.
- Logs: diagnostic logs under the per-user Logs directory, or use the platform's unified logging system for a native macOS app. Never treat logs as user documents.
- Preferences: small settings only, using UserDefaults or the platform preferences mechanism. Do not put media, databases, caches, or job payloads in preferences. Read and write preferences only through that API: never edit the preference `.plist` files directly, because the system caches them and can overwrite or ignore direct edits.
- Short-lived intermediates: use the system temporary directory for scratch files that never become user files, and clean them up when possible. Never use a repository `tmp/` directory as an application-wide temporary store.
- Files being saved: write the new file completely on the same volume as its destination, then replace the destination in one rename, so an interrupted save leaves the previous version intact. A rename cannot cross volumes, so do not write in the system temporary directory and move the result to a user folder that may be on another drive. Before writing or changing save code, read [the safe-save guide](references/atomic-save.md).

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

macOS asks the user for permission the first time an app reads or writes Documents, Desktop, Downloads, iCloud Drive, removable volumes, or network volumes, whether or not the app is sandboxed. If the user declines, later access fails with "operation not permitted" and the system does not ask again. Design for this:

- Keep app-managed data out of these locations. The app's own folders in Application Support, Caches, and Logs never need this permission. Reading another app's data there or in `~/Library/Containers` does: since macOS 14 the system asks before an app reads data that belongs to other apps.
- Let the user choose project and export locations with an open or save panel. A location chosen that way is granted without a separate prompt, so prefer it over a default inside Documents.
- Make the first access to a protected location right after a user action that explains why, such as choosing a folder or starting an export, so any prompt appears while the user knows the reason. A background job may then keep using a location the user chose and the app already reached; it must not be the first to touch one, and must handle a denial without a prompt the user cannot see.
- In a bundled app, add the matching purpose strings to `Info.plist` (`NSDocumentsFolderUsageDescription`, `NSDesktopFolderUsageDescription`, `NSDownloadsFolderUsageDescription`, `NSRemovableVolumesUsageDescription`, `NSNetworkVolumesUsageDescription`) so the prompt says why the app asks. iCloud Drive has no purpose string of its own.
- A command-line tool or script that is not an app bundle has no `Info.plist`. macOS shows the prompt for, and saves the decision under, the app that launched it, such as Terminal, iTerm, or an IDE. Name that app when reporting a denial.
- Report a permission denial separately from other write errors: name the location and the app that holds the permission, point to System Settings > Privacy & Security > Files and Folders, and offer to choose another location.

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

Do not silently expand the task or migrate data. If the user declines, keep the requested change focused and document the known layout debt. If the user approves, read [the migration guide](references/migration.md) before planning the work.

## Verification checklist

Before handing off storage work, verify that:

- no application-owned runtime files are written into the repository or current working directory;
- caches and temporary files can be deleted without losing user content;
- logs do not contain secrets or large payloads by default;
- custom paths work with paths that contain spaces, on removable volumes, and in read-only failure cases;
- an interrupted save leaves the previous version of the user's file intact, including when the destination is on another volume;
- declining the privacy prompt for a protected location produces an actionable error, tested after `tccutil reset All <bundle-id>` (for a command-line tool, the bundle ID of the app that launches it, such as `com.apple.Terminal`);
- existing projects retain their recorded paths;
- path resolution is testable without mutating the real home directory;
- the implementation uses the host platform's conventions and does not assume macOS paths on other platforms.
