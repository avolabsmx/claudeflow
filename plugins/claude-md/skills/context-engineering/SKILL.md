---
name: context-engineering
description: How to write and maintain a CLAUDE.md that actually changes Claude's output. Use when creating, editing, reviewing or debugging a CLAUDE.md or any agent context file, and when a project's agents keep producing work that ignores its conventions.
---

# Context engineering for CLAUDE.md

A CLAUDE.md is not documentation. Documentation is read by a person who can tell
when it is wrong. This file is read by an agent that cannot, before every single
request, and acted on as fact.

That asymmetry drives every rule below.

## The three failure modes

Almost every bad CLAUDE.md fails in one of three ways. Diagnose before editing —
the fixes point in opposite directions.

**Too vague to act on.** "Follow best practices. Write clean, maintainable
code." This changes nothing: it is a description of the default. The file is
short, so it looks efficient, but it is pure overhead — cost with no effect.

**Too long to survive.** Forty lines explaining how React hooks work, a
twenty-line sample component, the team's values. It is loaded on every request,
so the cost recurs forever while the benefit was zero the first time. Length
here is not a style problem, it is a permanent tax.

**Wrong, and therefore believed.** A script renamed six months ago. A version
that moved two majors. A directory that was restructured. This is the worst of
the three by a wide margin, because the other two waste effort while this one
actively misdirects — and the file never fails to compile, so nothing catches it.

## What earns a line

Ask one question of every line: **would removing this change what Claude does?**

If no, delete it. Not "shorten it" — delete it. A line that changes no output is
paying rent on every future request in the project.

That question rules out, immediately:

- How a framework works. Claude knows React. It does not know that *you* forbid
  `useEffect` outside `src/hooks`. Write the second, never the first.
- Team values and mission statements.
- Code samples over about ten lines. Give the path instead; the agent reads the
  file, and the file cannot drift the way a pasted copy does.
- Options you did not take. State the decision, not the menu.

And it rules *in*:

- **Commands, exactly as they are named.** A script called `test:unit` written as
  `test` sends every future agent to a command that does not exist.
- **Versions, resolved.** Not `^15.0.0` — the version actually installed. A range
  does not tell an agent which API it may use.
- **Deviations from the default.** This is the core of the whole file. Every
  place your project does something other than what a competent stranger would
  assume is a line that earns its place.
- **Rejected patterns.** What you tried and removed, and why. This is the most
  under-used section in practice and one of the highest-value: without it, agents
  helpfully reintroduce the thing you deliberately took out.
- **Boundaries.** Generated files, vendored code, applied migrations. Agents are
  precise about scope when you are precise about it first.

## Length

One page. Two if the project genuinely warrants it.

The instinct to add is much stronger than the instinct to cut, so the file only
ever grows. Trim it on a schedule, not when it becomes a problem — by then every
task has been paying for months.

Large repositories should use a short root file plus a `CLAUDE.md` per package.
Claude Code reads the nearest one, so each workspace describes itself and the
root stays small.

## Staleness is the real enemy

The file is prose. It never fails to compile, never breaks a test, never
triggers a review comment. It just quietly stops being true, and keeps being
believed.

Two habits fix this:

**Write only what you verified.** Read `package.json` for the scripts. Read the
lockfile for the versions. Never write a command from memory — a plausible
wrong one is worse than an admitted gap, because nobody checks a line that looks
right.

**Check it on a trigger, not a schedule.** After renaming a script, restructuring
directories, or a major upgrade. Those three account for nearly every stale
CLAUDE.md in the wild.

## Marking what you do not know

A gap stated is safe. A gap filled with plausible prose is a landmine, because
it reads exactly like a fact.

Use `{{PLACEHOLDER}}` for anything only a human knows — deploy targets, product
decisions, the reason behind an odd choice. An agent treats an obvious
placeholder as missing information and asks. It treats invented prose as truth
and acts on it.

## A shape that works

```markdown
# CLAUDE.md

## What this is
[One paragraph: what it does, who uses it, and what it deliberately is not.]

## Stack
| Concern | Choice |
| --- | --- |
[Resolved versions, from the lockfile.]

## Commands
| Command | What it does |
| --- | --- |
[Only commands that exist. Copy the names exactly.]

## Structure
[Top two levels. Annotate only where the name does not already say it.]

## Conventions
[Concrete patterns, and the ones deliberately rejected.]

## Do not touch
[Generated, vendored, migrated — with the reason for each.]
```

The order matters: identity, then facts, then rules, then boundaries. An agent
that reads only the first half should already have what it needs to avoid the
expensive mistakes.
