# In-Memory File System

Design a hierarchical file system with paths, directories, files, and common mutations.

## Scope

Support create, read, write, list, move, and delete using absolute paths. Include directories and text files. Permissions, links, storage blocks, and crash recovery are follow-ups.

## Model

| Type | Responsibility |
|---|---|
| Entry | shared name, parent, and timestamps |
| File | byte/text content and size |
| Directory | named children and child invariants |
| Path | normalized immutable segments |
| FileSystem | resolves paths and coordinates cross-parent operations |

Key invariants: sibling names are unique; a directory cannot contain itself; root has no parent; moving a directory cannot create a cycle.

    Entry
      |-- File
      |-- Directory -> children: name to Entry

Composite is natural because directories recursively own entries, but operations unsupported by File should not be forced into the base contract.

## Path resolution

1. Parse and normalize the absolute path.
2. Start at root.
3. For each segment, require the current entry to be a directory.
4. Look up the next child by name.
5. Return the entry or a precise not-found/not-directory error.

Keep parsing separate from traversal. Decide explicitly how repeated separators, dot, and dot-dot behave.

## Mutations

Create changes one parent directory. Move changes the old and new parents and the entry’s parent pointer as one operation. Delete should define whether non-empty directories are rejected or recursively removed.

## Design decisions

- Directory owns name uniqueness.
- File owns content mutations.
- FileSystem coordinates operations involving multiple parents.
- A visitor is useful only when many cross-tree operations appear.
- A repository is unnecessary for a purely in-memory exercise.

## Correctness

Lock directories in stable path or identity order for concurrent move operations. Revalidate source and destination after locks are acquired. For persistence, journal or transact the multi-node mutation.

## Follow-ups

- Symbolic and hard links.
- Permissions and ownership.
- Quotas and storage blocks.
- Watchers for path changes.
- Snapshotting and crash recovery.

## Interview finish

Implement Path, Directory.add/remove, File.read/write, resolve(), move(), and tests for duplicate names, cycles, invalid paths, and non-empty deletion.
