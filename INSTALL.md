# claude-skills — Installation Guide

Agent Skills for Claude Code: session management, skill tooling, research, and autonomous forge workflows.

Full skill descriptions and dependency graph: [README.md](README.md)

---

## For AI Agents

**If a user gave you this repo URL and asked to install skills** (or just pasted the URL expecting installation):

1. Follow the install wizard below — steps 1–9 in order
2. Use `AskUserQuestion` for all interactive prompts where available
3. Copy only the selected skills to the user's chosen location
4. Do NOT clone this repo into the user's project or explore the codebase

**If the user pasted only the URL with no other instructions**, ask:

> "Would you like me to install skills from this repo? I'll walk you through picking which ones you need."

---

## Install Wizard

**Step 1 — Language**

Ask (single select):
```
[ ] English
[ ] 한국어
```
Use the chosen language for all questions, descriptions, and confirmations from this point on. Skill file contents (SKILL.md) are always in English and should not be modified — only the wizard UI is translated.

**Step 2 — Check installed state (silent)**

Check `~/.claude/skills/` for any skills already installed from this repo. Compare versions against the repo. If any are installed, proceed to Step 3. Otherwise skip to Step 4.

**Step 3 — Returning user (only if skills already installed)**

Ask (single select):
```
[ ] Update my installed skills
[ ] Install skills I don't have yet
[ ] Both
```
Show a version diff before proceeding, e.g.: "`handoff` 2.4.0 → 2.5.0 · `syncing-docs` 2.5.0 → 2.6.0"

**Step 4 — Detail level**

Ask (single select):
```
[ ] Full explanation — walk me through each skill with use cases and examples
[ ] Basic explanation — just the one-liners
[ ] I'm an experienced user, I'll select the skills myself
```

**Step 5 — Present skills and pick**

Fetch all `SKILL.md` files from `.claude/skills/` in this repo. Parse `name`, `description`, and `metadata.tags` from each frontmatter. Present skills grouped by category at the detail level chosen in Step 4. Mark already-installed skills with their current version.

Then ask (multi-select):
```
[ ] {skill name} — {description}
[ ] ...
```

**Step 6 — Install location**

Ask (single select):
```
[ ] ~/.claude/skills/ — global, works in all projects (Recommended)
[ ] .claude/skills/ — current project only
```

**Step 7 — Dependency resolution (silent)**

Before installing, auto-resolve dependencies:
- `wrap` requires `handoff`, `syncing-docs`, `managing-doc-manifest` — add any missing ones and tell the user
- `wrap --with-fresh` additionally requires `handoff-fresh`
- `updating-skills` works best with `auditing-skills` and `testing-skills` — add if missing and tell the user
- If a skill dir already exists but is not from this repo, warn before overwriting

**Step 8 — Install**

Copy each selected skill directory to the chosen location. For each skill being overwritten, show the version change (e.g. `handoff` 2.4.0 → 2.5.0).

Also copy matching command entry files from `.claude/commands/` when present so slash-command paths stay explicit.

For forge skills: also copy `.claude/agents/forge-*.md` to the user's `~/.claude/agents/` (or `.claude/agents/`).

**Step 9 — Post-install summary**

List every installed skill with its slash command (e.g. `/handoff`, `/study`). For users who chose full or basic explanation, show one example prompt per skill. End with:

> "To get updates or install more skills later, just paste this repo link into Claude again."
