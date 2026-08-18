#!/usr/bin/env python3
"""PreToolUse notice for Read: says out loud when a file holds credentials.

This one never blocks. Reading a `.env` is often exactly the right thing to do,
and a guard that stopped it would be wrong far more often than right. What it
does is tell the agent what it just opened, so the contents do not end up
quoted back into a commit message, a summary, or a file it writes next.

Exit code is always 0. The value is entirely in the stderr line.

Derived from Alfred Dev (MIT) — see ATTRIBUTION.md.
"""

import json
import os
import sys

BRAND = "ClaudeFlow safety"
OPT_OUT_ENV = "CLAUDEFLOW_SAFETY_OFF"


def _is_env_file(name, _ext):
    return name == ".env" or name.startswith(".env.")


def _is_private_key(_name, ext):
    return ext in (".pem", ".key", ".p12", ".pfx")


def _is_ssh_key(name, _ext):
    return name in ("id_rsa", "id_ed25519", "id_ecdsa", "id_dsa")


def _is_service_credentials(name, ext):
    lowered = name.lower()
    if lowered in {
        "credentials.json", "service-account.json", "gcloud-credentials.json",
        ".npmrc", ".pypirc", "terraform.tfstate",
    }:
        return True
    if ext != ".json":
        return False
    return (
        lowered.startswith("service-account")
        or lowered.startswith("firebase-adminsdk")
        or lowered.endswith("-service-account.json")
    )


def _is_htpasswd(name, _ext):
    return name == ".htpasswd"


def _is_keystore(_name, ext):
    return ext in (".jks", ".keystore")


# Matched against the file's base name.
_NAME_RULES = [
    (_is_env_file, "this is an environment file"),
    (_is_private_key, "this is a private key or certificate"),
    (_is_ssh_key, "this is an SSH private key"),
    (_is_service_credentials, "this file holds service credentials"),
    (_is_htpasswd, "this is an Apache password file"),
    (_is_keystore, "this is a Java keystore"),
]

# Matched against the full path. AWS `credentials` and `config` live here
# rather than in the name rules — those two words are far too common alone.
_PATH_RULES = [
    (".aws/credentials", "these are AWS credentials"),
    (".aws/config", "this is AWS config, which may carry credentials"),
    ("/.docker/config.json", "these are Docker registry credentials"),
    ("/.kube/config", "this is Kubernetes cluster config"),
    ("/.terraform/terraform.tfstate", "this is Terraform state, which may carry secrets"),
    (".ssh/", "this is inside the SSH directory"),
    (".gnupg/", "this is inside the GPG directory"),
]


def describe(file_path):
    path = file_path.replace("\\", "/")
    name = os.path.basename(path)
    _, ext = os.path.splitext(name)

    for fragment, label in _PATH_RULES:
        if fragment in path:
            return label
    for rule, label in _NAME_RULES:
        if rule(name, ext.lower()):
            return label
    return None


def main():
    if os.environ.get(OPT_OUT_ENV):
        sys.exit(0)
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not file_path:
        sys.exit(0)

    label = describe(file_path)
    if label:
        print(
            f"[{BRAND}] heads up — {label}. "
            f"Do not quote the contents into commits, summaries, or files you write.",
            file=sys.stderr,
        )
    sys.exit(0)


if __name__ == "__main__":
    main()
