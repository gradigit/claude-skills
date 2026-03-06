# Agents

Agent-facing project context. Shared across Claude Code and Codex CLI for cross-agent continuity.

## Forge Skills (Autonomous Workflows)

### Skills

| Skill | Layer | Purpose |
|-------|-------|---------|
| [forge-claude-teams](.claude/skills/forge-claude-teams/) | 0 (practices) | Claude Code best practices for Agent tool, TeamCreate, SendMessage, task coordination |
| [forge-codex-multiagent](.claude/skills/forge-codex-multiagent/) | 0 (practices) | Codex CLI best practices for spawn_agent, fork_context, batch processing |
| [forge-research](.claude/skills/forge-research/) | 1 (capability) | Autonomous multi-agent research with hypothesis tracking and adversarial challenge |
| [forge-builder](.claude/skills/forge-builder/) | 1 (capability) | Autonomous building/coding with self-review, self-improvement, and quality gates |
| [forge-orchestrator](.claude/skills/forge-orchestrator/) | 2 (orchestrator) | Sequences Layer 1 skills through milestone-gated cycles with review and compound learning |

### Custom Agents

| Agent | Purpose | Tools |
|-------|---------|-------|
| [forge-adversarial-reviewer](.claude/agents/forge-adversarial-reviewer.md) | Critical review with confidence-gated findings (>80%) | Read, Grep, Glob, Bash |
| [forge-build-worker](.claude/agents/forge-build-worker.md) | Implementation worker with file-scope ownership | Read, Write, Edit, Bash, Grep, Glob |
| [forge-research-worker](.claude/agents/forge-research-worker.md) | Web research and codebase exploration (read-only, Rule of Two) | Read, Grep, Glob, Bash, WebSearch, WebFetch |
| [forge-performance-auditor](.claude/agents/forge-performance-auditor.md) | Metric-driven performance auditing | Read, Bash, Grep, Glob |

### Codex CLI Agent Roles

The same 4 agents are available as Codex custom roles via `[agents.<name>]` in `config.toml`:

| Role | Config File | Sandbox |
|------|-------------|---------|
| `forge-adversarial-reviewer` | `.codex/agents/forge-adversarial-reviewer.toml` | read-only |
| `forge-build-worker` | `.codex/agents/forge-build-worker.toml` | full-access |
| `forge-research-worker` | `.codex/agents/forge-research-worker.toml` | read-only |
| `forge-performance-auditor` | `.codex/agents/forge-performance-auditor.toml` | read-only |

Enable with `multi_agent = true` in `[features]`. See forge-codex-multiagent SKILL.md Section 1b for config syntax.

### Cross-References

- forge-research and forge-builder read the platform practices guide on startup: **forge-claude-teams** (Claude Code) or **forge-codex-multiagent** (Codex CLI)
- forge-orchestrator invokes forge-research for unknowns and forge-builder for implementation
- forge-orchestrator spawns all 4 custom agents for review, building, research, and performance auditing

### Dependency Graph

```
forge-orchestrator (Layer 2)
  ├── READS: forge-claude-teams OR forge-codex-multiagent (Layer 0)
  ├── INVOKES: forge-research (Layer 1)
  ├── INVOKES: forge-builder (Layer 1)
  └── SPAWNS: forge-adversarial-reviewer, forge-build-worker,
              forge-research-worker, forge-performance-auditor

forge-research (Layer 1)
  ├── READS: forge-claude-teams OR forge-codex-multiagent (Layer 0)
  └── SPAWNS: forge-adversarial-reviewer (optional)

forge-builder (Layer 1)
  ├── READS: forge-claude-teams OR forge-codex-multiagent (Layer 0)
  ├── SPAWNS: forge-build-worker (optional)
  └── SPAWNS: forge-adversarial-reviewer (optional)
```

## Existing Skills

See [README.md](README.md) for the full skill catalog and installation instructions.
