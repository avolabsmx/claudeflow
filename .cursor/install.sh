#!/usr/bin/env bash
# Cursor cloud agent build step (AC-1128).
# Runs once per environment build and is snapshotted, so it must be idempotent.
# Installs the toolchain this repo needs, its dependencies, Gentle AI and Engram.
# Needs no secrets: Engram credentials are read at runtime from Cursor secrets.
set -euo pipefail

NODE_MAJOR=24
GENTLE_AI_VERSION=4.0.0
BIN_DIR="$HOME/.local/bin"
SHARE_DIR="$HOME/.local/share"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PATH="$BIN_DIR:$PATH"
export GENTLE_AI_NO_SELF_UPDATE=1 COREPACK_ENABLE_DOWNLOAD_PROMPT=0 CI=1

log() { printf '[cursor-install] %s\n' "$*"; }

case "$(uname -m)" in
  x86_64 | amd64) NODE_ARCH=x64 GO_ARCH=amd64 ;;
  aarch64 | arm64) NODE_ARCH=arm64 GO_ARCH=arm64 ;;
  *) echo "unsupported architecture: $(uname -m)" >&2; exit 1 ;;
esac

mkdir -p "$BIN_DIR" "$SHARE_DIR" "$HOME/.cursor"

# Make ~/.local/bin visible to every later shell, since exported vars do not survive the snapshot.
persist_path() {
  # shellcheck disable=SC2016 # expanded later by the shell that sources the rc file
  local line='export PATH="$HOME/.local/bin:$PATH"'
  for rc in "$HOME/.bashrc" "$HOME/.profile"; do
    touch "$rc"
    grep -qxF "$line" "$rc" || printf '\n%s\n' "$line" >>"$rc"
  done
}

install_node() {
  if command -v node >/dev/null && [ "$(node -p 'process.versions.node.split(".")[0]')" = "$NODE_MAJOR" ]; then
    log "node $(node -v) already installed"
  else
    local base="https://nodejs.org/dist/latest-v${NODE_MAJOR}.x" tmp file
    tmp="$(mktemp -d)"
    curl -fsSL "$base/SHASUMS256.txt" -o "$tmp/SHASUMS256.txt"
    file="$(awk -v a="linux-${NODE_ARCH}.tar.gz" '$2 ~ a"$" {print $2}' "$tmp/SHASUMS256.txt")"
    curl -fsSL "$base/$file" -o "$tmp/$file"
    (cd "$tmp" && grep " $file\$" SHASUMS256.txt | sha256sum -c -)
    rm -rf "$SHARE_DIR/node"
    mkdir -p "$SHARE_DIR/node"
    tar -xzf "$tmp/$file" -C "$SHARE_DIR/node" --strip-components=1
    for bin in node npm npx corepack; do ln -sf "$SHARE_DIR/node/bin/$bin" "$BIN_DIR/$bin"; done
    rm -rf "$tmp"
    log "installed node $(node -v)"
  fi
  corepack enable --install-directory "$BIN_DIR"
}

install_go() {
  local version
  version="$(awk '/^toolchain go/ {sub("go", "", $2); print $2; exit}' "$REPO_ROOT/go.mod")"
  [ -n "$version" ] || version="$(awk '/^go / {print $2; exit}' "$REPO_ROOT/go.mod")"
  if command -v go >/dev/null && [ "$(go env GOVERSION)" = "go$version" ]; then
    log "go $version already installed"
    return
  fi
  local file="go${version}.linux-${GO_ARCH}.tar.gz" tmp
  tmp="$(mktemp -d)"
  curl -fsSL "https://dl.google.com/go/$file" -o "$tmp/$file"
  echo "$(curl -fsSL "https://dl.google.com/go/$file.sha256")  $tmp/$file" | sha256sum -c -
  rm -rf "$SHARE_DIR/go"
  tar -xzf "$tmp/$file" -C "$SHARE_DIR"
  ln -sf "$SHARE_DIR/go/bin/go" "$BIN_DIR/go"
  ln -sf "$SHARE_DIR/go/bin/gofmt" "$BIN_DIR/gofmt"
  rm -rf "$tmp"
  log "installed $(go version)"
}

install_gentle_ai() {
  if command -v gentle-ai >/dev/null && gentle-ai version 2>/dev/null | grep -q "$GENTLE_AI_VERSION"; then
    log "gentle-ai $GENTLE_AI_VERSION already installed"
  else
    local base="https://github.com/Gentleman-Programming/gentle-ai/releases/download/v${GENTLE_AI_VERSION}"
    local file="gentle-ai_${GENTLE_AI_VERSION}_linux_${GO_ARCH}.tar.gz" tmp
    tmp="$(mktemp -d)"
    curl -fsSL "$base/checksums.txt" -o "$tmp/checksums.txt"
    curl -fsSL "$base/$file" -o "$tmp/$file"
    (cd "$tmp" && grep " $file\$" checksums.txt | sha256sum -c -)
    tar -xzf "$tmp/$file" -C "$tmp" gentle-ai
    install -m 0755 "$tmp/gentle-ai" "$BIN_DIR/gentle-ai"
    rm -rf "$tmp"
  fi
  # Non-interactive install for Cursor; also installs the engram binary and its MCP entry.
  gentle-ai install --agent cursor --preset full-gentleman </dev/null
  command -v engram >/dev/null || { echo "engram was not installed by gentle-ai" >&2; exit 1; }
  log "$(gentle-ai version) / $(engram version | head -n1)"
}

persist_path

# Node is installed everywhere: Gentle AI components (context7, gga) run through npx.
install_node

if [ -f "$REPO_ROOT/pnpm-lock.yaml" ]; then
  (cd "$REPO_ROOT" && pnpm install --frozen-lockfile)
elif [ -f "$REPO_ROOT/package.json" ]; then
  (cd "$REPO_ROOT" && pnpm install)
fi

if [ -f "$REPO_ROOT/go.mod" ]; then
  install_go
  (cd "$REPO_ROOT" && go mod download)
fi

install_gentle_ai
