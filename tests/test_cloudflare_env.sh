#!/usr/bin/env bash
set -euo pipefail
script="skills/setup-vps/scripts/expose.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
# Extract only the pure credential loader; do not execute the privileged script.
awk '/^load_cf\(\) \{/ {active=1} active {print} active && /^\}/ {exit}' "$script" > "$tmp/loader.sh"
source "$tmp/loader.sh"
export CLOUDFLARE_ENV_FILE="$tmp/cloudflare.env"
cat > "$CLOUDFLARE_ENV_FILE" <<'EOF'
# Typical literal env format
export CLOUDFLARE_API_TOKEN='test-token_123'
CLOUDFLARE_ACCOUNT_ID="0123456789abcdef0123456789abcdef"
EOF
load_cf
[[ "$CLOUDFLARE_API_TOKEN" == "test-token_123" ]]
[[ "$CLOUDFLARE_ACCOUNT_ID" == "0123456789abcdef0123456789abcdef" ]]
cat > "$CLOUDFLARE_ENV_FILE" <<EOF
CLOUDFLARE_API_TOKEN=\$(touch "$tmp/pwned")
CLOUDFLARE_ACCOUNT_ID=0123456789abcdef0123456789abcdef
EOF
if load_cf >/dev/null 2>&1; then
  echo "malicious credential file unexpectedly accepted" >&2
  exit 1
fi
[[ ! -e "$tmp/pwned" ]] || { echo "code executed from credential file" >&2; exit 1; }
printf '%s\n' 'CLOUDFLARE_API_TOKEN=abc' '. /tmp/untrusted.sh' > "$CLOUDFLARE_ENV_FILE"
if load_cf >/dev/null 2>&1; then
  echo "shell source directive unexpectedly accepted" >&2
  exit 1
fi
ln -sf "$tmp/other" "$tmp/symlink"
export CLOUDFLARE_ENV_FILE="$tmp/symlink"
if load_cf >/dev/null 2>&1; then
  echo "symlink unexpectedly accepted" >&2
  exit 1
fi
echo "Cloudflare env parser tests passed"
