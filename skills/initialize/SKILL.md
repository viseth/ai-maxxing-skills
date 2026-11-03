---
name: initialize
description: Install selected base skills with explicit approval, retaining normal Claude Code and Codex permissions. Do not enable unattended execution.
---

Give every agent on this computer the base skills, in every folder. Do it yourself and talk to the user in their language, short, no jargon (never say "symlink" or "npx" to them).

Only use a reviewed local checkout pinned to a known commit. Never execute downloaded scripts from a mutable branch.

1. Check Node locally. If missing, ask the user to install it from verified official documentation.
2. Run the one command, in the background when your tool allows it (2 to 5 minutes):
   ```bash
   Do not pipe remote scripts to Bash. Review and run the local `scripts/initialize.sh` only after the security release gate passes.
   ```
   Everything comes from this kit, nothing from elsewhere. It installs, for Claude Code and Codex:
   - `skill-manager` (installs, updates or removes a skill from a name or a link, and creates or fixes their own skills), `/show-me` (explains anything with a small diagram or visual), `/grill-me` (sharpens an idea with questions before building), `/wait-what` (re-explains the last message in plain words when the user is lost), `/connect-tool` (connects any tool like Notion or Stripe) and `/use-style` (gives pages, apps and documents a named visual style like Vercel, Stripe or Linear);
   - the settings: keep Claude Code and Codex permission prompts enabled and preserve existing user policies;
   - the shortcuts in the terminal: `cc` opens Claude Code without questions, `ccc` continues the last conversation, `cx` opens Codex, `cxc` resumes the last Codex one.
   On Windows, keep Claude Code permission prompts enabled. Do not create aliases containing `--dangerously-skip-permissions`.
3. Every skill lands once in `~/.agents/skills/` (the single source, Codex reads it there), and `~/.claude/skills/` only links to it. The script ends with an `ok` or `MISS` line per skill: fix a `FAIL` or `MISS` by rerunning its line and reading the error, never by copying files by hand into `~/.claude/skills`. An `old=` line lists developer skills an older `/initialize` installed (apex, arena, app-icon...): they are not part of the kit anymore. Ask once whether to remove them; on yes run `bash ~/.agents/skills/skill-manager/scripts/skills.sh remove <names>` (they are kept in `~/.cache/removed-skills`, so it can be undone). Never remove them without asking: they may be the user's own.
4. **Style.** Open the style gallery so the user sees every style side by side: `~/.agents/skills/use-style/examples/gallery.html` (`open` on Mac, `xdg-open` on Linux, `start` on Windows). Ask one question: which style speaks to them most, the one they would like for their pages, apps and documents. Give the names with their one-line description from the gallery, and say they can click a card to see it full size. When they hesitate, recommend `vercel`. When `~/.agents/AGENTS.md` already has a `## Style` section, show its style and ask only whether to keep it.
5. **Global rule.** Write their choice in the global rules, `~/.agents/AGENTS.md` (create it when missing; `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` link to it once `setup-brain` ran). When it already has a `## Style` section, replace that section up to the next `## ` heading and keep every other line; otherwise add it at the end, after one blank line:
   ```markdown
   ## Style

   When you create a file the user will look at (a page, an app screen, a dashboard, an HTML report, a document, a visual), use the `use-style` skill with the `<chosen style>` style, unless the user asks for another one or the project already has its own design.
   ```
   When `~/.claude/CLAUDE.md` is a separate file (not a link to `~/.agents/AGENTS.md`), write the same section there too.
6. Tell the user in 3 lines what is installed (and that `cc` works in a new terminal window), that a new session shows `/show-me`, `/grill-me`, `/wait-what`, `/connect-tool` and `/use-style`, which style is now their default (they can change it any time by asking), and that running `/initialize` again updates the skills.
