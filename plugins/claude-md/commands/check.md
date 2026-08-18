---
description: Verify every factual claim in CLAUDE.md against the repository, and report what has gone stale.
argument-hint: "[path to CLAUDE.md — defaults to ./CLAUDE.md]"
allowed-tools: Read, Grep, Glob, Bash
---

# Check CLAUDE.md against reality

A CLAUDE.md is read before every request and believed without question. That is
what makes it powerful, and it is also why a stale one is worse than no file at
all: a wrong command gets run, a deleted directory gets referenced, a version
that changed six months ago decides which API you get.

Nothing in the toolchain catches this. The file is prose, so it never fails to
compile and never breaks a test. It just quietly stops being true.

Your job is to find every claim in the file that the repository contradicts.

## Scope

Check the file at `$1`, or `./CLAUDE.md` when no argument is given. If the path
does not exist, say so and stop — do not offer to write one, that is
`/claude-md:init`.

Read nested `CLAUDE.md` files only if the user names one. A monorepo has many,
and checking all of them uninvited buries the answer they asked for.

## What to verify

Work through these in order. For each, read the real source rather than
inferring — the whole point is that memory and prose are what went stale.

**1. Commands.** Extract every shell command the file tells someone to run.
Then verify each one exists:

- `npm`/`pnpm`/`yarn`/`bun` scripts → read `package.json` `scripts`
- `make` targets → read the `Makefile`
- `just` recipes → read the `justfile`
- `cargo`, `go`, `uv`, `poetry`, `rake`, `composer` → the matching manifest
- bare binaries → check they are a dependency or a documented install

A command in the file with no matching script is the highest-value finding in
this whole check. Report the closest real script by name so the fix is obvious.

**2. Paths.** Every file or directory the document names. Use Glob. Report the
ones that no longer exist, and when a plausible rename exists, name it.

**3. Versions.** Every version number claimed for a language, framework, or
library. Compare against the lockfile first (`package-lock.json`,
`pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Cargo.lock`, `poetry.lock`,
`uv.lock`, `go.mod`), and the manifest only when there is no lockfile. A
manifest range and an installed version are different facts; say which you read.

**4. Stack claims.** Tools and services the file says the project uses. Verify
each has a dependency, a config file, or an import somewhere. A framework named
in prose with nothing in the tree is either aspirational or removed — both
mislead.

**5. Conventions.** Where a convention is mechanically checkable, check it.
"Components live in `src/components`" is checkable. "We favour composition" is
not — skip it rather than guessing.

**6. Internal consistency.** Contradictions between two sections of the same
file. These are common after edits and invisible to the person who wrote both.

## Rules

- **Read, do not assume.** Every finding cites the file and line you read it
  from, and the file you checked it against. A finding with no source is a
  guess, and a guess here sends someone to edit a line that was fine.
- **Do not fix anything.** This command reports. The user decides what is stale
  and what is aspirational-on-purpose. Offer the fix at the end, do not apply it.
- **Report what you could not check.** A claim you had no way to verify is a
  real result, not a gap to hide. Silence reads as "verified", and that is the
  failure mode this whole command exists to prevent.
- **No score.** That is `/claude-md:audit`. This is pass or fail per claim.

## Output

### Summary
One line: `N claims checked · M stale · K unverifiable`. Then one sentence on
the most damaging finding, or a plain statement that the file is accurate.

### Stale claims

| Severity | CLAUDE.md | Claim | Reality |
| --- | --- | --- | --- |

`CLAUDE.md` is the line number. Severity:

- **blocker** — following it breaks something or wastes real time: a command
  that does not exist, a path that is gone
- **major** — a wrong version, or a tool claimed that is not installed
- **minor** — drifted prose, an inconsistency between sections

Order by severity, blockers first. Omit the table when nothing is stale, and
say so in one line instead of printing an empty header.

### Could not verify
Each claim you had no mechanical way to check, and what would settle it.

### Suggested edits
The exact replacement text for each blocker and major, as a diff the user can
apply or reject. Do not write to the file.
