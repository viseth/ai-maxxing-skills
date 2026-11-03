# Security hardening workstream (IN PROGRESS)

Upstream: Melvynx/ai-maxxing-skills. Baseline tree SHA: `7b12ee7bd846d1a399f71792057db6b96cac54e5`.

## Scope and status
- Inventory: 232 tracked blobs, 44 SKILL.md files (some nested), 17 executable-mode blobs. The CLI previously reported 39 discoverable skills; nested skills and invalid YAML affect that count.
- **Not a completed security audit.** No claim of malware-free or safe-to-install status.
- This branch is a preliminary security hold and should **not** be installed globally or merged until all remaining checks pass.

## Confirmed findings
1. HIGH: `skills/setup-vps/scripts/import-keys.sh` forwards the workstation's GitHub token to a remote VPS (`gh auth token | remote 'gh auth login --with-token'`). This can replicate broad workstation access on a server. **Mitigation:** script fails closed; replace with dedicated least-privilege credentials.
2. HIGH: `skills/setup-vps/SKILL.md` directs the agent to enable autonomous approvals and to copy credentials to the VPS. **Mitigation:** instructions now require approval and forbid these operations by default. Further review needed for every referenced script.
3. HIGH: `skills/connect-tool/SKILL.md` accepts API keys pasted in chat and interpolates them into a shell command. **Mitigation:** disallow keys in chat; require masked local auth.
4. MEDIUM/HIGH: multiple instructions retrieve scripts from mutable GitHub `main` branches. **Partial mitigation:** replaced this behavior in two reviewed skills. Repository-wide scan and pinning still needed.
5. INSTALL FAILURE: `skills/setup-vps/SKILL.md` frontmatter description has an unquoted colon, producing a YAML parse error. **Open**: fix frontmatter and validate all skills.

## Audit queue (not yet cleared)
- Review every `SKILL.md` and all scripts, including shell, Python, JS/MJS and the Hermes dashboard application.
- Identify command injection, untrusted downloads, credential exfiltration, excessive OAuth/API scopes, remote execution, prompt injection and destructive operations.
- Validate YAML frontmatter and file references.
- Add CI: frontmatter validation, secret scanning, shellcheck, static analysis, dependency audits and pinned workflow actions.
- Add negative tests for blocked credential forwarding and unapproved autonomy.
- Re-run Snyk/Socket/Gen assessments and investigate each finding by exact identifier.

## Release criteria
No high/critical unresolved findings, reproducible CI and documented threat model, human review of security-sensitive changes, and test install in an isolated environment with no production credentials.

## Subsequent work (2026-11-03)
- The heuristic scanner identified **83 matches**, including duplicates and scanner self-matches; these are **not 83 confirmed vulnerabilities**. Self-scanning has since been excluded.
- `initialize.sh` previously enabled `bypassPermissions` and created `--dangerously-skip-permissions` aliases. Its global bootstrap now fails closed; default permission mode and aliases were corrected. **The original install flow is intentionally nonfunctional pending redesign.**
- `hermes.sh` previously executed remote shell installers and supported `autonomy` disabling approvals and instruction protections. Both are now blocked, and package updates no longer fetch mutable upstream.
- `connect-vps` previously added broad wildcard SSH permissions to Claude settings. This instruction has been removed.
- `connect-tool/scripts/cli_template.py` now blocks redirects, requires HTTPS base URLs, disables arbitrary API paths and non-interactive login, and requires `--yes` for writes. **Caution:** `--yes` is not an independent human-approval boundary if an agent can pass it; the agent permission system must enforce approval separately.
- CI runs bash syntax checks, negative tests for blocked legacy credential forwarding and autonomy, Python AST checks and connect-tool negative tests. The latest expanded CI run must pass before treating these as verified.
- Remaining open issues: raw credentials saved in a JSON config (mode 0600, not OS credential manager); generic API client may still accept a provider-configured unexpected domain; `gate.py`, `expose.sh`, `discord.sh` and Hermes dashboard need deeper review; exact Snyk/Socket findings unverified; unpinned GitHub Actions and dependencies; README still includes legacy installation examples under a warning.
- Release remains **BLOCKED** until the remaining scripts are audited and the findings triaged.

## VPS authentication and Cloudflare review (continued)
- **HIGH confirmed:** `gate.py` treated an IP allowlist match as the `admin` role even for `/.gate/verify?need=admin`. The bypass is removed for administrator-only endpoints; allowlisted IPs may still access non-admin resources without login. This remaining network-based trust must be assessed against the deployment threat model.
- **MEDIUM/HIGH confirmed:** `expose.sh` interpolated a caller-provided hostname into Caddy configuration and file paths without strict validation. Add/remove now validate DNS-like hostnames and add validates the TCP port.
- **MEDIUM:** inbound `X-Gate-User` and `X-Gate-Role` headers could be attacker-controlled if upstream header handling was incomplete. The generated Caddy site now strips these headers before forward-auth copies verified values. **Requires actual Caddy integration test** to confirm directive ordering and that identity headers are only supplied by the gate.
- **MEDIUM:** `expose.sh` previously supplied the Cloudflare API token as a curl command-line argument; it now supplies that header via a process-substitution file descriptor. The token remains in a sourced environment file and requires restricted permissions and scope.
- The CI currently uses shell/Python syntax and static regression assertions. **It does not perform an end-to-end HTTP authorization or Caddy configuration test.**
- **Open:** review all remaining trust boundaries in `gate.py`, including the localhost `X-Gate-IP` header, session lifetime, CSRF coverage, IP allowlist behavior, and Caddy proxy configuration; review Cloudflare token lifecycle and origin restrictions.

## Hermes dashboard server review (continued)
- **HIGH confirmed:** `src/server/viewer.ts` previously treated missing `X-Gate-Role` as administrator (a supposed local trusted caller). The default is now `member`, and admin additionally requires a nonempty authenticated email. Existing unit tests were updated.
- **HIGH architecture risk still open:** `X-Gate-Role` and `X-Gate-User` are unsigned proxy headers. If the dashboard can be reached directly, an attacker can spoof both headers. Deployment **must** bind the dashboard to loopback, ensure the gate is the only network entry point, and verify that Caddy strips incoming identity headers. Consider cryptographically authenticated proxy identity rather than trusting raw headers.
- **MEDIUM confirmed:** `src/server/api.ts` previously used `request.text()` before checking its size, permitting large request-body allocations. It now reads the stream with a byte limit and cancels oversized requests. Unit tests added but not yet run under the dashboard's Node/Vitest toolchain.
- **Open:** run the complete dashboard `pnpm test` and `pnpm typecheck` on Node >=24, inspect the full dependency tree and lockfile, and add HTTP end-to-end tests.

## Dashboard CI verification (continued)
- `pnpm-lock.yaml` contained two concatenated YAML documents. Removed the short first document, retaining the complete lockfile.
- GitHub Actions now has a dedicated dashboard job with Node 24, Corepack/pnpm frozen lockfile installation, `pnpm test` and `pnpm typecheck`. **Both jobs succeeded** in run `41735998309` at commit `fa92c193531a670ff2c0acef3850ed8d5596a84d`.
- The new unit tests exercise the missing-role admin denial and streamed JSON byte limits. This is **not** a deployed Caddy/Gate integration test.
- **Release-blocking architecture concern:** unsigned proxy identity headers remain trusted for administrator authorization. Dashboard must not be reachable except through the trusted proxy, and local users/processes able to call loopback must be considered in the threat model. An authenticated proxy-to-app channel is recommended.
- GitHub Actions actions are referenced by major tags rather than immutable SHA pins. Dependency vulnerability scanning and provenance verification are still outstanding.

## Skill supply-chain and gate form hardening (continued)
- Replaced mutable `raw.githubusercontent.com/.../main` download guidance in 12 additional skill instructions with local, reviewed-checkout guidance. This reduces **documented** supply-chain exposure but does not automatically pin every dependency or remove every mutable download elsewhere.
- `setup-brain` now requires explicit approval and backups before replacing global Claude/Codex configuration. This is a skill-instruction control, not an OS-enforced permission boundary.
- `gate.py` form parsing now rejects missing/nondecimal/oversized `Content-Length`, invalid UTF-8, and more than 32 URL-encoded form fields; malformed requests return HTTP 400. The workflow includes static assertions, **not HTTP integration tests**.
- The previous GitHub Actions run `41736284930` succeeded after the skill instruction edits; gate form changes were awaiting validation at documentation time.
- Release remains BLOCKED: additional mutable downloads, unpinned installers, secret-handling paths and proxy trust assumptions require review.

## Gate allowlist authorization refinement
- **HIGH confirmed:** a saved client IP previously bypassed authentication for all HTTP methods on non-admin applications. Now IP-only authorization is limited to original `GET` and `HEAD` requests, as passed by Caddy in `X-Forwarded-Method`. Other methods require an authenticated session.
- **Usability/security fix:** a saved IP no longer prevents the visitor from reaching the login page to obtain a session for write operations.
- **Important limitations:** HTTP GET/HEAD are assumed read-only; any state-changing GET endpoint remains vulnerable. The gate trusts the proxy-supplied original method and IP; direct access to the gate listener or spoofable proxy headers can undermine these checks. Real HTTP integration tests and a network boundary audit remain required.
- CI adds static assertions for the method restriction. No end-to-end request authorization test has yet been executed.

## Localhost HTTP integration tests for VPS gate
- Added `tests/test_gate_http.py`, which starts the real `ThreadingHTTPServer` gate on a loopback ephemeral port with temporary fixtures and sends HTTP requests using the standard library. It does not contact production services.
- The matrix covers anonymous and allowlisted IP access, GET/HEAD versus mutating methods, admin-only routes, member/admin session roles, invalid cookies, missing proxy IP, malformed form requests, and login reachability from an allowlisted IP.
- The inventory CI job now installs test-only `bcrypt==4.2.1` and runs `python3 -m unittest discover -s tests -p 'test_gate_http.py' -v`. This adds behavior coverage beyond string assertions.
- **Still untested:** the actual Caddy/Cloudflare proxy integration, externally reachable interfaces, cross-site browser behavior, direct dashboard access, and GET endpoints with side effects.

## Additional gate and Caddy findings
- **HIGH confirmed deployment bug:** the generated Caddy site used `echo "\\trequest_header ..."`, which can emit a literal backslash-t rather than a Caddy indentation character, potentially preventing configuration parsing. Replaced both directives with `printf` and added a CI assertion. A real `caddy validate` run is still outstanding.
- **MEDIUM:** `expose.sh` Cloudflare API helper previously used unquoted conditional argument expansion for JSON request bodies. Replaced it with a Bash argument array and explicit curl failure handling. Credentials are still supplied via a file descriptor rather than a process argument.
- Added 3 HTTP integration tests for expired sessions, missing/invalid forwarded methods, and spoofed role headers on write requests. First CI run revealed that the gate defaulted a missing forwarded method to GET, returning 302 instead of the expected 401. Changed that fallback to fail closed. **New CI result must be checked before declaring the tests green.**
- A forged original method or IP remains possible if an untrusted local caller can directly access the gate; Caddy-to-gate authentication and host firewall/process isolation remain release-blocking.
