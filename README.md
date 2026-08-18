<div align="center">

# ◆ ClaudeFlow — free tools for Claude Code

**Guardrails that stop the accident. And a check for the file every agent reads first.**

```
/plugin marketplace add avolabsmx/claudeflow
/plugin install safety@claudeflow
```

MIT licensed. No account, no signup, no telemetry, no configuration.

</div>

---

## `safety` — three guardrails, zero setup

Claude Code can run shell commands and write files. That is the whole point, and
it is also why one bad expansion, one stale connection string, or one wrong
branch is all it takes.

This plugin installs three checks that run **before** the action, not after.
There is nothing to remember and nothing to configure — once it is installed it
just works, forever.

| Guard | Runs on | What it does |
| --- | --- | --- |
| **Dangerous command** | `Bash` | Refuses commands that cannot be undone: `rm -rf /`, force push to main, `DROP DATABASE`, `docker system prune -af`, `mkfs`, `dd` to a block device, fork bombs |
| **Secret** | `Write`, `Edit` | Refuses to write a live credential into a file — AWS keys, GitHub tokens, Slack tokens, private keys, connection strings with passwords |
| **Sensitive read** | `Read` | Never blocks. Says out loud when the file just opened is a `.env`, an SSH key, or AWS credentials, so its contents do not end up quoted into a commit |

### It is built to not cry wolf

A guardrail that fires on normal work does not get fixed. It gets uninstalled,
and takes every other check with it. So the detection is token-based rather than
regex-on-the-raw-string, which is what lets it tell these apart:

```
rm -rf ./node_modules              ✓ allowed
rm -rf /                           ✗ blocked

git push --force origin my-feature ✓ allowed  (normal after a rebase)
git push --force origin main       ✗ blocked
git push --force                   ✗ blocked only when you are on main

api_key = "YOUR_API_KEY_HERE"      ✓ allowed  (a placeholder, not a secret)
api_key = "AKIAIOSFODNN7EXAMPLE"   ✗ blocked
```

Verified against 16 destructive commands and 18 everyday ones: everything
dangerous blocked, nothing normal blocked.

### When it gets in your way

```bash
export CLAUDEFLOW_SAFETY_OFF=1
```

One switch, all three off for the session. Deliberately blunt — someone who
needs a command through should get it through in five seconds, not uninstall.

### What it is not

This is a **guardrail, not a security boundary.** It exists to catch the
accident: the variable that expanded to empty, the force push from the wrong
branch, the key pasted into a config file. It does not defend against an
attacker, and nothing here should be relied on as if it did.

Requires Python 3 (already present on macOS and Linux).

---

## `claude-md` — check the file every agent reads first

```
/plugin install claude-md@claudeflow
```

Claude Code reads your `CLAUDE.md` before every request and acts on it as fact.
Your code has a compiler, a linter and a test suite. That file has none of them.
It never fails to build — it just quietly stops being true, and keeps being
believed.

| Command | What it does |
| --- | --- |
| `/claude-md:check` | Verifies every claim against the repository — commands against `package.json`, paths against the tree, versions against the lockfile |
| `/claude-md:trim` | Finds the lines costing you context on every request without changing any output |

Plus a `context-engineering` skill that loads when you are writing or debugging
a context file.

```
| Severity | Line | Claim        | Reality                            |
| blocker  | 13   | `npm test`   | No `test` script. Closest: `test:unit` |
| blocker  | 19   | `src/hooks/` | Directory does not exist           |
| major    | 6    | React 18     | package.json:10 pins react 19.0.0  |
```

It reports and does not edit. Whether a line is stale or aspirational-on-purpose
is invisible to a tool and obvious to you.

---

## Design rules

Both plugins follow the same rules the paid ClaudeFlow kits do:

- **Read, never assume.** Every finding cites the file it came from.
- **Report, do not fix**, unless the fix is unambiguous.
- **Say what you could not check.** Silence would read as "verified".
- **Never cry wolf.** A false positive costs more than a missed edge case,
  because it gets the whole thing removed.

## Attribution

The `safety` guards are derived from [Alfred Dev](https://github.com/686f6c61/alfred-dev)
by 686f6c61 (MIT) — a full SDLC plugin for Claude Code that is worth installing
on its own. What we changed and why is in
[`plugins/safety/ATTRIBUTION.md`](./plugins/safety/ATTRIBUTION.md).

## Want the rest?

This is free and genuinely free — MIT, use it anywhere. It is also narrow on
purpose: each plugin does one job completely rather than ten jobs partly.

[ClaudeFlow](https://claudeflow.so) is the paid tier: 60 engineering agents,
24 growth agents, 128 skills and 126 curated slash commands, as an Engineer Kit,
a Growth Kit, or the Complete Bundle.

## Contributing

If a guard blocks something normal, that is the most valuable bug report you can
file — open an issue with the command. False positives are the failure mode we
care most about.

## License

MIT — see [LICENSE](./LICENSE).

> "Claude" and "Claude Code" are trademarks of Anthropic. ClaudeFlow is
> independent and not affiliated with, endorsed by, or sponsored by Anthropic.

<div align="center">
<sub><a href="https://claudeflow.so">claudeflow.so</a> · built by AvoLabs</sub>
</div>
