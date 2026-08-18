---
description: Score a CLAUDE.md against a rubric and return the specific edits that would raise it.
argument-hint: "[path to CLAUDE.md — defaults to ./CLAUDE.md]"
allowed-tools: Read, Grep, Glob, Bash
---

# Audit a CLAUDE.md

`/claude-md:check` asks whether the file is *true*. This asks whether it is
*good* — whether it earns the context it costs on every request.

Audit `$1`, or `./CLAUDE.md`.

## The rubric

Score each criterion 0–5. A score needs evidence: the line that earned it, or
the absence you looked for and did not find.

**1. Orientation (weight 2).** Can a reader who has never seen this project say
what it does after the first paragraph? Vague openers are the most common
failure — "a web application built with modern technologies" tells an agent
nothing it did not already assume.

**2. Verifiable commands (weight 3).** Are the commands real, complete, and
exact? Check them against `package.json`, the `Makefile`, the `justfile`. This
carries the most weight because it is the section agents act on directly.

**3. Version specificity (weight 2).** Are framework and language versions
stated? An agent that does not know you are on React 19 will hand you `useMemo`
you no longer need, or miss an API you have.

**4. Conventions with teeth (weight 2).** Does it state patterns concretely
enough to follow, including what the project has rejected? "Write clean code"
scores 0. "Container components in `src/containers`, presentational in
`src/components`, no logic below the container" scores 5.

**5. Boundaries (weight 2).** Does it say what not to touch, and why? Generated
files, vendored code, applied migrations.

**6. Economy (weight 3).** Every line is loaded on every request forever. Score
this on whether the file earns its length — not on whether it is short.
Restated framework documentation, long code samples, and motivational prose all
score 0 no matter how well written.

**7. Freshness (weight 2).** Does it describe the repository as it is now? Spot
check the riskiest claims; run `/claude-md:check` for the exhaustive pass.

**8. Honest gaps (weight 1).** Are unknowns marked as unknowns, or quietly
filled with plausible prose? A file that admits what it does not know is safer
than one that guesses fluently.

## Scoring

Weighted average, one decimal, out of 5.

- **4.0+** — good. Name the one thing worth improving and stop.
- **2.5–3.9** — working but leaking. Rank the fixes by leverage.
- **below 2.5** — the agents are mostly ignoring it or being misled. Say so
  plainly and recommend `/claude-md:init` to rebuild from the repository.

Do not inflate. A generous score on a bad file costs the user real output
quality on every task from here on, and they will never trace it back to this.

## Output

### Score
`X.X / 5` and the one-line verdict for that band.

### By criterion

| Criterion | Score | Weight | Evidence |
| --- | :---: | :---: | --- |

Evidence is a line number or a named absence. Never a restatement of the
criterion.

### The three edits worth making
Ranked by how much output quality they buy per word changed. For each: the
current text, the replacement, and what it fixes. Concrete text, not advice.

### What to delete
Lines paying no rent. Quote them and give the reason. Be specific — "trim the
intro" is not actionable, quoting the two sentences is.

## Rules

- Read the repository, not only the file. Half these criteria are about the gap
  between the two.
- Do not edit anything. Report, and let the user apply.
- Do not pad. If the file is good, say it is good in two lines and stop. An
  audit that manufactures findings to look thorough trains people to ignore it.
