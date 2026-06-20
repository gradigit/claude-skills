---
name: forge-codex-multiagent
description: "Codifies best practices for Codex CLI multi-agent features: spawn_agent, fork_context, send_input, batch processing. Reference guide for building effective agent workflows with conflict prevention and error recovery. Do NOT use when working with Claude Code — use forge-claude-teams instead."
license: MIT
metadata:
  version: "1.1.1"
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
    agent_type="worker",    # Built-in (default/worker/explorer/monitor) or a custom role name
    message="...",          # The task — must follow the 5-component context handoff below
    model=None,             # Optional — inherits main model if omitted
    fork_context=False      # Optional — clone current context into the child (see fork_context)
)
```

**Context handoff template** (required in `message`):

| Component | Content | Example |
|-----------|---------|---------|
| **Task** | Imperative, specific objective | "Analyze auth middleware for token refresh race conditions" |
| **Context** | Project state, decisions, constraints | "Using Express 4.x, JWT tokens, Redis session store" |
| **Scope** | Files/directories this agent owns | "Own: src/auth/*.ts, src/middleware/auth.ts" |
| **Boundaries** | What to ignore, what others own | "Do NOT modify src/routes/ or test/" |
| **Output contract** | Format, location, completion signal | "Write findings to output/auth-analysis.md, print DONE when complete" |

> **Verify**: Confirm `spawn_agent` accepts `agent_type`, `message`, and optional `model`/`fork_context` parameters in your Codex version. (The live 0.140.x binary uses these names — older drafts of this guide showed `name=`/`instructions=`, which the tool does not accept.)

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

### wait_agent / resume_agent

Synchronous wait blocks until agent completes or timeout elapses. Resume restarts a suspended agent.

```python
result = wait_agent(agent_id, timeout=300)    # Wait up to 5 minutes
resume_agent(agent_id)                        # Resume suspended agent
```

**Timeout guidelines:**

| Task type | Recommended timeout |
|-----------|-------------------|
| Quick lookup / search | 60s |
| File analysis | 120-180s |
| Multi-file research | 300s |
| Complex refactoring | 600s |

> **Verify**: Confirm `wait_agent` accepts optional `timeout` (seconds) and `resume_agent` exists. (The live binary uses `wait_agent`, not bare `wait`.)

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

Codex loads custom agent roles from **per-file TOMLs** — one file per role at
`~/.codex/agents/<name>.toml` (personal) or `.codex/agents/<name>.toml`
(project-level, installed alongside skills). This is the mechanism the forge
roles ship with and the one that loads reliably.

```toml
# ~/.codex/agents/my-reviewer.toml
name = "my-reviewer"
description = "When to use this role"
sandbox_mode = "read-only"    # read-only | workspace-write | danger-full-access
developer_instructions = """
Your system prompt here. Use the same XML structure
(objective, context, output-format, boundaries) as Claude Code agents.
"""
```

Each role file requires a non-empty `name`; the valid `sandbox_mode` values are
exactly `read-only`, `workspace-write`, and `danger-full-access` (the older
`full-access` value is rejected at load time by current Codex).

Global limits live under a `[agents]` table in `config.toml`:

```toml
# ~/.codex/config.toml or .codex/config.toml (project-level)
[agents]
max_threads = 3    # see max_threads guidance in Section 2
```

> **Legacy/alternate**: Codex also compiles in an inline `[agents.<name>]`
> config.toml form with a `config_file` pointer. Prefer the per-file model
> above — the inline form has known config-loading caveats (roles can fail with
> "unknown agent_type" unless `-c`-injected; see openai/codex#14579, #15250).

**Forge agent roles**: The forge pipeline includes 4 predefined roles:

| Role | Sandbox | Purpose |
|------|---------|---------|
| `forge-adversarial-reviewer` | read-only | Critical review with confidence gating |
| `forge-build-worker` | danger-full-access | Implementation within file scope |
| `forge-research-worker` | read-only | Web research + codebase exploration |
| `forge-performance-auditor` | read-only | Metric-driven benchmarking |

Role config files: `.codex/agents/forge-*.toml` (installed alongside skills).

**Built-in roles**: Codex also ships with `default`, `worker`, `explorer`, and `monitor`. Use forge roles for structured output with quality bars; use built-in roles for ad-hoc work.

> **Known limitation**: In tool-backed sessions, `spawn_agent` may only resolve the built-in `agent_type` values (`default`/`worker`/`explorer`/`monitor`) and not select per-file custom roles by name (openai/codex#15250). Session-log analysis confirms real `spawn_agent` calls used built-in types, never `forge-*` role names. Until this is fixed upstream, treat the forge role TOMLs as developer-instruction templates: their content can be passed via `message`/`base_instructions` even when the role can't be selected by name.

> **Verify**: Confirm per-file `~/.codex/agents/*.toml` role loading (and the legacy `[agents.<name>]` form, if used) match your Codex version, and test whether `spawn_agent` can select a forge role by name. Enable multi-agent with `multi_agent = true` in `[features]`.

### 1c. Codex Role Selection — prompt-templates (workaround for #15250)

Session-log analysis of real forge runs found the forge-* roles were spawned by
name **0 times across 98 Codex runs** (agent_type was always `explorer`/`default`/
`worker`), so the fresh-context review fan-out silently degraded to undifferentiated
explorers. Until by-name selection works on Codex, **select the role by injecting
its prompt-template**, not its name:

- Pick the closest built-in `agent_type` (read-only roles → `explorer`; build role
  → `worker`).
- Prepend the role's **identity + quality bar** to `message` (or pass via
  `base_instructions`). The role TOMLs in `.codex/agents/forge-*.toml` are the
  source of that text — treat them as prompt templates, not selectable names.
- Always inject the **7-tag context handoff template** (Section on Agent Spawning
  in forge-orchestrator) into every spawn — the 7-tag form was used in only ~5% of
  Codex spawns; programmatic injection fixes that.

| Forge role | Codex `agent_type` | Inline this quality bar in `message` |
|------------|--------------------|--------------------------------------|
| forge-adversarial-reviewer | `explorer` | confidence-gated findings (>80%), evidence required, excluded-list for low-confidence |
| forge-research-worker | `explorer` | read-only, cite every source, Rule-of-Two, structured findings |
| forge-performance-auditor | `explorer` | metric-backed only, reproducible commands, baseline/measured/threshold |
| forge-build-worker | `worker` | FILE SCOPE own/read/deny, self-verify against spec, run tests after changes |

> These are **prompt-role** distinctions on Codex, not `agent_type` distinctions.
> On Claude Code the roles ARE selectable by name (use `subagent_type`); keep both
> paths. Re-test by-name selection per Codex version (the Verify note above).

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
| Conservative (forge default) | 3 | Standard multi-agent work |
| Moderate | 5 | Independent, non-conflicting tasks |
| Maximum | 7 | Forge ceiling — coordination overhead dominates beyond this |

```python
# Set in Codex config (~/.codex/config.toml under [agents])
max_threads = 3    # Forge recommendation for most work
```

> **Note**: 3 and 7 are forge recommendations, not Codex limits. Codex's own
> `max_threads` default is 6 with no hard upper cap (real-world configs set it as
> high as 100). The 7 ceiling below is forge guidance based on coordination
> overhead, not a CLI constraint — raise it deliberately for genuinely
> independent fan-out work.

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
| **429 / rate limit** | spawn/wait errors with 429 or "temporarily limiting requests" | **NOT a logical failure** — back off + retry the SAME task (see Rate-Limit Resilience); never re-spawn blind |
| Agent crash | `wait_agent` returns error / no output | `close_agent` for partial output, `spawn_agent` fresh |
| Timeout exceeded | `wait_agent` timeout expires | `close_agent`, retry with simplified task |
| Garbage output | Output fails validation | `close_agent`, `spawn_agent` with clarified instructions |
| Scope violation | Agent modified files outside scope | Revert changes, `close_agent`, re-spawn with stricter scope |
| All retries exhausted | 2+ failures on same task | Escalate to user with failure context |

### Recovery Protocol

```
1. Detect failure (timeout, crash, bad output)
2. close_agent(failed_id)           # Collect whatever output exists
3. Analyze failure cause
4. spawn_agent(                     # Fresh agent, never reuse failed one
       agent_type="worker",
       message="""
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
- **A 429 is NOT a task failure** — do not count it toward the 2-retry budget; back off and resume

### Rate-Limit (429) Resilience

429 / "server is temporarily limiting requests" was the **#1 real Codex failure
mode** in session-log analysis (1,072 occurrences), and ~46% of unique spawns were
**blind re-spawns of an identical task** after a 429 — wasting budget and worsening
the storm. Treat rate limits as a distinct, transient condition:

- **Distinguish** a 429 from a logical failure. A 429 means "retry later", not
  "the task was wrong". Never clarify/simplify the task in response to a 429.
- **Exponential backoff with jitter**: on 429, wait ~base·2^n (e.g. 5s, 10s, 20s,
  40s…) before retrying the *same* spawn; cap the backoff and the attempts.
- **Spawns-per-minute budget**: cap how many spawns you launch per minute (in
  addition to the `max_threads` per-wait ceiling). Sustained volume, not just
  per-batch width, triggers the storm.
- **Pause-and-drain**: on repeated 429s, stop launching new spawns, let in-flight
  agents drain, then resume at a lower rate.
- **Dedup cache**: key completed/in-flight work by a task signature (role + scope +
  message hash). If a 429 interrupts, **resume/await** the existing agent rather
  than spawning a duplicate.

> The orchestrator's own batch ceilings (Section 2 `max_threads`, 1–4 per wait) cap
> width; this section caps *rate over time* and prevents the blind-re-spawn
> amplification.

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
CREATE:    agent_id = spawn_agent(agent_type, message, [model], [fork_context])
SEND:      send_input(agent_id, message)          # running agents only
WAIT:      result = wait_agent(agent_id, [timeout]) # synchronous block
RESUME:    resume_agent(agent_id)                   # restart suspended
CLOSE:     output = close_agent(agent_id)           # graceful + collect
FORK:      fork_id = fork_context(instructions)     # clone context
BATCH:     agents = spawn_agents_on_csv(csv, tpl)   # CSV batch spawn

SIGNALS:   HALT | SKIP | IDLE | DONE               # batch mode protocol
THREADS:   max_threads = 3 (forge default), 7 (forge ceiling)  # Codex default 6, no hard cap
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

Current version: 1.1.1. See [CHANGELOG.md](CHANGELOG.md) for history.
