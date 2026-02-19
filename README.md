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
| [handoff](.claude/skills/handoff/) | 2.1.0 | Creates HANDOFF.md so new sessions can pick up where the last one left off |
| [syncing-docs](.claude/skills/syncing-docs/) | 2.0.0 | Detects drift between code and project state files, fixes owned docs |
| [managing-doc-manifest](.claude/skills/managing-doc-manifest/) | 1.0.0 | Creates `.doc-manifest.yaml` — a registry of docs and their code references |
| [wrap](.claude/skills/wrap/) | 1.0.0 | End-of-session coordinator: sync docs, audit CLAUDE.md, then handoff |

During work, `syncing-docs` keeps documentation in sync with code changes. At the end of a session, `wrap` chains sync-docs → [claude-md-improver](https://github.com/anthropics/skills) (Anthropic plugin) → handoff. The result is a HANDOFF.md snapshot so a new session can resume with "Read HANDOFF.md and continue."

Claude Code sessions are ephemeral, but project context shouldn't be. These skills maintain CLAUDE.md, TODO.md, HANDOFF.md, and `.doc-manifest.yaml` as persistent state files that survive `/clear` and crashes.

### Research

| Skill | Version | Description |
|-------|---------|-------------|
| [study](.claude/skills/study/) | 1.0.0 | Structured web research with source verification and hypothesis tracking |

Standalone skill. No dependencies on other skills in this collection.

## Why These Exist

Claude Code sessions are stateless — context is lost on `/clear` or crash. After enough sessions where I had to re-explain project state from scratch, I built these skills to fix three things:

- `handoff` captures what was done, what failed, and what's next. A new session reads HANDOFF.md and picks up where the last one left off.
- `syncing-docs` detects when code changes make docs stale and fixes them. No more outdated README sections or wrong file paths in CLAUDE.md.
- The meta-tooling skills (`creating-skills`, `updating-skills`, `auditing-skills`, `testing-skills`) enforce consistency so skills don't degrade as you iterate on them.

## Installation

### Guided install via AI agent

If you're using Claude, you can paste this repo URL into the chat and ask Claude to guide you through installation. Claude will read this README, enumerate the available skills with descriptions, ask which ones you want, check what's already installed, and copy the selected skills to `~/.claude/skills/`.

**Instructions for the AI agent:**

1. Read all `SKILL.md` files under `.claude/skills/` in this repo (fetch from GitHub if not cloned locally). Parse the `name`, `description`, and `metadata.tags` from each frontmatter.
2. Group skills by tag and present them to the user with their descriptions. For each skill, note whether it is already installed at `~/.claude/skills/{name}/` and if so, the installed version vs. the repo version.
3. Ask the user which skills to install. Accept: individual names, tag groups (e.g. "all session management skills"), or "all".
4. Warn about dependencies: if the user selects `wrap`, note it also needs `handoff`, `syncing-docs`, and `managing-doc-manifest`. If they select `updating-skills`, note it works best alongside `auditing-skills` and `testing-skills`.
5. For each selected skill, copy the skill directory to `~/.claude/skills/{name}/`. If a version is already installed, confirm before overwriting.
6. After installing, confirm what was installed and the slash command to invoke each (e.g. `/handoff`, `/study`).

### Option 1: Clone into a project (project-level)

```bash
# Clone into your project — skills are auto-discovered
git clone https://github.com/gradigit/claude-skills.git /tmp/claude-skills
cp -r /tmp/claude-skills/.claude/skills/* your-project/.claude/skills/
```

### Option 2: Install globally (all projects)

```bash
git clone https://github.com/gradigit/claude-skills.git /tmp/claude-skills
cp -r /tmp/claude-skills/.claude/skills/* ~/.claude/skills/
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

updating-skills ──→ creating-skills (spec rules)
                └──→ auditing-skills (validation checklist)
                └──→ testing-skills (run evaluations)

testing-skills ──→ creating-skills (EVALUATIONS.md format)

study (standalone)
```

`wrap` chains three skills sequentially. If a dependency isn't installed, that step can be skipped — but the full workflow works best with all session management skills present.

### External dependencies

| Dependency | Required by | Type | How to get it |
|------------|-------------|------|---------------|
| [claude-md-improver](https://github.com/anthropics/skills) | `wrap` (step 2) | Anthropic official plugin | Install from anthropics/skills |

### Optional integrations

- `syncing-docs` checks for an `architect/` directory (created by [forging-plans](https://github.com/gradigit/forging-workflow)). If it doesn't exist, this is silently skipped.
- `handoff` references CLAUDE.md, TODO.md, and `architect/` files if present. None are required.

## Customization

These skills are workflow opinions. They assume:
- Projects should have a CLAUDE.md for persistent context
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
