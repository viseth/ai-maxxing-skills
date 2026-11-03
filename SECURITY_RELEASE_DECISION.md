# Security review — final decision (phases 13–16)

**Decision: NO-GO for unattended/global installation or production deployment.** This is a review milestone, **not** a security certification. Do not merge this pull request solely because CI passes.

## Phase 13 — privileged scripts
- Replaced root execution of user-controlled Cloudflare environment files with literal-only parsing; malicious input regression tests run in CI.
- Restricted unreviewed auto-installers: Hermes skills no longer fetch mutable Node/npm CLI packages, dashboard `install-node` is blocked, and VPS exposure requires independently installed Caddy/cloudflared packages.
- Added guards for caller-controlled systemd environment values and service ports in dashboard and Hermes scripts.
- `import-keys.sh` remains intentionally blocked with exit 78. The legacy code remains below the early exit; remove it in a future cleanup.

## Phase 14 — HTTP and proxy validation
- `gate.py` localhost HTTP integration tests cover network-only read access, writes requiring sessions, admin/member roles, expired/forged sessions, missing proxy methods, malformed forms and spoofed identity headers.
- `tests/test_caddy_config.sh` builds representative gate and site configuration from the actual `gate_snippet` function and runs `caddy validate` in CI. **This is syntax/configuration validation, not a running end-to-end reverse-proxy test.**
- No Cloudflare Tunnel, real DNS, actual browser, remote server, or local process isolation test has been run.

## Phase 15 — dependency and supply-chain review
- Some skills still reference mutable branches, external downloads, and third-party tools. Heuristic findings in `scripts/security_audit.py` are **inventory only** and do not fail CI; a green workflow must not be interpreted as no security findings.
- Dashboard `pnpm install --frozen-lockfile`, unit tests, and typecheck run in CI. A full dependency vulnerability audit, transitive integrity review, license review, and signed-release provenance verification have **not** been completed.
- CI GitHub Actions use version tags, not immutable action SHAs. Node and pnpm bootstrap for deployment require an independently reviewed installation process.
- Skill text and examples are not an enforced sandbox; running unreviewed skills with broad Claude Code permissions remains risky.

## Phase 16 — acceptance criteria and decision
Release only after all conditions are met:
1. Verify the exact checked-out commit, all external dependencies, downloaded binaries and action revisions; resolve all high/critical scanner findings with evidence or documented exceptions.
2. Run a disposable Linux VPS test with a real Caddy + gate + Hermes dashboard deployment. Test untrusted identity headers, direct local-port access, all write endpoints, CSRF protections and non-admin/allowlisted users.
3. Review service users, bind addresses, filesystem ownership, secrets, systemd unit isolation and firewall rules. Prove no application is reachable through an alternate route.
4. Exercise rollback and migration from existing credential files; verify no secrets enter logs, command arguments, or user-readable files.
5. Perform independent manual review of the final diff and approve explicitly. Keep the PR as draft and do not deploy until this is done.

**Scope limitation:** These phases establish a defensible risk register and targeted automated checks. They do not establish that the repository is safe for unrestricted installation.
