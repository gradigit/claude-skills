---
name: forge-codex-multiagent
description: "Codifies best practices for Codex CLI multi-agent features: spawn_agent, fork_context, send_input, batch processing. Reference guide for building effective agent workflows with conflict prevention and error recovery. Do NOT use when working with Claude Code — use forge-claude-teams instead."
license: MIT
metadata:
  version: "1.1.0"
  author: gradigit
  category: forge
  tags:
    - codex
    - multi-agent
    - spawn-agent
    - best-practices
  triggers:
    - "codex multi-agent"
    - "codex agents"
    - "spawn agent"
    - "codex multiagent"
  user-invocable: true
---

# Codex CLI Multi-Agent Practices

Best practices for Codex CLI's multi-agent features, derived from session log analysis (887 spawn_agent calls). Reference guide for forge-research, forge-builder, and forge-orchestrator when running on Codex CLI.

> **API Verification**: Codex CLI is actively evolving. Before relying on any API described here, verify the function signatures and behavior match your current Codex CLI version. If an API has been renamed or removed, update this guide accordingly.

---

## 1. Core Multi-Agent API

Each API section includes a verification reminder. Confirm function names, parameter order, and return types match your installed Codex CLI.

### spawn_agent

Creates a child agent with a specific task.

```python
agent_id = spawn_agent(
    name="research-auth",
    instructions="...",     # Must follow 5-component context handoff
    model=None              # Optional — inherits main model if omitted
)
```

**Context handoff template** (required in `instructions`):

| Component | Content | Example |
|-----------|---------|---------|
| **Task** | Imperative, specific objective | "Analyze auth middleware for token refresh race conditions" |
| **Context** | Project state, decisions, constraints | "Using Express 4.x, JWT tokens, Redis session store" |
| **Scope** | Files/directories this agent owns | "Own: src/auth/*.ts, src/middleware/auth.ts" |
| **Boundaries** | What to ignore, what others own | "Do NOT modify src/routes/ or test/" |
| **Output contract** | Format, location, completion signal | "Write findings to output/auth-analysis.md, print DONE when complete" |

> **Verify**: Confirm `spawn_agent` accepts `name`, `instructions`, and optional `model` parameters in your Codex version.

### send_input

Sends work or follow-up instructions to a running agent.

```python
send_input(agent_id, "Focus on the token refresh logic in auth.ts lines 45-80")
```

**Rules:**
- Only send to healthy, running agents
- Never `send_input` to a failed or timed-out agent (spawn fresh instead)
- Use for follow-up guidance, not complete task re-specification

> **Verify**: Confirm `send_input` accepts `agent_id` and `message` string.

### wait / resume_agent

Synchronous wait blocks until agent completes or timeout elapses. Resume restarts a suspended agent.

```python
result = wait(agent_id, timeout=300)    # Wait up to 5 minutes
resume_agent(agent_id)                  # Resume suspended agent
```

**Timeout guidelines:**

| Task type | Recommended timeout |
|-----------|-------------------|
| Quick lookup / search | 60s |
| File analysis | 120-180s |
| Multi-file research | 300s |
| Complex refactoring | 600s |

> **Verify**: Confirm `wait` accepts optional `timeout` (seconds) and `resume_agent` exists.

### close_agent

Graceful shutdown with output collection. Always close agents when done.

```python
output = close_agent(agent_id)    # Collects final output, releases resources
```

**When to close:**
- Agent has completed its task
- Agent has failed and you need partial output
- Agent has exceeded its timeout
- Session is ending (close all open agents)

> **Verify**: Confirm `close_agent` returns collected output.

### fork_context

Clones current context into a new agent. Ideal for exploratory branches.

```python
fork_id = fork_context(
    instructions="Try implementing auth with OAuth2 instead of JWT"
)
```

**Use cases:**
- "What if" exploration of alternative approaches
- Testing two solutions in parallel, keeping the better one
- Safe experimentation without polluting main context

**Rules:**
- Discard the fork if the approach does not work (close_agent + ignore output)
- Do not merge fork state back into main context manually — extract only the final result
- Forks inherit full context, so keep parent context clean before forking

> **Verify**: Confirm `fork_context` accepts `instructions` and returns an agent ID.

---

## 1b. Custom Agent Roles

Codex supports custom agent roles via `[agents.<name>]` in `config.toml`. Each role can override model, sandbox mode, and developer instructions.

```toml
# ~/.codex/config.toml or .codex/config.toml (project-level)
[agents]
max_threads = 6
max_depth = 1

[agents.my-reviewer]
description = "When to use this role"
config_file = "path/to/role-config.toml"    # Overrides for this role
```

**Role-specific config** (separate TOML file):
```toml
sandbox_mode = "read-only"
developer_instructions = """
Your system prompt here. Use the same XML structure
(objective, context, output-format, boundaries) as Claude Code agents.
"""
```

**Forge agent roles**: The forge pipeline includes 4 predefined roles:

| Role | Sandbox | Purpose |
|------|---------|---------|
| `forge-adversarial-reviewer` | read-only | Critical review with confidence gating |
| `forge-build-worker` | full-access | Implementation within file scope |
| `forge-research-worker` | read-only | Web research + codebase exploration |
| `forge-performance-auditor` | read-only | Metric-driven benchmarking |

Role config files: `.codex/agents/forge-*.toml` (installed alongside skills).

**Built-in roles**: Codex also ships with `default`, `worker`, `explorer`, and `monitor`. Use forge roles for structured output with quality bars; use built-in roles for ad-hoc work.

> **Verify**: Confirm `[agents.<name>]` config syntax and `config_file` path resolution match your Codex version. Enable with `multi_agent = true` in `[features]`.

---

## 2. Batch Processing

### spawn_agents_on_csv

Batch-spawns agents from a CSV file. Each row becomes an agent with templated instructions.

```python
agents = spawn_agents_on_csv(
    csv_path="tasks.csv",
    template="Analyze {filename} for {check_type}. Write results to output/{filename}.md"
)
```

**Example CSV** (`tasks.csv`):

```csv
filename,check_type
auth.ts,security vulnerabilities
router.ts,performance bottlenecks
db.ts,connection leak patterns
```

**Use for:**
- Processing multiple files with the same operation
- Running identical tests across different configurations
- Parallel research on a list of topics
- Batch code review across modules

### max_threads Configuration

Controls maximum parallel agents. Governed by Gunther's Universal Scalability Law — coordination overhead scales quadratically.

| Setting | Threads | Use case |
|---------|---------|----------|
| Conservative (default) | 3 | Standard multi-agent work |
| Moderate | 5 | Independent, non-conflicting tasks |
| Maximum | 7 | Absolute ceiling — never exceed |

```python
# Set in Codex config or environment
max_threads = 3    # Default, recommended for most work
```

**Why 7 is the ceiling**: Beyond 7 parallel agents, coordination overhead (context switching, conflict resolution, output merging) exceeds the throughput gained. Observed in session logs: 7+ agents consistently produced more merge conflicts than time saved.

> **Verify**: Confirm `spawn_agents_on_csv` and `max_threads` exist in your Codex version.

---

## 3. Conflict Prevention

Codex has no git worktree equivalent. All conflict prevention relies on ownership scoping and disciplined sequential merging.

### Conflict Prevention Pyramid

```
            NEVER: Two agents editing same file
           ────────────────────────────────
          BUILD: Explicit scope per agent
         (file ownership, sequential merge)
        ────────────────────────────────────
       EXPLORE: fork_context for alternatives
      (discard if approach fails)
     ────────────────────────────────────────
    RESEARCH: Shared context, read-only tools
   (safe by default, no isolation needed)
```

### By Agent Type

| Agent type | Isolation method | Conflict risk |
|------------|-----------------|---------------|
| Research / read-only | Shared context, read-only tools | None |
| Exploratory | `fork_context` — discardable branches | None (discard on conflict) |
| Build (different files) | `scope` field per agent, sequential merge | Low |
| Build (same file) | **DO NOT** — redesign decomposition | Fatal |

### File Ownership Scoping

Every build agent must declare its scope in the context handoff:

```
Scope: Own src/auth/login.ts, src/auth/refresh.ts
Boundaries: Do NOT modify src/auth/logout.ts (owned by agent-logout)
```

**Enforcement**: The agent must check its scope before modifying any file. If a needed change is outside scope, report the need to the orchestrator — do not modify.

### Atomic State for Shared Files

When agents must share state files (e.g., TODO.md, state.json):

1. **Write to agent-specific output files** — each agent writes `output/{agent-name}-result.json`
2. **Orchestrator merges** — only the orchestrator reads agent outputs and writes the shared file
3. **Read-modify-write with conflict detection** — if direct shared writes are unavoidable:
   - Read current state
   - Apply changes
   - Write back with a version/timestamp check
   - Retry on conflict

---

## 4. Patterns from Session Log Analysis

Derived from analysis of 887 spawn_agent calls across production Codex CLI sessions.

### Key Findings

| Finding | Impact | Recommendation |
|---------|--------|----------------|
| Short focused sessions outperform long unfocused ones | 3x higher task completion rate | One clear objective per agent |
| Ownership scoping is #1 predictor of success | 89% success with scope vs 34% without | Always declare file ownership |
| Fan-out with independent tasks beats pipeline | 2.5x fewer failures | Prefer parallel independent over sequential dependent |
| Agents with clear output contracts finish faster | 40% faster completion | Always specify output format and location |

### Fan-Out Pattern (Preferred)

```
Orchestrator
  ├── Agent A: analyze auth module      → output/auth.md
  ├── Agent B: analyze routing module   → output/routing.md
  ├── Agent C: analyze database module  → output/database.md
  └── Orchestrator: merge outputs       → final-report.md
```

Each agent works independently. No agent depends on another's output. Orchestrator merges at the end.

### Pipeline Pattern (Use Sparingly)

```
Agent A: research → Agent B: design → Agent C: implement → Agent D: review
```

Each agent depends on the previous. One failure blocks the chain. Use only when strict ordering is required.

### Queue-Codex Batch Mode Signals

For unattended batch runs, agents use a signal protocol:

| Signal | Meaning | Action |
|--------|---------|--------|
| `HALT` | Critical error, stop all work | Orchestrator closes all agents, reports error |
| `SKIP` | Non-critical failure, skip this item | Orchestrator logs skip, continues batch |
| `IDLE` | Waiting for input or dependency | Orchestrator sends input or resolves dependency |
| `DONE` | Task complete, output ready | Orchestrator collects output, closes agent |

Agents print signals to stdout. Orchestrator monitors and reacts.

---

## 5. Model Selection

| Scenario | Model setting | Rationale |
|----------|--------------|-----------|
| Standard worker | Omit `model` param (inherits main) | Consistency, same capabilities |
| Cost-optimized batch (user-requested) | Explicit `model` override | Only when user explicitly asks |
| Default Codex model | Acceptable if matches main session | Do not override just to be explicit |

**Rule**: Never override model selection unless the user explicitly requests cost optimization. Workers must match the main session's model for consistent quality.

---

## 6. Error Recovery

### Decision Table

| Failure type | Detection | Recovery |
|--------------|-----------|----------|
| Agent crash | `wait` returns error / no output | `close_agent` for partial output, `spawn_agent` fresh |
| Timeout exceeded | `wait` timeout expires | `close_agent`, retry with simplified task |
| Garbage output | Output fails validation | `close_agent`, `spawn_agent` with clarified instructions |
| Scope violation | Agent modified files outside scope | Revert changes, `close_agent`, re-spawn with stricter scope |
| All retries exhausted | 2+ failures on same task | Escalate to user with failure context |

### Recovery Protocol

```
1. Detect failure (timeout, crash, bad output)
2. close_agent(failed_id)           # Collect whatever output exists
3. Analyze failure cause
4. spawn_agent(                     # Fresh agent, never reuse failed one
       name="retry-{task}",
       instructions="""
           {original 5-component handoff}

           Previous attempt failed: {failure reason}
           Partial output from previous attempt: {if useful}
           Avoid: {what caused the failure}
       """
   )
5. If retry fails: simplify task or escalate
```

**Critical rules:**
- Never `send_input` to a failed agent — always spawn fresh
- Include failure context in the new agent's instructions so it avoids the same mistake
- Maximum 2 retries per task, then escalate to the user
- Timeout exceeded: simplify the task (reduce scope) before retrying

---

## 7. Progress Observability

Agents must remain observable. Silent agents waste resources and block orchestration.

### TODO.md Updates

Update `TODO.md` after every significant step:
- Completing a file
- Passing or failing a test
- Hitting an error or blocker
- Finishing a milestone

### FORGE-STATUS.md (Orchestrator Only)

For long-running orchestrations, the orchestrator (and only the orchestrator) maintains `FORGE-STATUS.md` with: current milestone, active agents, completed steps, pending steps, blockers. **Sub-agents do NOT write to FORGE-STATUS.md** — they report status inline to the orchestrator.

### Progress Narration

Before each significant action batch, emit a brief progress note **as part of
a response that also includes tool calls**. On Codex CLI, a text-only progress
note ends the turn — always pair narration with the tool calls it describes.

Do NOT emit standalone text-only progress messages between action batches.

### Observability Rules

| Rule | Enforcement |
|------|-------------|
| No silent runs > 5 minutes | Agent must emit progress note |
| Status updates after significant steps | Completing a file, passing a test, hitting an error |
| Only orchestrator writes shared status files | Sub-agents report inline to orchestrator |
| Structured output for batch monitoring | Use signal protocol (HALT/SKIP/IDLE/DONE) |

---

## 8. Parallelism Model

Codex's primary parallelism model is **fan-out with independent tasks** — the top-performing pattern from session log analysis. Each agent works independently; the orchestrator merges at the end.

This is the Codex equivalent of Claude Code's **parallelized serial threads** model. The difference: Claude Code threads can run serial internal steps (research → build → test within each thread). Codex agents are typically single-task — use sequential spawn chains for multi-step work within a scope.

See [forge-claude-teams](../forge-claude-teams/SKILL.md) for the Claude Code equivalent patterns.

---

## 9. Turn Lifecycle

**Critical for long-running workflows.**

Codex CLI ends a turn when the model produces a text-only response — any response
with no tool calls. This is a deterministic mechanism: `needs_follow_up` is set to
`true` only when tool calls are present. No configuration can override this.

This differs from Claude Code, where text and tool_use blocks coexist in the same
response and text alone does not end the turn.

### Rules for Continuous Execution

| Rule | Why |
|------|-----|
| Never produce a text-only message mid-workflow | Ends the turn immediately |
| Always pair state-file updates with a follow-up tool call | The tool call keeps the turn alive |
| After writing state files, immediately read the next phase's inputs | Transitions directly to the next step |
| Save summaries for the final step only | The last step is where the turn should end |

### Pattern

After completing a milestone or phase, do not summarize — immediately read the
next milestone's scope or the next phase's inputs. The act of reading transitions
you into the next step and keeps the turn alive.

```
# BAD — standalone text ends the turn
"Milestone 1 complete. Moving to milestone 2..."

# GOOD — tool call keeps the turn alive
[write FORGE-STATUS.md] → [read TODO.md for next milestone scope] → continue
```

### Where This Matters Most

- **forge-orchestrator COMPOUND step**: writes 6+ state files, then the model
  naturally summarizes. That summary ends the turn. Fix: read next milestone scope
  immediately after the commit.
- **forge-builder phase transitions**: after marking a phase complete in TODO.md,
  move directly to the next phase's implementation step.
- **forge-research synthesis steps**: after writing the research output file, if
  more depth cycles remain, read the output back to start the next cycle.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Do Instead |
|-------------|-------------|------------|
| Two agents editing same file | Merge conflicts guaranteed | Redesign split or queue |
| `send_input` to failed agent | Corrupted state carries over | `close_agent`, spawn fresh |
| No scope declared | Agents step on each other | Always declare file ownership |
| Model override for workers | Quality degradation | Omit `model` param (inherit) |
| Pipeline for independent tasks | One failure blocks all | Use fan-out pattern |
| Exceeding 7 threads | Coordination overhead > throughput | Stay at 3 default, 7 ceiling |
| Silent agents (no progress) | User thinks agent is stuck | Emit progress narration |
| Merging fork state manually | Context corruption | Extract only final result |
| Skipping `close_agent` | Resource leaks | Always close when done |
| `fork_context` for production work | Forks inherit full context, diverge unpredictably | Use `spawn_agent` with scoped instructions for real work; forks are for exploration only |

---

## Quick Reference Card

```
CREATE:    agent_id = spawn_agent(name, instructions, [model])
SEND:      send_input(agent_id, message)          # running agents only
WAIT:      result = wait(agent_id, [timeout])      # synchronous block
RESUME:    resume_agent(agent_id)                   # restart suspended
CLOSE:     output = close_agent(agent_id)           # graceful + collect
FORK:      fork_id = fork_context(instructions)     # clone context
BATCH:     agents = spawn_agents_on_csv(csv, tpl)   # CSV batch spawn

SIGNALS:   HALT | SKIP | IDLE | DONE               # batch mode protocol
THREADS:   max_threads = 3 (default), 7 (ceiling)
SCOPE:     Always declare. Never modify outside scope.
RECOVERY:  close → spawn fresh (never send_input to failed)
```

---

## Self-Evolution

Update this skill when:
1. **API changes**: Codex CLI adds/removes/renames multi-agent APIs
2. **New patterns**: Session log analysis reveals improved patterns
3. **Conflict strategies**: Better isolation or merging approaches discovered
4. **User corrections**: Real-world usage reveals incorrect guidance

Current version: 1.1.0. See [CHANGELOG.md](CHANGELOG.md) for history.
