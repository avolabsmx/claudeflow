#!/usr/bin/env python3
"""PreToolUse guard for Bash: refuses commands that destroy things irreversibly.

This is a guardrail, not a security boundary. It exists to catch the accident —
the `rm -rf` with a variable that expanded to empty, the force push to main from
the wrong branch, the `DROP TABLE` against prod because the connection string
was stale. It does not defend against an attacker, and nothing here should be
relied on as if it did.

Detection is token-based, not regex-on-the-raw-string. The difference matters:
`rm -rf ./build` and `rm -rf /` differ by two characters and by everything else,
and a regex loose enough to catch the second reliably starts blocking the first.
Every check below parses the command into tokens, strips neutral wrappers
(`sudo`, `env`, inline assignments), and inspects the actual target.

Derived from Alfred Dev (MIT) — see ATTRIBUTION.md.
"""

import json
import os
import re
import shlex
import sys

BRAND = "ClaudeFlow safety"

# One escape hatch, deliberately blunt. Someone who needs a blocked command
# through should be able to get it through in five seconds without editing a
# file in a plugin cache — otherwise they uninstall instead, and lose the other
# fifteen checks along with the one that annoyed them.
OPT_OUT_ENV = "CLAUDEFLOW_SAFETY_OFF"

_SHELL_WRAPPERS = frozenset({"sh", "bash", "zsh"})
_SQL_CLIENTS = frozenset({"psql", "mysql", "mariadb", "sqlite3", "duckdb"})

_DROP_SQL = re.compile(r"\bDROP\s+(DATABASE|TABLE|SCHEMA)\b", re.IGNORECASE)
_DEVICE_REDIRECT = re.compile(r">\s*/dev/(sd|hd|nvme|vd|xvd)\w*", re.IGNORECASE)

# Used only when tokenization fails (unbalanced quotes). Deliberately narrow:
# these run against a raw string, so anything looser would fire on prose.
_RAW_FALLBACK = [
    (re.compile(r"(?:^|[\s;&|])rm\s+(?:-\w*\s+)*-\w*[rf]\w*\s+(?:-\w+\s+)*(/|~|\$HOME|\$\{HOME\})(\s|$|/\*)"),
     "Catastrophic delete: rm -rf against root or home"),
    (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
     "Fork bomb: local denial of service"),
    (_DROP_SQL, "Data destruction: DROP DATABASE/TABLE/SCHEMA"),
    (_DEVICE_REDIRECT, "Output redirected to a block device"),
]


# --------------------------------------------------------------------------
# token helpers
# --------------------------------------------------------------------------

def _basename(token):
    return os.path.basename(token or "")


def _strip_leading_wrappers(tokens):
    """Drop neutral prefixes: sudo, env, and inline VAR=value assignments."""
    idx = 0
    while idx < len(tokens):
        token = tokens[idx]
        base = _basename(token)

        if base == "sudo":
            idx += 1
            while idx < len(tokens) and tokens[idx].startswith("-"):
                idx += 1
            continue

        if base == "env":
            idx += 1
            while idx < len(tokens) and "=" in tokens[idx] and not tokens[idx].startswith("-"):
                idx += 1
            continue

        if "=" in token and not token.startswith("-"):
            name, _ = token.split("=", 1)
            if name.replace("_", "").isalnum():
                idx += 1
                continue

        break
    return tokens[idx:]


def _strip_quoted(command):
    """Blank out quoted content, preserving operators outside quotes."""
    out = []
    in_single = in_double = escaped = False
    for char in command:
        if escaped:
            out.append(" " if (in_single or in_double) else char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            out.append(" " if (in_single or in_double) else char)
            continue
        if char == "'" and not in_double:
            in_single = not in_single
            out.append(" ")
            continue
        if char == '"' and not in_single:
            in_double = not in_double
            out.append(" ")
            continue
        out.append(" " if (in_single or in_double) else char)
    return "".join(out)


def _embedded_shell_command(tokens):
    """The command inside `sh -c '...'` and friends, so wrappers do not hide it."""
    core = _strip_leading_wrappers(tokens)
    if not core or _basename(core[0]) not in _SHELL_WRAPPERS:
        return None
    idx = 1
    while idx < len(core):
        token = core[idx]
        if token == "-c" and idx + 1 < len(core):
            return core[idx + 1]
        if token.startswith("-") and "c" in token and idx + 1 < len(core):
            return core[idx + 1]
        idx += 1
    return None


def _has_flags(tokens, short, long_form):
    for token in tokens:
        if token == long_form:
            return True
        if token.startswith("-") and not token.startswith("--") and short in token[1:]:
            return True
    return False


# --------------------------------------------------------------------------
# detectors — each returns a reason string, or None
# --------------------------------------------------------------------------

def _sensitive_delete_target(target):
    roots = ("/", "/etc", "/usr", "/var", "/boot", "/System", "/Library")
    if target in {"~", "~/", "$HOME", "${HOME}"} or target.startswith("~/"):
        return True
    if target in {"/*", "~/*", "$HOME/*", "${HOME}/*"}:
        return True
    for root in roots:
        if target == root or target == root.rstrip("/") + "/*":
            return True
        if root != "/" and target.startswith(root + "/"):
            return True
    return False


def _detect_rm(tokens):
    core = _strip_leading_wrappers(tokens)
    if not core or _basename(core[0]) != "rm":
        return None
    rest = core[1:]
    if not (_has_flags(rest, "r", "--recursive") and _has_flags(rest, "f", "--force")):
        return None
    targets = [t for t in rest if not t.startswith("-")]
    if any(_sensitive_delete_target(t) for t in targets):
        return "Catastrophic delete: rm -rf against a root, system, or home directory"
    return None


def _current_branch():
    """The branch we are on, or None when that cannot be established.

    Worth a subprocess: without it a bare `git push --force` is ambiguous, and
    the only way to be safe about the ambiguity is to block it — which also
    blocks force-pushing your own feature branch after a rebase. That is the
    single most common legitimate force push there is, and blocking it is how
    a guardrail gets uninstalled.
    """
    try:
        import subprocess
        out = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=3,
        )
        return out.stdout.strip() if out.returncode == 0 else None
    except Exception:
        return None


_PROTECTED = {"main", "master"}


def _names_protected_ref(token):
    """True when this positional argument targets main or master.

    Handles the refspec form too: in `HEAD:main` the destination is what gets
    overwritten, so that is the half that decides.
    """
    ref = token.split(":")[-1] if ":" in token else token
    ref = ref.replace("refs/heads/", "")
    if "/" in ref:
        ref = ref.split("/")[-1]
    return ref in _PROTECTED


def _detect_git_push(tokens):
    core = _strip_leading_wrappers(tokens)
    if len(core) < 2 or _basename(core[0]) != "git" or core[1] != "push":
        return None
    rest = core[2:]
    forced = any(
        t in {"--force", "--force-with-lease", "-f"}
        or (t.startswith("-") and not t.startswith("--") and "f" in t[1:])
        for t in rest
    )
    if not forced:
        return None

    refs = [t for t in rest if not t.startswith("-")]

    if any(_names_protected_ref(t) for t in refs):
        return "Force push to main/master: the remote history would be overwritten"

    # A ref was named and it is not protected — force-pushing your own branch
    # after a rebase. Normal, and blocking it is how this plugin gets removed.
    if len(refs) > 1:
        return None

    # No branch named: whether this is safe depends entirely on where HEAD is.
    branch = _current_branch()
    if branch in _PROTECTED:
        return f"Force push while on {branch}: the remote history would be overwritten"
    return None


def _detect_sql_drop(tokens):
    core = _strip_leading_wrappers(tokens)
    if not core:
        return None
    if _basename(core[0]).lower() == "drop":
        if len(core) > 1 and core[1].upper() in {"DATABASE", "TABLE", "SCHEMA"}:
            return "Data destruction: DROP DATABASE/TABLE/SCHEMA"
        return None
    if _basename(core[0]) not in _SQL_CLIENTS:
        return None
    if any(_DROP_SQL.search(t) for t in core[1:]):
        return "Data destruction: DROP DATABASE/TABLE/SCHEMA through a SQL client"
    return None


def _detect_docker_prune(tokens):
    core = _strip_leading_wrappers(tokens)
    if len(core) < 3:
        return None
    if _basename(core[0]) != "docker" or core[1] != "system" or core[2] != "prune":
        return None
    rest = core[3:]
    if _has_flags(rest, "a", "--all") and _has_flags(rest, "f", "--force"):
        return "docker system prune -af: removes every volume, image, and container"
    return None


def _detect_chmod(tokens):
    core = _strip_leading_wrappers(tokens)
    if len(core) < 3 or _basename(core[0]) != "chmod":
        return None
    positional = [t for t in core[1:] if not t.startswith("-")]
    if not positional or positional[0] != "777":
        return None
    if any(t == "/" or t.startswith("/") for t in positional[1:]):
        return "Unsafe permissions: chmod 777 against an absolute system path"
    return None


def _detect_fork_bomb(tokens):
    core = _strip_leading_wrappers(tokens)
    joined = "".join(core)
    if ":(){" in joined and ":|:&" in joined:
        return "Fork bomb: local denial of service"
    return None


def _detect_mkfs(tokens):
    core = _strip_leading_wrappers(tokens)
    if len(core) < 2 or not _basename(core[0]).startswith("mkfs."):
        return None
    if any(t.startswith("/dev/") for t in core[1:]):
        return "Disk format: mkfs against a block device"
    return None


def _detect_dd(tokens):
    core = _strip_leading_wrappers(tokens)
    if not core or _basename(core[0]) != "dd":
        return None
    if any(re.match(r"of=/dev/(sd|hd|nvme|vd|xvd)\w*", t) for t in core[1:]):
        return "dd writing directly to a block device"
    return None


def _detect_git_reset(tokens):
    core = _strip_leading_wrappers(tokens)
    if len(core) < 4 or _basename(core[0]) != "git" or core[1] != "reset":
        return None
    rest = core[2:]
    if "--hard" in rest and any(t in {"origin/main", "origin/master"} for t in rest):
        return "git reset --hard origin/main: discards every local change"
    return None


_DETECTORS = (
    _detect_rm, _detect_git_push, _detect_sql_drop, _detect_docker_prune,
    _detect_chmod, _detect_fork_bomb, _detect_mkfs, _detect_dd, _detect_git_reset,
)


def find_reason(command, _depth=0):
    """The reason this command is refused, or None when it is fine."""
    if _depth > 3:  # a wrapper chain this deep is not a real command
        return None
    try:
        tokens = shlex.split(command)
    except ValueError:
        # Unbalanced quotes: no reliable tokens, so every token detector would
        # return None and the command would sail through. Scan the raw string
        # with the narrow fallback set instead of pretending it was checked.
        for pattern, reason in _RAW_FALLBACK:
            if pattern.search(command):
                return reason
        return None

    embedded = _embedded_shell_command(tokens)
    if embedded:
        found = find_reason(embedded, _depth + 1)
        if found:
            return found

    for detector in _DETECTORS:
        reason = detector(tokens)
        if reason:
            return reason

    if _DEVICE_REDIRECT.search(_strip_quoted(command)):
        return "Output redirected to a block device"
    return None


def main():
    if os.environ.get(OPT_OUT_ENV):
        sys.exit(0)

    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        # Fail OPEN here, loudly, and this is a deliberate departure from the
        # original. If the payload cannot be read there is no command to judge,
        # so blocking is not "refusing something dangerous" — it is refusing
        # everything, including `ls`. For a plugin installed by strangers that
        # turns one upstream format change into a machine where Claude can run
        # no commands at all, and the rational response to that is uninstall,
        # which removes every other check too. A guardrail that fails silently
        # open is bad; one that fails closed on all input is worse, because it
        # gets removed. Loud stderr is the compromise.
        print(f"[{BRAND}] could not read the hook payload ({exc}); "
              f"this command was NOT checked.", file=sys.stderr)
        sys.exit(0)

    command = (payload.get("tool_input") or {}).get("command", "")
    if not command:
        sys.exit(0)

    reason = find_reason(command)
    if not reason:
        sys.exit(0)

    print(
        f"\n[{BRAND}] BLOCKED — this command is not reversible\n\n"
        f"  Command:  {command[:200]}\n"
        f"  Risk:     {reason}\n\n"
        f"  If this is genuinely what you want, run it yourself in a terminal.\n"
        f"  To turn this guard off for a session: export {OPT_OUT_ENV}=1\n",
        file=sys.stderr,
    )
    sys.exit(2)


if __name__ == "__main__":
    main()
