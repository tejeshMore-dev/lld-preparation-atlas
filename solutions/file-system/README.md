# In-Memory File System Low-Level Design

Maintain a recursive directory tree while resolving absolute paths and safely creating, reading, moving, renaming, and deleting entries.

## Understanding the Problem

Maintain a recursive directory tree while resolving absolute paths and safely creating, reading, moving, renaming, and deleting entries.

The design starts with the business invariant and the critical workflow. Named patterns come later, only where a requirement creates a real variation or boundary.

## Requirements

### Clarifying Questions

- Are paths absolute or relative?
- How are dot, dot-dot, and repeated separators handled?
- Can non-empty directories be deleted?
- Are links and permissions in scope?
- Must concurrent moves be safe?

### Final Requirements

1. Normalize and resolve absolute paths.
2. Create directories and text files.
3. Read, replace, append, and list.
4. Move and rename without collisions or cycles.
5. Delete files and explicitly handle non-empty directories.

The detailed reference below records additional assumptions, exclusions, validation rules, and edge cases.

## Core Entities and Relationships

| Entity | Responsibility |
|---|---|
| Path | Owns normalized immutable path segments. |
| Entry | Shared identity, name, parent, and metadata. |
| File | Owns content operations. |
| Directory | Owns uniquely named children. |
| FileSystem | Coordinates traversal and cross-parent mutations. |
| EntryVisitor | Optional extension for tree-wide operations. |

The object that owns mutable state also owns the invariant protecting that state. Coordinating services load collaborators and sequence the use case; they do not bypass entity behavior.

## Class Design

### Good Solution

Use File and Directory under a small Entry abstraction; keep path parsing separate from traversal.

### Great Solution

Use stable identity, controlled parent mutation, atomic cross-parent move with cycle checks, deterministic errors, and lock ordering.

### Final Class Design

The critical collaboration is: parse path -> resolve parent/entry -> validate type and invariant -> mutate one or two parents atomically -> return immutable result.

The full class map, state transitions, method contracts, and design rationale are preserved in the detailed reference below.

## Implementation

Implement one vertical slice before filling every class:

    parse path -> resolve parent/entry -> validate type and invariant -> mutate one or two parents atomically -> return immutable result

### Complete Code Implementation

This repository currently treats this problem as a Markdown design exercise. The contracts, algorithms, atomic boundaries, pseudocode, and complete verification plan are in the detailed reference below. Implement the entity that owns the main invariant first, then the coordinating service.

## Verification

Verify the happy path, the highest-risk rejection, and state after failure. Then force two competing operations at the atomic boundary and assert the invariant, not thread timing.

The detailed reference lists problem-specific test cases and complexity.

## Extensibility

- Permissions, ownership, and quotas
- Symbolic links and watchers
- Snapshots, journaling, and durable content

Each extension should enter through a named policy, boundary, or lifecycle change rather than a new conditional inside the main workflow.

## What Is Expected at Each Level?

### Junior

Deliver the agreed core workflow with coherent entities, valid state changes, and straightforward failure handling.

### Mid-level

Make invariants explicit, isolate real variations, cover failure paths with tests, and discuss the relevant concurrency boundary.

### Senior

Explain cycle prevention, atomic move/rollback, stable identity, concurrent lock order, unique parent/name constraints, and crash recovery.

## Interview Walkthrough

1. Clarify the version-one scope and exclusions.
2. State the invariants before drawing classes.
3. Introduce the core entities and walk: parse path -> resolve parent/entry -> validate type and invariant -> mutate one or two parents atomically -> return immutable result.
4. Compare the good and great solution based on the stated requirements.
5. Implement a complete vertical slice and one failure test.
6. Handle a realistic follow-up through an explicit extension seam.

## Detailed Design Reference

<details>
<summary>Open the implementation-specific deep dive</summary>
Design a hierarchical file system with absolute paths, directories, files, and safe structural mutations.

## 1. Understanding the problem

The core challenge is maintaining a recursive tree while supporting path-based operations.

The model must preserve:

- unique names within one directory;
- valid parent/child relationships;
- correct path traversal;
- no directory cycles;
- atomic moves across parents;
- behavior differences between files and directories.

This is an in-memory LLD, not an operating-system storage implementation.

## 2. Clarifying questions

- Are paths absolute, relative, or both?
- How should repeated separators, dot, and dot-dot behave?
- Is the file content text or bytes?
- Does write replace or append?
- Can non-empty directories be deleted?
- Can entries be renamed and moved?
- Are symbolic or hard links required?
- Are permissions, quotas, and timestamps in scope?
- Must concurrent operations be safe?
- Is persistence required?

## 3. Final requirements

Version one supports:

1. A root directory.
2. Absolute normalized paths.
3. Directory and text-file creation.
4. Reading and replacing/appending file content.
5. Listing a directory.
6. Moving and renaming entries.
7. Deleting files and optionally empty directories.
8. Precise errors for missing entries and invalid entry types.
9. Thread-safe mutations in one process.

Links, permissions, storage blocks, and durable recovery are follow-ups.

## 4. Invariants

1. Root has no parent and cannot be deleted or moved.
2. Each non-root entry has exactly one parent.
3. Sibling names are unique.
4. A File cannot contain children.
5. A Directory cannot become its own ancestor or descendant.
6. Entry names contain no path separator and are not dot/dot-dot.
7. Moving an entry updates old parent, new parent, and entry parent consistently.
8. A failed mutation leaves the tree unchanged.
9. Resolving a path never traverses through a File as though it were a Directory.

## 5. Core model

| Type | Important state | Responsibility |
|---|---|---|
| Path | normalized segments | parsing and path semantics |
| Entry | name, parent, timestamps | shared identity and metadata |
| File | content | read, replace, append, size |
| Directory | children by name | child uniqueness and local mutations |
| FileSystem | root and lock/repositories | path resolution and cross-parent workflows |
| EntryVisitor | optional | tree-wide operations when they multiply |

Relationships:

    Entry <|-- File
    Entry <|-- Directory
    Directory *-- Entry
    FileSystem *-- Directory : root
    FileSystem --> Path

Composite is natural for ownership, but File and Directory should not promise operations they cannot honor.

## 6. Path value object

Path should be immutable and normalized at construction.

Suggested contract:

    Path.parse("/a/b/file.txt") -> ("a", "b", "file.txt")
    path.parent
    path.name
    path.is_root

Decide explicitly:

- repeated separators collapse;
- dot is ignored;
- dot-dot either resolves without escaping root or is rejected;
- trailing separator is accepted only for a directory or normalized away;
- empty input is invalid;
- root is represented by zero segments.

Keeping parsing separate from traversal prevents string manipulation from spreading across FileSystem methods.

## 7. Entry design

Entry contains metadata common to both concrete types:

- stable entry ID if identity must survive moves;
- name;
- parent reference;
- created and modified time.

Useful behavior:

    rename(new_name)
    absolute_path()
    touch(now)

Do not expose set_parent publicly. Only a Directory/FileSystem move operation should coordinate parent changes.

## 8. Directory design

Directory stores:

    children: dict[str, Entry]

Useful behavior:

    child(name) -> Entry
    add(entry)
    remove(name) -> Entry
    contains(name) -> bool
    list_entries() -> immutable/sorted view

add() rejects duplicate names and an entry already owned elsewhere. remove() returns the removed entry so a move can roll back if adding to the destination fails.

A Directory should not resolve complete paths; it understands only immediate children.

## 9. File design

File owns content:

    read() -> str
    write(content)
    append(content)
    size -> int

If byte content is required, use bytes and define encoding at the application boundary. File operations update modified time through an injected Clock.

## 10. Path resolution

To resolve /projects/lld/readme:

1. Parse into segments.
2. Start at root.
3. For each segment:
   - require the current entry to be a Directory;
   - look up the child by exact name;
   - fail with NotFound when absent.
4. Return the final Entry.

Provide helpers:

    resolve(path) -> Entry
    resolve_directory(path) -> Directory
    resolve_parent(path) -> (Directory, leaf_name)

resolve_parent is useful for create operations where the leaf does not exist yet.

## 11. Create workflows

### Create directory

1. Parse the path and reject root.
2. Resolve the parent directory.
3. Validate the new name.
4. Construct Directory.
5. Ask the parent to add it.
6. Return an immutable entry description.

mkdirs() is a separate command because it defines different behavior for missing intermediate parents.

### Create file

The flow is the same, with a File leaf and optional initial content. Decide whether create overwrites; version one should reject duplicates to avoid accidental data loss.

## 12. Read, write, and list

- read_file requires the target to be File.
- write_file requires File and replaces content.
- append_file requires File and appends.
- list_directory requires Directory and returns stable entry metadata.

Use NotAFile and NotADirectory rather than returning empty results.

Listing can be sorted by name for deterministic tests, even if storage uses a dictionary.

## 13. Move and rename

Move is the most important structural operation.

    move(source_path, destination_directory_path, new_name=None)

Flow:

1. Resolve source and destination.
2. Reject root.
3. Require destination Directory.
4. Determine final name.
5. Reject duplicate destination child.
6. If source is a Directory, reject destination inside source subtree.
7. Remove from old parent.
8. Change name/parent and add to destination.
9. Roll back all fields if an unexpected failure occurs.

Steps 5â€“8 are one atomic boundary.

Cycle check can walk destination parents toward root. If source appears, the move is invalid.

## 14. Delete

Version one can choose conservative semantics:

- files may be deleted;
- empty directories may be deleted;
- non-empty directories require recursive=True;
- root cannot be deleted.

Recursive delete should define whether it is atomic for the whole subtree. In memory, detaching the subtree from its parent is one mutation; garbage collection handles descendants when no references remain.

## 15. Error model

| Error | Meaning |
|---|---|
| InvalidPath | syntax or normalization rule failed |
| NotFound | a path segment is missing |
| AlreadyExists | sibling name collision |
| NotAFile | file-only operation targeted another type |
| NotADirectory | traversal/list targeted a file |
| DirectoryNotEmpty | conservative delete rejected |
| InvalidMove | root/cycle/ownership rule failed |
| PermissionDenied | future authorization boundary |

Errors should include the relevant path but not expose internal object references.

## 16. Patterns and principles

| Technique | Purpose |
|---|---|
| Composite | recursive directory ownership |
| Value object | normalized Path |
| Template method | rarely needed; shared Entry data is enough |
| Visitor | optional for many tree-wide operations |
| Iterator | directory traversal without child-map exposure |
| Command | useful for journaling or undo |
| Encapsulation | Directory owns children; File owns content |

Avoid treating every operation uniformly through Entry when the contracts differ.

## 17. Concurrency

A single FileSystem read/write lock is simplest.

Finer locking:

- read locks for resolution;
- directory write locks for child mutation;
- lock old and new parents in stable entry-ID order for move;
- revalidate source and destination after locks;
- protect file content separately if large concurrent writes matter.

Never resolve paths, release all locks, and then mutate stale entries without version checks.

## 18. Persistence and recovery

For a durable version:

- store stable entry IDs and parent IDs;
- enforce unique(parent_id, name);
- transact move updates;
- store large content separately from metadata;
- use a journal/write-ahead log for crash recovery;
- define snapshot consistency for recursive listing;
- detect or repair orphan entries.

Links complicate ownership and deletion and should be added only with explicit reference semantics.

## 19. Complexity

For path depth D, children C, and subtree size N:

| Operation | Dictionary children |
|---|---:|
| resolve | O(D) average |
| create | O(D) |
| read/write after lookup | O(D + content size) |
| list | O(D + C log C) if sorted |
| move | O(D + height) for cycle check |
| delete empty | O(D) |
| recursive traversal | O(N) |

Space is O(number of entries + content).

## 20. Verification

Test:

- root resolution;
- normalization cases;
- nested create and lookup;
- duplicate sibling rejection;
- read, replace, and append;
- file used as intermediate path;
- list ordering;
- move across directories;
- rename collision;
- move directory into descendant;
- root mutation rejection;
- empty and recursive delete behavior;
- failed move leaves original tree intact;
- concurrent moves do not lose entries.

## 21. Extensibility

- **Relative paths:** add a WorkingDirectory context without changing Entry.
- **Permissions:** authorization policy checks Entry metadata before operations.
- **Links:** introduce explicit link entries and cycle-aware resolution.
- **Watchers:** publish path-change events after successful mutations.
- **Quotas:** aggregate or index subtree byte usage.
- **Snapshots:** persistent immutable roots or copy-on-write nodes.
- **Search:** separate index updated from entry events.
- **Versioning:** store immutable file revisions behind File.

## 22. Trade-offs

- Parent references make absolute paths and cycle checks easy but create bidirectional links.
- Dictionary children provide fast lookup but listing needs sorting.
- One global lock is easy to prove but limits concurrent writes.
- Stable IDs survive moves; path-only identity is simpler but unstable.
- Recursive composite design is expressive but deep recursion may need iterative traversal.

## 23. Interview expectations

### Junior

Model File, Directory, and basic path traversal with create/read/list.

### Mid-level

Add normalized Path, move/delete semantics, type-specific errors, invariants, and tests.

### Senior

Discuss atomic cross-parent move, lock order, persistence constraints, links, crash recovery, and why the simple tree is the correct version one.

## 24. Interview walkthrough

1. Fix absolute-path and delete semantics.
2. State sibling uniqueness, one-parent, and no-cycle invariants.
3. Put child ownership in Directory and path coordination in FileSystem.
4. Implement resolve_parent(), create, and read.
5. Add move as the critical multi-object mutation.
6. Test rollback and cycles.
7. Discuss fine-grained locking and durability only after the in-memory model works.

</details>
