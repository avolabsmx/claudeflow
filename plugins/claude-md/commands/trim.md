---
description: Find the lines in CLAUDE.md that cost context on every request without changing any output.
argument-hint: "[path to CLAUDE.md — defaults to ./CLAUDE.md]"
allowed-tools: Read, Grep, Glob
---

# Trim a CLAUDE.md

This file is loaded before every request, so its length is not paid once — it is
paid on every task, forever, by every agent. A 400-line CLAUDE.md is a standing
tax on a project's whole future.

Most of them are long for the same few reasons, and none of those reasons
survive contact with the question: *would removing this line change what Claude
does?*

Analyse `$1`, or `./CLAUDE.md`. Report only. Do not edit.

## What to look for

**Restated documentation.** Explanations of how React, Docker or Postgres work.
Claude knows. Only the *project-specific* deviation earns its place: not how
`useEffect` works, but that this codebase forbids it outside `src/hooks`.

**Long code samples.** More than about ten lines is almost always a pointer in
disguise. Replace it with the path — the agent can read the file, and the file
cannot go stale the way a pasted copy does.

**Duplication.** The same rule stated in two sections, which is what happens when
a file grows by accretion. Keep the clearer one.

**Prose with no instruction in it.** Team values, mission statements,
encouragement. It changes nothing an agent does.

**Dead scope.** Sections about parts of the project that no longer exist. Verify
with Glob before calling it dead.

**Over-specified obvious structure.** `src/` holds source, `tests/` holds tests.
Only annotate a directory whose name does not already say it.

**Options never taken.** "You could use X or Y." An agent needs the decision,
not the menu. If the project chose Y, say Y.

## What to protect

Be conservative. A wrong cut here is invisible: output quality drops on some
future task and nobody connects it to a line deleted months earlier.

Never propose cutting:

- Commands, paths, or versions — even ones that look obvious
- Anything stating a *deviation* from a default, which is exactly what context
  is for
- "Do not touch" boundaries
- Anything marked `{{PLACEHOLDER}}` or TODO — that is unfinished, not surplus

When you are unsure whether a line does work, keep it and say you were unsure.
Uncertainty is a finding, not something to resolve by guessing.

## Output

### Summary
`N lines · ~M tokens` now. Projected after the cuts. Then one sentence on the
single largest source of weight.

### Cuts

| Lines | Bytes | What | Why it changes nothing |
| --- | ---: | --- | --- |

Ordered by size, largest first. `What` quotes or names the passage — enough for
the user to find it without opening the file beside your report.

### Rewrites
Passages worth keeping but not at their current length. Show current and
proposed text side by side, with the saving.

### Kept deliberately
Anything you considered and did not propose cutting, with the reason. This
section is the one that makes the report trustworthy: it shows what you looked
at and chose to leave, so the user knows the silence elsewhere is a decision
rather than an oversight.
