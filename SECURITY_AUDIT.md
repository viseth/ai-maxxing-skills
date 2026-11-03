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
