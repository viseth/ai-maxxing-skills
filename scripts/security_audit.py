#!/usr/bin/env python3
"""Conservative, read-only heuristic scanner for agent skills (not a security certification)."""
import argparse
import json
import pathlib
import re
import sys

PATTERNS = {
    "mutable_raw_github": (r"raw\.githubusercontent\.com/[^\s\x60'\"]+/(?:main|master)/", "high"),
    "download_pipe_shell": (r"(?:curl|wget)[^\n|]{0,250}\|\s*(?:sudo\s+)?(?:bash|sh)\b", "high"),
    "chat_secret_in_shell": (r"printf[^\n]{0,160}(?:<key>|api.?key|token)", "high"),
    "unattended_agent": (r"dangerously-skip-permissions|hermes-setup autonomy", "high"),
    "broad_remote_allow": (r"Bash\((?:ssh|scp|rsync)\s+[^)]*\*\)", "high"),
    "unversioned_install": (r"npx\s+(?:-y\s+)?[^\s\x60]+@latest|npm\s+install\s+-g\s+[^\s\x60]+", "medium"),
}
# Findings are intentionally not suppressed by prose disclaimers; review manually.
def scan(root):
    findings = []
    skills = list((root / "skills").rglob("SKILL.md"))
    for path in sorted(p for p in root.rglob("*") if p.is_file() and ".git" not in p.parts):
        if path.suffix.lower() not in {".md", ".sh", ".py", ".js", ".mjs", ".ts"} and path.name not in {"image_gen", "chrome-ai", "dashboard-cli"}:
            continue
        try:
            data = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        rel = str(path.relative_to(root)).replace("\\", "/")
        if path.name == "SKILL.md":
            if not data.startswith("---\n") or "\n---\n" not in data[4:]:
                findings.append({"file": rel, "line": 1, "rule": "invalid_frontmatter", "severity": "high"})
            else:
                fm = data.split("---", 2)[1]
                if not re.search(r"(?m)^name:\s*[^\s]", fm) or not re.search(r"(?m)^description:\s*[^\s]", fm):
                    findings.append({"file": rel, "line": 1, "rule": "missing_metadata", "severity": "medium"})
        for rule, (pattern, severity) in PATTERNS.items():
            for match in re.finditer(pattern, data, flags=re.IGNORECASE):
                findings.append({"file": rel, "line": data.count("\n", 0, match.start()) + 1, "rule": rule, "severity": severity})
    return {"skill_files": len(skills), "findings": findings, "note": "Heuristic findings require manual verification; this is not an audit certification."}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path, default=pathlib.Path("."))
    parser.add_argument("--output", type=pathlib.Path)
    args = parser.parse_args()
    report = scan(args.root.resolve())
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(f"Scanned {report['skill_files']} SKILL.md files; {len(report['findings'])} heuristic findings")
    for finding in report["findings"][:80]:
        print(f"{finding['severity'].upper()} {finding['file']}:{finding['line']} {finding['rule']}")
    return 0  # Inventory mode: do not claim pass/fail until triage and baseline are complete.

if __name__ == "__main__":
    sys.exit(main())
