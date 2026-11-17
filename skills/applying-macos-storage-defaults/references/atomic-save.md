# Saving a file safely

How to save a user's file so an interrupted save leaves the previous version intact. [The skill](../SKILL.md) says when to read this.

Write the new file completely on the same volume as its destination, then replace the destination in one rename. A rename cannot cross volumes, so do not write in the system temporary directory and move the result to a user folder that may be on another drive.

## Native app

Use `data.write(to: destination, options: .atomic)`, `NSDocument`, or a directory from `FileManager.default.url(for: .itemReplacementDirectory, in: .userDomainMask, appropriateFor: destination, create: true)` with `FileManager.default.replaceItemAt(destination, withItemAt: newFile)`; `replaceItemAt` also keeps the original file's permissions, extended attributes, and Finder tags.

## Cross-platform app

1. Resolve the destination through any symlinks first, so the save replaces the real file instead of turning the link into a separate copy.
2. Create the temporary file in that resolved file's directory, write it, flush it, and `fsync` it.
3. Copy the original file's permissions and extended attributes (which hold Finder tags) onto the temporary file, because a rename gives the destination the temporary file's metadata.
4. Rename the temporary file over the destination with `os.replace` or `rename(2)`, then `fsync` the containing directory so the rename itself survives a power loss.
5. Delete the temporary file if any step fails.

A rename breaks hard links to the original file; if the app must keep them, write in place behind a backup copy instead.
