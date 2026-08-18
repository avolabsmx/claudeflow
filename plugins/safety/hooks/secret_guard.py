#!/usr/bin/env python3
"""PreToolUse guard for Write and Edit: refuses to write a live credential.

Credentials reach a repository by being written into one, and almost never on
purpose. By the time a key is in a commit the cheap fix is gone: the remedy is
rotation, not `git rm`.

Every pattern here is anchored to a real credential format with a distinctive
prefix — AKIA, ghp_, xox, AIza, sk-ant. That is deliberate. A generic
high-entropy-string detector fires on minified JavaScript, lockfile hashes and
UUIDs, and a guard that cries wolf on `package-lock.json` gets uninstalled
within the hour.

Derived from Alfred Dev (MIT) — see ATTRIBUTION.md.
"""

import json
import os
import re
import sys

BRAND = "ClaudeFlow safety"
OPT_OUT_ENV = "CLAUDEFLOW_SAFETY_OFF"

SECRET_PATTERNS = [
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS access key"),
    (re.compile(r"sk-ant-[a-zA-Z0-9\-]{20,}"), "Anthropic API key"),
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "API key with an sk- prefix (OpenAI, Stripe, or similar)"),
    (re.compile(r"(ghp_[a-zA-Z0-9]{36}|github_pat_[a-zA-Z0-9_]{20,})"), "GitHub personal access token"),
    (re.compile(r"xox[bpsa]-[a-zA-Z0-9\-]{10,}"), "Slack token"),
    (re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "Google API key"),
    (re.compile(r"SG\.[a-zA-Z0-9\-_]{22,}\.[a-zA-Z0-9\-_]{22,}"), "SendGrid API key"),
    (re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"), "private key"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), "hardcoded JWT"),
    (re.compile(
        r"(?:mysql|postgresql|postgres|mongodb(?:\+srv)?|redis|amqp)"
        r"://(?:(?:[^/\s\"':@]+:[^/\s\"'@]+)|(?:[^/\s\"'@]{8,}))@"
    ), "connection string with embedded credentials"),
    (re.compile(r"https://hooks\.slack\.com/services/[A-Za-z0-9/]+"), "Slack webhook URL"),
    (re.compile(r"https://discord\.com/api/webhooks/[0-9]+/[A-Za-z0-9_-]+"), "Discord webhook URL"),
]

# The loosest rule, kept separate because it is the one that needs a guard of
# its own. `password = "..."` is the shape of a leaked credential and also the
# shape of every example, fixture and template ever written.
_ASSIGNMENT = re.compile(
    r"(?i)(?:password|passwd|api_key|apikey|api_secret|secret_key"
    r"|auth_token|access_token|private_key)"
    r"""\s*[:=]\s*["']([^"']{8,})["']"""
)

# A value matching any of these is documentation, not a credential.
_PLACEHOLDER = re.compile(
    r"(?i)^(?:"
    r"your[_\- ]?|my[_\- ]?|some[_\- ]?|<.*>|\$\{.*\}|\{\{.*\}\}|%\w+%"
    r"|x{4,}|\*{4,}|\.{3,}|change[_\- ]?me|replace[_\- ]?me|placeholder"
    r"|example|sample|dummy|fake|test[_\- ]?only|todo|tbd|redacted"
    r"|insert[_\- ]|add[_\- ]your|password|secret|token|abc123|123456"
    r")"
)


def find_secret(text):
    if not text:
        return None
    for pattern, label in SECRET_PATTERNS:
        if pattern.search(text):
            return label
    for match in _ASSIGNMENT.finditer(text):
        value = match.group(1)
        if _PLACEHOLDER.search(value):
            continue
        return "hardcoded credential in an assignment"
    return None


def scan_targets(payload):
    """The strings worth scanning, per tool. Paths are never scanned — a file
    named `secrets.ts` is not a secret, and treating it as one blocks the very
    file someone is trying to write correctly."""
    tool = str(payload.get("tool_name") or "")
    tool_input = payload.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return []

    if tool == "Write":
        return [tool_input.get("content", "")]
    if tool == "Edit":
        return [tool_input.get("new_string", "")]
    if tool == "NotebookEdit":
        return [tool_input.get("new_source", "")]
    return []


def main():
    if os.environ.get(OPT_OUT_ENV):
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except Exception as exc:
        # Fail open, loudly — same reasoning as the command guard: an
        # unreadable payload means nothing was checked, not that something
        # dangerous was found.
        print(f"[{BRAND}] could not read the hook payload ({exc}); "
              f"this write was NOT checked.", file=sys.stderr)
        sys.exit(0)

    for text in scan_targets(payload):
        label = find_secret(text)
        if label:
            print(
                f"\n[{BRAND}] BLOCKED — this looks like a live credential\n\n"
                f"  Found:  {label}\n\n"
                f"  Put it in an environment variable and read it at runtime.\n"
                f"  If it is already committed somewhere, rotate it — removing\n"
                f"  the line does not un-leak it.\n\n"
                f"  False positive? export {OPT_OUT_ENV}=1 for this session.\n",
                file=sys.stderr,
            )
            sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
