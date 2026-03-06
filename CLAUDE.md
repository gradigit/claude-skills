# Forge Skills Suite

5 new skills + 4 custom agents for autonomous, long-running agent workflows with self-review, self-improvement, and multi-agent coordination. Added to the existing claude-skills repo (gradigit/claude-skills).

## Build Commands

No build step — skills are Markdown files (SKILL.md) with YAML frontmatter. Validation uses the auditing-skills skill:
```bash
# Audit a skill for spec compliance
claude -p "audit the skill at .claude/skills/forge-orchestrator/"

# Run skill evaluations
claude -p "test the skill at .claude/skills/forge-research/"
```

## Project Structure

```
.claude/
  skills/                          # Existing skills (9) + new forge skills (5)
    forge-claude-teams/            # Layer 0 — Claude Code multi-agent practices
    forge-codex-multiagent/        # Layer 0 — Codex CLI multi-agent practices
    forge-research/                # Layer 1 — Autonomous multi-agent research
    forge-builder/                 # Layer 1 — Autonomous building with self-review
    forge-orchestrator/            # Layer 2 — Master orchestrator
      agents/                      # Custom agent definitions (copied to .claude/agents/ on install)
  agents/                          # Custom agent definitions (installed location)
    forge-adversarial-reviewer.md  # Read-only critical reviewer
    forge-build-worker.md          # Implementation worker (worktree isolation)
    forge-research-worker.md       # Web research + codebase exploration
    forge-performance-auditor.md   # Benchmarking and profiling
  commands/                        # Slash command entry points
architect/                         # Planning artifacts (this project)
  prompt.md                        # Perfected specification (reference only during execution)
  transcript.md                    # Q&A log from planning (reference only)
  STATE.md                         # Planning skill state (ignore during execution)
  plan.md                          # Implementation plan (THE execution instructions — created in Mode 2)
```

## Conventions

- Skills follow the Agent Skills spec (agentskills.io) — SKILL.md with YAML frontmatter
- Layered architecture: Layer 0 (practices) → Layer 1 (capabilities) → Layer 2 (orchestrator)
- Custom agents use `.claude/agents/*.md` with YAML frontmatter (`model: inherit` always)
- Implementation order: Layer 0 first, then Layer 1, then custom agents, then Layer 2
- All prompt surfaces use XML tags for structure, Markdown for content, YAML for metadata
- Sub-agent prompts follow the 7-tag XML template (objective, context, output-format, tools, boundaries, quality-bar, task)
- Reviewers use confidence gating (>80% threshold + file:line evidence)
- Builders use end-state descriptions (not step-by-step) and temperature 0.0
- Skills are user-invocable with explicit cross-references (not relying on auto-inject alone)
- Each skill gets EVALUATIONS.md with triggering + functional + performance tests
- Version bump + CHANGELOG.md update on every skill change

## architect/ Directory

**Read `architect/plan.md` for implementation instructions.** This is the execution plan — follow it phase by phase.

The other files in architect/ are pre-planning artifacts. Do not treat them as instructions:
- `prompt.md` — the original specification used to generate the plan. Reference only. The plan supersedes it.
- `transcript.md` — Q&A log from the planning process. Reference only. Useful if you need to understand why a decision was made.
- `STATE.md` — planning skill state. Ignore during execution.

## Compact Instructions
<!-- Read by the compaction summarizer itself. Guides WHAT to preserve. -->
When compacting, preserve:
- The current forge pipeline stage and substep
- All file paths from the last 10 tool calls
- All test results and their pass/fail status
- Any error messages being actively debugged
- The exact milestone name and number from FORGE-STATUS.md

## Forge Pipeline State
<!-- Read by the agent after compaction. Guides WHAT TO DO. -->
After any context compaction, re-read these files immediately:
1. FORGE-HANDOFF.md — what you were doing when compaction occurred
2. FORGE-STATUS.md — current milestone and phase
3. TODO.md — task checklist with completion status
4. FORGE-MEMORY.md — cross-session learnings

Then continue from the point described in FORGE-HANDOFF.md "What's In Progress".

## Current Phase
Phase: Complete
All 5 milestones finished. 5 skills + 4 custom agents built.

## Phase Progress
- [x] Intake: state files created, git-ignore updated, CLAUDE.md sections added
- [x] M1: Layer 0 Skills (forge-claude-teams: 437 lines, forge-codex-multiagent: 425 lines)
- [x] M2: Layer 1 Skills (forge-research: 379 lines, forge-builder: 276 lines)
- [x] M3: Custom Agents (4 agents, ~100 lines each)
- [x] M4: Layer 2 Orchestrator (forge-orchestrator: 303 lines + 6 reference files)
- [x] M5: Integration (README, AGENTS.md, /forge + /forge-research + /forge-builder commands, agent install, symlinks)
