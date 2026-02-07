# claude-skills

A collection of Claude Code skills for structured workflows, session management, and skill development. Built for [Claude Code](https://code.claude.com) — Anthropic's CLI tool.

These skills are opinionated workflow tools that I built and refined through daily use. They encode specific patterns for managing Claude Code sessions, maintaining project documentation, and creating new skills. They work best as a cohesive set, but individual skills can be used standalone where noted.

## Skills

### Meta / Skill Tooling

| Skill | Version | Description |
|-------|---------|-------------|
| [creating-skills](.claude/skills/creating-skills/) | 3.1.0 | Creates new skills through adaptive interviewing or autonomous generation |
| [updating-skills](.claude/skills/updating-skills/) | 1.0.0 | Systematic workflow for modifying skills with version bumps and audits |
| [auditing-skills](.claude/skills/auditing-skills/) | 1.0.0 | Validates skills against the Agent Skills spec and best practices |

These three form a lifecycle: **create** a skill, **update** it as you iterate, **audit** it for quality. `updating-skills` references `creating-skills` for spec compliance rules and `auditing-skills` for the validation checklist.

### Session Management

| Skill | Version | Description |
|-------|---------|-------------|
| [handoff](.claude/skills/handoff/) | 2.1.0 | Creates HANDOFF.md files for seamless session continuation after `/clear` |
| [syncing-docs](.claude/skills/syncing-docs/) | 2.0.0 | Detects drift between code and project state files, fixes owned docs |
| [managing-doc-manifest](.claude/skills/managing-doc-manifest/) | 1.0.0 | Creates `.doc-manifest.yaml` — a registry of docs and their code references |
| [wrap](.claude/skills/wrap/) | 1.0.0 | End-of-session coordinator: sync docs, audit CLAUDE.md, then handoff |

These skills implement a **session continuity workflow**:

1. **During work**: `syncing-docs` keeps documentation in sync with code changes
2. **End of session**: `wrap` chains sync-docs → [claude-md-improver](https://github.com/anthropics/skills) (Anthropic plugin) → handoff
3. **Handoff**: Creates a HANDOFF.md snapshot so a new session can resume with "Read HANDOFF.md and continue"

The key idea: Claude Code sessions are ephemeral, but project context shouldn't be. These skills bridge that gap by maintaining CLAUDE.md, TODO.md, HANDOFF.md, and `.doc-manifest.yaml` as persistent state files.

### Research

| Skill | Version | Description |
|-------|---------|-------------|
| [study](.claude/skills/study/) | 1.0.0 | Structured web research with source verification and hypothesis tracking |

Standalone skill. No dependencies on other skills in this collection.

## Why These Exist

Claude Code is powerful but sessions are stateless — context is lost on `/clear` or crash. After enough sessions where I had to re-explain project state, I built these skills to solve three problems:

1. **Session amnesia**: `handoff` captures what was done, what failed, and what's next. A new session reads HANDOFF.md and picks up where the last one left off.
2. **Documentation drift**: `syncing-docs` detects when code changes make docs stale and fixes them automatically. No more outdated README sections or wrong file paths in CLAUDE.md.
3. **Skill quality**: The meta-tooling skills (`creating-skills`, `updating-skills`, `auditing-skills`) enforce consistency so skills don't degrade over time.

## Installation

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

- **Don't want `.doc-manifest.yaml`?** Remove `managing-doc-manifest` and the manifest step from `syncing-docs`
- **Don't use HANDOFF.md?** Use `syncing-docs` standalone without `wrap` or `handoff`
- **Want different HANDOFF.md format?** Edit `handoff/templates.md`
- **Want different audit rules?** Edit `auditing-skills/checklist.md`

## Related

- [forging-workflow](https://github.com/gradigit/forging-workflow) — Companion repo for turning rough ideas into implementation-ready prompts and plans
- [Anthropic Skills](https://github.com/anthropics/skills) — Official skills from Anthropic
- [Agent Skills Spec](https://agentskills.io) — The open standard these skills follow
- [Claude Code Docs: Skills](https://code.claude.com/docs/en/skills) — Official documentation

## License

MIT — see [LICENSE](LICENSE).
