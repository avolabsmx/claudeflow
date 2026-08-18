# Attribution

The three guards in this plugin are derived from **[Alfred Dev](https://github.com/686f6c61/alfred-dev)**
by 686f6c61, used under the MIT License.

Alfred Dev is a complete, opinionated SDLC plugin for Claude Code — eight agents,
persistent per-project memory, quality gates, and workflows from idea to delivery.
If any of that sounds useful, install the original: it is free, and it is much
more than what we extracted here.

## What we took

- `hooks/dangerous-command-guard.py` → `hooks/dangerous_command_guard.py`
- `hooks/sensitive-read-guard.py` → `hooks/sensitive_read_guard.py`
- `hooks/secret-guard.py` plus the pattern table from `core/secrets.py` → `hooks/secret_guard.py`

The detection logic, the patterns, and the token-based parsing approach are theirs.
That approach is the reason these guards are usable at all: matching regexes
against a raw command string cannot distinguish `rm -rf ./build` from `rm -rf /`
without blocking both.

## What we changed, and why

**Unbundled.** Alfred's guards are wired into its session system and its own
helper allowlist. These run standalone, with no dependency on any of it.

**Translated to English**, and rebranded in the user-facing messages.

**`git push --force` is now branch-aware.** The original blocked a force push
whenever no protected branch was named. That blocks force-pushing your own
feature branch after a rebase — the most common legitimate force push there is.
These guards resolve `HEAD` instead and block only when you are actually on
main or master, or when main or master is named explicitly (including in a
`HEAD:main` refspec).

**Unparseable hook input now fails open, loudly.** The original fails closed:
if the payload cannot be parsed it blocks the operation. That is the right call
inside a system whose author controls both ends. In a plugin installed by
strangers it means one upstream format change turns into a machine where no
Bash command runs at all — and the rational response to that is to uninstall,
which removes every other check too. These guards print a loud warning to stderr
saying the command was not checked, and allow it.

**Placeholder values are no longer treated as credentials.** The hardcoded
credential pattern fires on `password = "..."`, which is the shape of a leaked
secret and also of every example, fixture, and template ever written.
`YOUR_API_KEY`, `changeme`, `${VAR}`, `{{VAULT}}`, `xxxxxx` and friends are
skipped.

**A dead regex table was dropped.** The original's 80-line `_DANGEROUS_PATTERNS`
list was never consulted — `_find_dangerous_reason` uses the token-based
detectors instead. Carrying it forward would have implied a second layer of
checking that does not exist.

**One opt-out.** `CLAUDEFLOW_SAFETY_OFF=1` disables all three for a session.

## License

Alfred Dev is MIT. This derivative is MIT. See [LICENSE](../../LICENSE).
