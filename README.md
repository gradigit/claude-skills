# claude-skills

Opinionated workflow tools for [Claude Code](https://code.claude.com) that I built and refined through daily use. They handle session management, project documentation, and skill development. They work best as a set, but individual skills can be used standalone where noted.

## Skills

### Meta / Skill Tooling

| Skill | Version | Description |
|-------|---------|-------------|
| [creating-skills](.claude/skills/creating-skills/) | 4.0.0 | Creates new skills through adaptive interviewing or autonomous generation |
| [updating-skills](.claude/skills/updating-skills/) | 2.0.0 | Systematic workflow for modifying skills with version bumps and audits |
| [auditing-skills](.claude/skills/auditing-skills/) | 2.0.0 | Validates skills against the Agent Skills spec and best practices |
| [testing-skills](.claude/skills/testing-skills/) | 1.0.0 | Three-tier evaluation of skills (triggering, functional, performance) |

These four form a lifecycle: create a skill, update it as you iterate, audit it for quality, test it with evaluations. `updating-skills` references `creating-skills` for spec compliance and `auditing-skills` for the validation checklist. `testing-skills` runs EVALUATIONS.md scenarios to verify skill behavior.

### Session Management

| Skill | Version | Description |
|-------|---------|-------------|
| [handoff](.claude/skills/handoff/) | 2.4.0 | Creates HANDOFF.md so new sessions can pick up where the last one left off |
| [handoff-fresh](.claude/skills/handoff-fresh/) | 1.8.0 | Builds a fork-safe onboarding bundle for a brand-new agent in forked/new-folder repos |
| [syncing-docs](.claude/skills/syncing-docs/) | 2.6.0 | Detects drift between code and project state files, fixes owned docs (CLAUDE.md + AGENTS.md) |
| [managing-doc-manifest](.claude/skills/managing-doc-manifest/) | 1.0.0 | Creates `.doc-manifest.yaml` — a registry of docs and their code references |
| [wrap](.claude/skills/wrap/) | 1.3.0 | End-of-session coordinator: sync docs, run instruction-doc quality pass (CLAUDE.md + AGENTS.md), then handoff (optional fresh bundle) |

During work, `syncing-docs` keeps documentation in sync with code changes. At the end of a session, `wrap` chains sync-docs → [claude-md-improver](https://github.com/anthropics/skills) (Anthropic plugin) → handoff. For forked/new-folder continuation by a brand-new agent, run `handoff-fresh` to generate a full onboarding bundle.

Claude Code sessions are ephemeral, but project context shouldn't be. These skills maintain CLAUDE.md, AGENTS.md, TODO.md, HANDOFF.md, and `.doc-manifest.yaml` as persistent state files that survive `/clear` and crashes.

## Explicit Commands and Hook Model

- Canonical command entry points:
  - `/sync-docs`
  - `/handoff`
  - `/handoff-fresh`
  - `/wrap`
- These flows are manual by default. No implicit side-channel behavior is required.
- Hook guidance and archive-first cleanup policy for deprecated auto-handoff hooks: see [HOOKS.md](HOOKS.md).

### Research

| Skill | Version | Description |
|-------|---------|-------------|
| [study](.claude/skills/study/) | 1.2.0 | Structured web research with source verification and hypothesis tracking |

Standalone skill. No dependencies on other skills in this collection.

## Why These Exist

Claude Code sessions are stateless — context is lost on `/clear` or crash. After enough sessions where I had to re-explain project state from scratch, I built these skills to fix three things:

- `handoff` captures what was done, what failed, and what's next. A new session reads HANDOFF.md and picks up where the last one left off.
- `syncing-docs` detects when code changes make docs stale and fixes them. No more outdated README sections or wrong file paths in CLAUDE.md.
- The meta-tooling skills (`creating-skills`, `updating-skills`, `auditing-skills`, `testing-skills`) enforce consistency so skills don't degrade as you iterate on them.

## Installation

### Guided install via AI agent

Paste this repo URL into Claude and ask it to install skills. Claude will guide you through the full process interactively.

**Instructions for the AI agent:**

Follow these steps in order. Use `AskUserQuestion` for all questions where it is available.

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
Show a version diff before proceeding, e.g.: "`handoff` 2.3.0 → 2.4.0 · `syncing-docs` 2.5.0 → 2.6.0 · `handoff-fresh` 1.7.0 → 1.8.0"

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

Copy each selected skill directory to the chosen location. For each skill being overwritten, show the version change (e.g. `handoff` 2.3.0 → 2.4.0).

Also copy matching command entry files from `.claude/commands/` when present (for example `handoff.md`, `handoff-fresh.md`, `wrap.md`) so slash-command paths stay explicit.

**Step 9 — Post-install summary**

List every installed skill with its slash command (e.g. `/handoff`, `/study`). For users who chose full or basic explanation, show one example prompt per skill. End with:

> "To get updates or install more skills later, just paste this repo link into Claude again."

### Option 1: Clone into a project (project-level)

```bash
# Clone into your project — skills are auto-discovered
git clone https://github.com/gradigit/claude-skills.git /tmp/claude-skills
mkdir -p your-project/.claude/skills your-project/.claude/commands
cp -r /tmp/claude-skills/.claude/skills/* your-project/.claude/skills/
cp -r /tmp/claude-skills/.claude/commands/* your-project/.claude/commands/
```

### Option 2: Install globally (all projects)

```bash
git clone https://github.com/gradigit/claude-skills.git /tmp/claude-skills
mkdir -p ~/.claude/skills ~/.claude/commands
cp -r /tmp/claude-skills/.claude/skills/* ~/.claude/skills/
cp -r /tmp/claude-skills/.claude/commands/* ~/.claude/commands/
```

### Option 3: Use as additional directory

```bash
git clone https://github.com/gradigit/claude-skills.git ~/claude-skills
# Then in Claude Code:
claude --add-dir ~/claude-skills
```

## Dependencies

### Between skills in this collection

```
wrap ──→ syncing-docs ──→ managing-doc-manifest
  │
  └──→ handoff
  └──→ handoff-fresh (optional via --with-fresh)

updating-skills ──→ creating-skills (spec rules)
                └──→ auditing-skills (validation checklist)
                └──→ testing-skills (run evaluations)

testing-skills ──→ creating-skills (EVALUATIONS.md format)

study (standalone)
```

`wrap` chains three skills sequentially by default, with an optional fourth step (`--with-fresh`) for `handoff-fresh`. If a dependency isn't installed, that step can be skipped — but the full workflow works best with all session management skills present.

### External dependencies

| Dependency | Required by | Type | How to get it |
|------------|-------------|------|---------------|
| [claude-md-improver](https://github.com/anthropics/skills) | `wrap` (step 2) | Anthropic official plugin | Install from anthropics/skills |

### Optional integrations

- `syncing-docs` checks for an `architect/` directory (created by [forging-plans](https://github.com/gradigit/forging-workflow)). If it doesn't exist, this is silently skipped.
- `handoff` references CLAUDE.md, AGENTS.md, TODO.md, and `architect/` files if present. None are required.
- `handoff-fresh` emits a fresh-agent bundle at `.handoff-fresh/current/` by default: `claude.md`, `agents.md`, `todo.md`, `handoff.md`, `context.md`, `reports.md`, `artifacts.md`, `state.md`, `prior-plans.md`, `read-receipt.md`, `session-log-digest.md`, `session-log-chunk.md`, `handoff-everything.md`. It also updates root `HANDOFF.md` as a bridge pointer to bundle handoff, supports an agent-internal `--validate-read-gate` preflight check before coding, enforces shared-context parity between bundle `claude.md` and `agents.md`, and keeps log continuity token-budgeted.

## Customization

These skills are workflow opinions. They assume:
- Projects should have CLAUDE.md and AGENTS.md for persistent cross-agent context
- Sessions should end with a handoff for continuity
- Documentation should be tracked with `.doc-manifest.yaml`
- Skills should follow the [Agent Skills spec](https://agentskills.io)

You're free to modify any of these to fit your workflow. The skills are MIT-licensed.

### Common customizations

- Don't want `.doc-manifest.yaml`? Remove `managing-doc-manifest` and the manifest step from `syncing-docs`
- Don't use HANDOFF.md? Use `syncing-docs` standalone without `wrap` or `handoff`
- Want a different HANDOFF.md format? Edit `handoff/templates.md`
- Want different audit rules? Edit `auditing-skills/checklist.md`

## Related

- [forging-workflow](https://github.com/gradigit/forging-workflow) — Companion repo for turning rough ideas into implementation-ready prompts and plans
- [Anthropic Skills](https://github.com/anthropics/skills) — Official skills from Anthropic
- [Agent Skills Spec](https://agentskills.io) — The open standard these skills follow
- [Claude Code Docs: Skills](https://code.claude.com/docs/en/skills) — Official documentation

## License

MIT — see [LICENSE](LICENSE).
