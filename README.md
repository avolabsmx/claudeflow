<div align="center">

# ◆ ClaudeFlow — free tools for Claude Code

**Four commands for the highest-leverage file in your project.**

```
/plugin marketplace add avolabsmx/claudeflow
/plugin install claude-md@claudeflow
```

MIT licensed. No account, no signup, no telemetry.

</div>

---

## Why CLAUDE.md is worth four commands

Claude Code reads your `CLAUDE.md` before every request and acts on it as fact.
That is what makes it the highest-leverage file in the repository — and it is
also the problem.

Your code has a compiler, a linter, a test suite and a reviewer. Your
`CLAUDE.md` has none of those. It is prose, so it never fails to build and never
breaks a test. It just quietly stops being true, and keeps being believed.

The script you renamed. The version that moved two majors. The directory you
restructured last quarter. Every one of those is still in there, and every agent
you run is still acting on it.

## What you get

| Command | What it does |
| --- | --- |
| `/claude-md:check` | Verifies every claim in the file against the repository — commands against `package.json`, paths against the tree, versions against the lockfile. Reports what has gone stale, with line numbers. |
| `/claude-md:init` | Writes a `CLAUDE.md` from what the repository actually contains. Never invents a command; marks real gaps as gaps. |
| `/claude-md:audit` | Scores the file against a weighted rubric and returns the three edits that buy the most output quality per word changed. |
| `/claude-md:trim` | Finds the lines costing you context on every request without changing any output. |

Plus a `context-engineering` skill that loads whenever you are writing or
debugging a context file.

## What `check` looks like

Run against a project whose `CLAUDE.md` had drifted:

```
| Severity | Line | Claim                   | Reality                                          |
| blocker  | 13   | `npm test`              | No `test` script. Closest is `test:unit`         |
| blocker  | 19   | `src/hooks/`            | Directory does not exist                         |
| major    | 6    | React 18                | package.json:10 pins react 19.0.0                |
```

It reports. It does not edit. You decide what is stale and what is
aspirational-on-purpose — that distinction is invisible to a tool and obvious to
you, which is exactly why the fix stays your call.

It also tells you what it *could not* verify. A claim with no mechanical check
is a real result, not a gap to hide: silence would read as "verified", and that
is the failure this whole thing exists to prevent.

## Install

```
/plugin marketplace add avolabsmx/claudeflow
/plugin install claude-md@claudeflow
```

If the install summary says `Run /reload-plugins to activate.`, run it.

Then, in any project:

```
/claude-md:check
```

Requires Claude Code v2.1.120 or later.

## Design rules

These four commands follow the same rules the paid ClaudeFlow kits do:

- **Read, never assume.** Every finding cites the file it came from. A finding
  with no source sends someone to edit a line that was fine.
- **Report, do not fix.** Except `init`, which writes only when no file exists —
  and writes `CLAUDE.generated.md` when one does. Your hand-written context holds
  things no repository states.
- **Say what you could not check.** An unverifiable claim is reported as
  unverifiable, never quietly omitted.
- **No padding.** If your file is good, `audit` says so in two lines and stops.
  An audit that manufactures findings to look thorough trains you to ignore it.

## Want the rest?

This is the free tier, and it is genuinely free — MIT, use it anywhere, no
strings. It is also narrow on purpose: it does one job completely rather than
ten jobs partly.

Once your context is right, [ClaudeFlow](https://claudeflow.so) is the team that
uses it: 60 engineering agents, 24 growth agents, 128 skills and 126 curated
slash commands, split into an Engineer Kit, a Growth Kit and a Complete Bundle.

Good context makes every one of them better. That is the whole reason this
plugin is the free one.

## Contributing

Issues and PRs welcome. If a check misses something in your project, that is a
bug worth reporting — open an issue with the `CLAUDE.md` line and what it should
have caught.

## License

MIT — see [LICENSE](./LICENSE). Use it in commercial projects, fork it, ship it.

> "Claude" and "Claude Code" are trademarks of Anthropic. ClaudeFlow is
> independent and not affiliated with, endorsed by, or sponsored by Anthropic.

<div align="center">
<sub><a href="https://claudeflow.so">claudeflow.so</a> · built by AvoLabs</sub>
</div>
