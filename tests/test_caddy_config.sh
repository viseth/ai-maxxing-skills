#!/usr/bin/env bash
set -euo pipefail
# Validate a representative local Caddy config with the exact gate_snippet() implementation.
# No tunnel, DNS, root service, or production app is started.
command -v docker >/dev/null || { echo "Docker required for isolated pinned-version Caddy validation" >&2; exit 3; }
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
sed -n '/^gate_snippet()/,/^# The gate:/p' skills/setup-vps/scripts/expose.sh | sed '$d' > "$tmp/gate-function.sh"
source "$tmp/gate-function.sh"
GATE_AUTH_PORT=9180
gate_snippet gate /.gate/verify > "$tmp/gate.caddy"
gate_snippet gate_admin '/.gate/verify?need=admin' >> "$tmp/gate.caddy"
cat > "$tmp/site.caddy" <<'EOF'
http://example.test:8080 {
  request_header -X-Gate-User
  request_header -X-Gate-Role
  import gate
  reverse_proxy 127.0.0.1:8794
}
http://admin.example.test:8080 {
  request_header -X-Gate-User
  request_header -X-Gate-Role
  import gate_admin
  reverse_proxy 127.0.0.1:8794
}
EOF
cat > "$tmp/Caddyfile" <<EOF
{
  admin off
  auto_https off
  default_bind 127.0.0.1
  servers {
    trusted_proxies static 127.0.0.1/32 ::1/128
    client_ip_headers CF-Connecting-IP
  }
}
import $tmp/gate.caddy
import $tmp/site.caddy
EOF
docker run --rm --network none --read-only --cap-drop ALL --security-opt no-new-privileges \
  --mount "type=bind,src=$tmp,dst=$tmp,readonly" \
  caddy:2.10.2 validate --config "$tmp/Caddyfile" --adapter caddyfile
echo "Representative gate + app Caddy configuration validated"
