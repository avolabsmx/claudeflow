---
description: Write a CLAUDE.md from what the repository actually contains — never from assumption.
argument-hint: "[subdirectory — defaults to the repo root]"
allowed-tools: Read, Grep, Glob, Bash, Write
---

# Write a CLAUDE.md from the repository

Most CLAUDE.md files are written from memory, and memory is where the errors
come from: the script someone renamed, the version that moved, the directory
that got restructured. Every line you write here comes from a file you read in
this session.

Target `$1` if given, otherwise the repository root.

## Before writing anything

Gather the facts. Read, do not infer:

**Identity.** `package.json` name and description, the README's first paragraph,
the repository name. What does this thing do, and for whom?

**Stack and versions.** Dependencies from the manifest, resolved versions from
the lockfile. Report what is installed, not what the range allows — an agent
reading `^15.0.0` cannot tell whether it may use a 15.4 API.

**Commands.** The real ones. `package.json` scripts, `Makefile` targets,
`justfile` recipes, `docker-compose` services. Copy the names exactly. A script
named `test:unit` written as `test` sends every future agent to a command that
does not exist.

**Structure.** The top two levels of source directories, and what lives in each.
Skip anything gitignored, vendored, or generated.

**Existing conventions.** Infer them from the code, not from what is
fashionable: how files are named, how tests are organized, how modules are
imported. Read enough files to be sure — three examples of a pattern, not one.

**Config that constrains.** `tsconfig.json` strictness, linter rules that would
reject an agent's output, formatter settings. These decide whether generated
code lands clean or bounces.

**Do not touch.** Generated directories, vendored code, applied migrations,
anything the `.gitignore` or a header marks as machine-written.

## Then write

Aim for one page. Two at the very most.

This file is loaded on every single request, so every line costs context on
every task forever. A section that is not changing the output is not free — it
is a tax. When in doubt, cut it.

Structure:

1. **What this is** — one paragraph. What it does, who uses it, and one sentence
   on what it deliberately is *not*, if there is a real misconception to prevent.
2. **Stack** — a table of concern → choice, with versions.
3. **Commands** — a table of command → what it does. Only commands that exist.
4. **Structure** — the directory map, one line each, only where the name does
   not already say it.
5. **Conventions** — what you found in the code. Include patterns the project
   has deliberately rejected when you can see the evidence; those stop an agent
   from helpfully reintroducing something that was removed on purpose.
6. **Do not touch** — the list above, with the reason for each.

## Rules

- **Never invent a command.** If you cannot find how to run the tests, write
  `_TODO: how do you run the tests?_` and say so in your summary. A plausible
  guess is the worst outcome here: it looks right, so nobody checks it, and
  every agent runs it.
- **Mark real gaps as gaps.** `{{PLACEHOLDER}}` for anything only a human knows —
  deploy targets, product decisions, why an odd choice was made.
- **No aspiration.** Describe the project that exists. The one being planned
  belongs in a roadmap, and an agent cannot tell the two apart.
- **No long code samples.** The agent can read the code. Give it the map.

## If a CLAUDE.md already exists

Do not overwrite it. Write `CLAUDE.generated.md` beside it and report the
differences you found, so the user merges deliberately. Someone's hand-written
context is worth more than yours — it holds things no repository states.

## Output

Write the file, then report:

- Where you wrote it, and its length in lines.
- Every fact you took from a file, with the file it came from.
- Every `{{PLACEHOLDER}}` and TODO you left, and why.
- What you deliberately left out to keep it short.

Then say plainly: run `/claude-md:check` after filling in the placeholders.
