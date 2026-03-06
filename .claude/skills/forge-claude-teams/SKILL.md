---
name: forge-claude-teams
description: "Codifies best practices for Claude Code multi-agent features: Agent tool, TeamCreate, SendMessage, task coordination. Reference guide for building effective agent teams with conflict prevention, error recovery, and progress observability. Do NOT use when working with Codex CLI — use forge-codex-multiagent instead."
license: MIT
metadata:
  version: "1.1.0"
  author: gradigit
  category: forge
  tags:
    - claude
    - teams
    - agents
    - multi-agent
    - best-practices
  triggers:
    - "claude teams"
    - "multi-agent"
    - "agent teams"
    - "teamcreate"
  user-invocable: true
---

# Forge Claude Teams

Best practices for Claude Code's multi-agent features. Reference guide — read sections as needed, not sequentially.

## Agent Tool (Subagents)

### When to Use Subagents vs Teams

| Use Case | Mechanism | Why |
|----------|-----------|-----|
| Independent task, clear input/output | Agent tool (subagent) | No shared state needed, fire-and-collect |
| Coordinated multi-step work | TeamCreate + teammates | Shared task list, message passing, lifecycle |
| Quick read-only lookup | Agent tool (Explore type) | Lightweight, no tool overhead |
| Parallel builds with merging | Team with worktree isolation | Conflict prevention requires coordination |

### Subagent Type Selection

Match `subagent_type` to the tools the agent needs. Wrong type = silent failures.

| `subagent_type` | Tools Available | Use For |
|-----------------|-----------------|---------|
| `"general-purpose"` | All (Read, Write, Edit, Bash, Grep, Glob) | Implementation, fixes, file creation |
| Explore | Read-only (Read, Grep, Glob, WebSearch) | Research, codebase exploration, analysis |
| Plan | Read-only + planning focus | Architecture decisions, approach design |
| Custom (`.claude/agents/`) | Per agent definition | Specialized workers with tool restrictions |

**Rule**: Never assign implementation work to read-only agent types. An Explore agent that needs to edit a file will silently skip the edit.

### Model Selection

| Scenario | Model | Rationale |
|----------|-------|-----------|
| All worker agents | `inherit` (default) | Consistency, no degradation |
| Explore subagents | Platform default (acceptable) | Read-only, lower stakes |
| Build workers | `inherit` always | Quality-critical, must match lead |

Never specify `model: "haiku"` or `model: "sonnet"` for workers. Let them inherit.

### Context Handoff Template

Every sub-agent prompt must include these 5 components:

```xml
<task>
  Implement the authentication middleware for Express routes.
  Handle JWT validation, token refresh, and role-based access.
</task>

<context>
  Project uses Express 4 + TypeScript. Auth tokens are JWTs signed
  with RS256. Existing user model is in src/models/user.ts.
  Decision: we chose Passport.js over custom middleware (see ADR-003).
</context>

<scope>
FILE SCOPE:
  own: [src/middleware/auth.ts, src/middleware/roles.ts]
  read: [src/models/user.ts, src/config/auth.ts]
  deny: [src/routes/*, src/models/*]
</scope>

<boundaries>
  Do NOT modify routes, models, or config files.
  Another agent owns src/routes/ — do not touch.
</boundaries>

<output-contract>
  Files: src/middleware/auth.ts, src/middleware/roles.ts
  Tests: src/middleware/__tests__/auth.test.ts
  Signal: "AUTH_MIDDLEWARE_COMPLETE" when done
</output-contract>
```

> **For orchestrator-level sub-agents**: The forge pipeline uses a 7-tag XML template (objective, context, output-format, tools, boundaries, quality-bar, task) for sub-agent spawn prompts. Sub-agent `<boundaries>` include a structured FILE SCOPE block (own/read/deny) for machine-parseable scope declarations. See [sub-agent-template.md](../forge-orchestrator/sub-agent-template.md) for the full template and role-specific contracts.

### Parallelism Model

**Parallelized serial threads** — not pure fan-out.

```
Orchestrator
  ├── Thread A (auth module): research → implement → test → fix (serial)
  ├── Thread B (API routes):  research → implement → test → fix (serial)
  └── Thread C (database):    research → implement → test → fix (serial)
       ↑ parallel across threads, serial within each thread
```

Each thread owns a coherent work chunk and accumulates context as it progresses. Threads can spawn sub-agents for research/review within their scope.

**Concurrency limits** (Gunther's USL — coordination overhead scales N^2):

| Agent Type | Max Parallel | Rationale |
|------------|-------------|-----------|
| Build workers | 2-3 | File conflicts, merge complexity |
| Read-only reviewers | 3 per batch | Rate limits; batch as 3+2 |
| Research queries | 3-5 per thread | Independent, no conflict risk |

### Background vs Foreground

| Mode | When | Example |
|------|------|---------|
| Foreground | Results needed before next step | Code review before merge |
| Background | Independent, non-blocking work | Running test suite while building |

**Never poll** background agents. Wait for the notification callback. Polling wastes tokens and can race.

---

## Teams (TeamCreate / SendMessage / TaskList)

### Full Lifecycle

```
1. TeamCreate          → creates team + shared task list
2. TaskCreate (×N)     → define all work items upfront
3. Agent tool (×N)     → spawn teammates (they join the team)
4. TaskUpdate          → assign tasks via `owner` parameter
5. [teammates work]    → claim tasks, implement, coordinate
6. SendMessage         → DMs for coordination, never broadcast routine
7. shutdown_request    → graceful shutdown per teammate
8. TeamDelete          → cleanup after all teammates confirmed shutdown
```

### Task Ownership

```python
# Assign a task to a teammate
TaskUpdate(taskId="3", owner="auth-builder")

# Teammates claim unassigned tasks in ID order
# (lowest ID first — earlier tasks set up context for later ones)
TaskUpdate(taskId="4", owner="my-name", status="in_progress")
```

**Rules**:
- Assign via `TaskUpdate` with `owner`, not via messages
- Teammates should check `TaskList` after completing each task
- Prefer ID order when multiple tasks are available
- Set `status: "in_progress"` when starting, `"completed"` when done

### Communication

| `type` | Use For | Cost |
|--------|---------|------|
| `"message"` | DMs to specific teammate (default) | 1 message |
| `"broadcast"` | Critical announcements only | N messages (1 per teammate) |
| `"shutdown_request"` | Graceful termination | 1 message |
| `"plan_approval_response"` | Approve/reject teammate plans | 1 message |

**Never broadcast routine status.** If only one teammate needs the info, use `"message"`.

```python
# Good — targeted DM
SendMessage(type="message", recipient="auth-builder",
            content="Auth module ready for review",
            summary="Auth ready for review")

# Bad — broadcasting routine status
SendMessage(type="broadcast",
            content="I finished the auth module")  # Don't do this
```

### Idle Handling

Teammates go idle after every turn. This is **normal and expected**.

| Observation | Meaning | Action |
|-------------|---------|--------|
| Teammate went idle | Turn ended, waiting for input | Send message to wake if needed |
| Teammate idle after sending message | Sent message, waiting for response | Normal — respond when ready |
| Teammate idle for extended period | No work assigned or blocked | Check TaskList, assign work |

**Idle does NOT equal done.** Send a message to wake an idle teammate.

### Plan Mode

Spawn a teammate in plan mode when you want to approve their approach:

```python
# Spawn with plan mode
Agent(name="architect", mode="plan", team_name="my-team", ...)

# When they submit a plan, approve or reject:
SendMessage(type="plan_approval_response", request_id="abc-123",
            recipient="architect", approve=True)

# Or reject with feedback:
SendMessage(type="plan_approval_response", request_id="abc-123",
            recipient="architect", approve=False,
            content="Add error handling for the API calls")
```

### Shutdown Protocol

```python
# 1. Request shutdown for each teammate
SendMessage(type="shutdown_request", recipient="auth-builder",
            content="All tasks complete, wrapping up")

# 2. Teammate responds (automatically via shutdown_response)
# 3. Wait for all approvals
# 4. Only then clean up
TeamDelete()  # Fails if active members remain
```

**Never call TeamDelete before all teammates have confirmed shutdown.**

---

## Conflict Prevention

### Conflict Prevention Pyramid

```
                ┌─────────────────────┐
                │  SAME FILE builds   │  ← DO NOT. Redesign or queue.
                │  (never parallel)   │
                ├─────────────────────┤
                │  DIFFERENT FILE     │  ← Worktrees + ownership scoping
                │  builds (parallel)  │
                ├─────────────────────┤
                │  Read-only / research│  ← Shared tree, safe by default
                │  (always parallel)  │
                └─────────────────────┘
```

### Decision Table

| Agents Doing | Isolation | Setup |
|-------------|-----------|-------|
| Research / read-only | None needed | Shared working tree |
| Build on **different** files | Worktree per agent | `isolation: "worktree"` or `EnterWorktree` + file ownership. Use Clash hook for real-time conflict detection if available |
| Build on **same** file | **DO NOT** | Redesign decomposition or queue sequentially |

### Worktree Setup

**Primary**: Pass `isolation: "worktree"` in the Agent tool call to run the sub-agent in an isolated git worktree automatically:

```python
Agent(name="auth-builder", subagent_type="general-purpose",
      isolation="worktree", prompt="...")
```

**Fallback**: If `isolation: "worktree"` is not supported, instruct the sub-agent to call `EnterWorktree` as its first action:

```xml
<boundaries>
  Run in an isolated worktree. Call EnterWorktree as your first action.
  FILE SCOPE:
    own: [src/middleware/auth.ts, src/middleware/roles.ts]
    read: [src/models/user.ts, src/config/auth.ts]
    deny: [src/routes/*]
</boundaries>
```

After validation, the orchestrator merges worktree branches sequentially.

> **Codex CLI note**: No worktree equivalent exists in Codex. Rely on file ownership scoping + sequential execution for build isolation. See forge-codex-multiagent for Codex-specific conflict prevention.

### File Ownership Enforcement

Declare ownership in every agent's context handoff. The agent MUST NOT modify files outside its declared scope.

```
Agent A:
  own: [src/auth/*, src/middleware/auth.*]
  read: [src/config/*, src/types/*]
  deny: [src/routes/*, src/models/*]

Agent B:
  own: [src/routes/*, src/controllers/*]
  read: [src/config/*, src/types/*]
  deny: [src/auth/*, src/models/*]

Agent C:
  own: [src/models/*, src/db/*]
  read: [src/config/*, src/types/*]
  deny: [src/auth/*, src/routes/*]
```

This format is machine-parseable. The forge-orchestrator writes it to `.claude/forge-scopes.json` for automated scope validation via the forge-scope-guard hook.

If two agents need to modify the same file, the decomposition is wrong. Refactor the task split.

---

## Error Recovery

### Agent Failure

When a sub-agent crashes, overflows context, or produces garbage:

```xml
<task>
  [Original task description — copied verbatim]
</task>

<context>
  Previous agent failed with: "Context window exceeded while processing
  auth middleware tests. Last successful output: auth.ts created,
  roles.ts created, tests not started."
  Start fresh. Do not attempt to recover previous agent state.
</context>
```

**Rules**:
- Spawn a **fresh** agent with the same context handoff + failure note
- Never retry the crashed agent instance
- Include what the previous agent accomplished (if anything)
- Include the failure reason so the new agent can avoid the same path

### Merge Conflicts

If sequential merge of worktree branches produces conflicts:

1. **Stop immediately** — do not auto-resolve
2. Present conflicts to the user with full diff context
3. Wait for user resolution before continuing

Cross-agent merge conflicts are architectural issues. Auto-resolution risks silent data loss.

### Quality Gate Failures

```
Gate fails → re-run agent with feedback → max 2 retries → escalate
```

| Attempt | Action |
|---------|--------|
| 1st failure | Re-run with gate feedback appended to context |
| 2nd failure | Re-run with both failure contexts |
| 3rd failure | **Escalate to user** — the task decomposition may be wrong |

---

## Progress Observability

### TODO.md Updates

Update `TODO.md` after every significant step:
- Completing a file
- Passing or failing a test
- Hitting an error or blocker
- Finishing a milestone

### FORGE-STATUS.md (Orchestrator Only)

For long-running orchestrations, the orchestrator (and only the orchestrator) maintains:

```markdown
# Forge Status

## Current Milestone
M2: Core Implementation (3 of 5 tasks complete)

## Active Agents
- auth-builder: implementing JWT refresh (worktree: wt-auth)
- api-researcher: exploring rate limiting approaches

## Completed
- [x] Project scaffold
- [x] Database schema
- [x] User model

## Pending
- [ ] Auth middleware (in progress)
- [ ] API routes
- [ ] Integration tests

## Blockers
- None currently
```

**Sub-agents do NOT write to FORGE-STATUS.md.** They report status to the orchestrator via SendMessage; the orchestrator updates the file.

### Progress Narration

Before each significant action batch, emit a brief progress note:

```
→ About to spawn 3 build workers for auth, routes, and models.
  Each gets worktree isolation. Expected completion: ~5 minutes.
```

**Never run silently for 5+ minutes.** If a cycle produces no observable output, write a progress note explaining what is happening and why.

---

## Quick Reference: Tool Cheat Sheet

| Action | Tool | Key Parameters |
|--------|------|----------------|
| Spawn sub-agent | `Agent` | `name`, `subagent_type`, `team_name`, `mode` |
| Create team | `TeamCreate` | `team_name`, `description` |
| Create task | `TaskCreate` | `subject`, `description`, `activeForm` |
| Assign task | `TaskUpdate` | `taskId`, `owner` |
| Send DM | `SendMessage` | `type: "message"`, `recipient`, `content`, `summary` |
| Broadcast | `SendMessage` | `type: "broadcast"`, `content`, `summary` |
| Shutdown agent | `SendMessage` | `type: "shutdown_request"`, `recipient` |
| Delete team | `TeamDelete` | (no params — uses current team) |
| List tasks | `TaskList` | (no params) |
| Enter worktree | `EnterWorktree` | `name` (optional) |

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Do Instead |
|-------------|-------------|------------|
| Broadcasting routine status | N messages, wastes tokens | DM the relevant teammate |
| Polling background agents | Races, wastes tokens | Wait for notification |
| Same-file parallel builds | Merge conflicts guaranteed | Redesign split or queue |
| `model: "haiku"` for workers | Quality degradation | Inherit main model |
| Implementation on Explore agent | Edits silently skipped | Use general-purpose type |
| Auto-resolving merge conflicts | Silent data loss | Stop and present to user |
| Retrying crashed agents | Corrupted state carries over | Spawn fresh agent |
| Force-killing teammates | Orphaned state | Use shutdown_request |
| No file ownership declared | Agents step on each other | Declare scope in handoff |
| Running silent 5+ minutes | User thinks agent is stuck | Emit progress narration |

---

## Self-Evolution

Update this skill when:
1. **Claude Code API changes**: New Agent tool parameters, TeamCreate options, or SendMessage types
2. **New anti-pattern discovered**: Add to anti-patterns table with fix
3. **Concurrency limits change**: Update parallelism table if rate limits or platform caps change
4. **New isolation mechanism**: If Claude Code adds native worktree parameters to Agent tool, update conflict prevention

Current version: 1.0.0. See [CHANGELOG.md](CHANGELOG.md) for history.
