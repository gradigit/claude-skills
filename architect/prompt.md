# Forge Skills Suite — Implementation Specification

## Overview

Build 5 new skills for the claude-skills repo (gradigit/claude-skills) that enable autonomous, long-running agent workflows with self-review, self-improvement, and multi-agent coordination.

### Skills

| Skill | Layer | Purpose |
|-------|-------|---------|
| forge-claude-teams | 0 (practices) | Claude Code best practices for Agent tool, TeamCreate, SendMessage, task coordination |
| forge-codex-multiagent | 0 (practices) | Codex CLI best practices for spawn_agent, fork_context, batch processing |
| forge-research | 1 (capability) | Pure autonomous multi-agent research with hypothesis tracking and adversarial challenge |
| forge-builder | 1 (capability) | Autonomous building/coding with self-review, self-improvement, and quality gates |
| forge-orchestrator | 2 (orchestrator) | Sequences Layer 1 skills through milestone-gated cycles with review, testing, and brainstorming |

### Architecture: Layered + Hybrid (Skills + Custom Agents)

```
Layer 2: forge-orchestrator (SKILL — sequences Layer 1, references Layer 0)
           │
           ├── Layer 1: forge-research (SKILL — standalone, references Layer 0)
           ├── Layer 1: forge-builder (SKILL — standalone, references Layer 0)
           │
           ├── Custom Agents (.claude/agents/):
           │     forge-adversarial-reviewer (read-only, tool-restricted)
           │     forge-build-worker (full tools, worktree isolation)
           │     forge-research-worker (web tools, context isolation)
           │     forge-performance-auditor (read+bash, background)
           │
Layer 0: forge-claude-teams (SKILL — practices, auto-inject + explicit refs)
Layer 0: forge-codex-multiagent (SKILL — practices, auto-inject + explicit refs)
```

- **Skills** (SKILL.md): orchestration logic, knowledge/practices, workflow definitions. Run inline in the main thread's context.
- **Custom agents** (`.claude/agents/`): execution workers with context isolation, tool restrictions, and optional worktree isolation. Run in separate context windows.
- Layer 0 skills are `user-invocable: true` with explicit `read SKILL.md` references from Layer 1 and Layer 2 skills. This is the ONLY cross-platform reliable injection method (Codex has no auto-inject; Claude auto-inject is a bonus, not primary mechanism).
- Layer 1 skills are standalone — usable independently or orchestrated by Layer 2.
- Layer 2 sequences Layer 1 and adds cross-cutting concerns (milestone gates, brainstorming, documentation, suggestions, compounding).

---

## Skill 1: forge-claude-teams (Layer 0 — Practices)

### Purpose
Codifies best practices for Claude Code's multi-agent features so that any skill referencing this guide can use teams/agents effectively without the user providing instructions about these features.

### Content Areas

**Agent Tool (subagents)**
- When to use subagents vs teams: subagents for independent tasks with clear input/output contracts; teams for coordinated multi-step work with shared state
- Subagent type selection: match `subagent_type` to required tools (Explore = read-only research, general-purpose = full capability, Plan = architecture). Never assign implementation work to read-only agent types
- Model selection: inherit main model always. Never specify `model: "haiku"` or `model: "sonnet"` for worker agents. Only exception: Explore subagent type (platform default, read-only, acceptable for quick searches)
- Context handoff template — every sub-agent prompt must include 5 components:
  1. **Task**: What to do (imperative, specific)
  2. **Context**: Project state, decisions made, constraints
  3. **Scope**: File/directory ownership boundaries
  4. **Boundaries**: What to ignore, what other agents own
  5. **Output contract**: Format, location, completion signal
- Parallelism model: **parallelized serial threads**. Launch parallel threads where each thread runs serial/sequential work internally. Each thread takes ownership of a coherent work chunk, accumulates context as it progresses, and can spawn its own sub-agents for research/review/exploration within its scope. This is NOT pure fan-out parallelism — it's parallel pipelines, each internally sequential. Gunther's USL: coordination overhead scales N². Practical limit: 2-3 parallel build threads, up to 3 parallel read-only review agents per batch (batched 3+2 to avoid rate limits), up to 3-5 parallel independent research queries within a thread
- Background vs foreground: use foreground when results are needed before proceeding; background for genuinely independent work. Never poll background agents — wait for notification

**Teams (TeamCreate/SendMessage/TaskList)**
- Team lifecycle: TeamCreate → TaskCreate tasks → spawn teammates with Agent tool → assign tasks via TaskUpdate → teammates work → SendMessage for coordination → shutdown_request when done → TeamDelete
- Task ownership: assign via TaskUpdate with `owner` parameter. Teammates claim unassigned unblocked tasks in ID order
- Communication: SendMessage with `type: "message"` for DMs (default). `type: "broadcast"` only for critical team-wide announcements. Never broadcast routine status — it sends N separate messages
- Idle handling: teammates go idle after every turn (normal). Idle ≠ done. Send a message to wake idle teammates
- Plan mode for teammates: use `mode: "plan"` parameter when spawning if you want to approve their approach before implementation. Use `plan_approval_response` to approve/reject
- Shutdown protocol: always send `shutdown_request` before TeamDelete. Wait for approval responses. Never force-kill teammates

**Conflict Prevention**
- Conflict prevention pyramid:
  - Research/read-only agents: shared working tree, safe by default. No isolation needed
  - Build agents on DIFFERENT files: git worktrees + ownership scoping. Each agent owns specific files/directories. Use Clash hook for real-time conflict detection if available
  - Build agents on SAME file: DO NOT. Redesign task decomposition to split by file, or queue sequentially
- Worktree setup for Claude Code: include `isolation: "worktree"` in the Agent tool call to run the sub-agent in an isolated git worktree. If this parameter is not supported, instruct the sub-agent to call `EnterWorktree` as its first action. Each worktree gets its own branch. Orchestrator merges worktree branches sequentially after validation
  - For Codex: no worktree equivalent exists. Rely on file ownership scoping + sequential execution for build isolation
- File ownership: declare in each agent's context handoff. Agent MUST NOT modify files outside its declared scope

**Error Recovery**
- Agent failure (crash, context overflow, garbage output): spawn a fresh agent with the same context handoff. Do not retry the crashed agent. Include failure context: "Previous agent failed with: {reason}. Start fresh."
- Merge conflict: if sequential merge of worktree branches conflicts, stop and present conflicts to the user. Do not auto-resolve merge conflicts across agent boundaries
- Quality gate failure: re-run the failing agent with feedback from the gate. Max 2 retries per gate, then escalate to user

**Progress Observability**
- Update TODO.md after every significant step (completing a file, passing a test, hitting an error)
- Long-running orchestrations: write status to a `FORGE-STATUS.md` file with: current milestone, active agents, completed steps, pending steps, blockers. **Only the orchestrator writes FORGE-STATUS.md** — sub-agents report status to the orchestrator inline, not by writing to shared files
- **Progress narration** (from OpenAI Codex): Before each significant action batch, emit a brief human-readable progress note explaining what the agent is about to do and why. This serves both observability and debugging
- Never run silently for extended periods. If a cycle produces no observable output for 5+ minutes, write a progress note

### Format
This skill is a practices guide (reference document), not a procedural workflow. Structure as sections with clear headers, code examples, and decision tables. Similar pattern to remotion-best-practices.

### Metadata
```yaml
user-invocable: true
tags: [claude, teams, agents, multi-agent, best-practices]
```

---

## Skill 2: forge-codex-multiagent (Layer 0 — Practices)

### Purpose
Codifies best practices for Codex CLI's multi-agent features. Parallel to forge-claude-teams but for Codex's different API surface.

### API Verification
The API surface below was derived from session log analysis (887 spawn_agent calls across 5 days). Codex CLI is evolving — verify these APIs exist and match current signatures before implementing. If an API has been renamed or removed, update this guide to match the current Codex CLI.

### Content Areas

**Core Multi-Agent API**
- `spawn_agent(name, instructions, [model])`: create a child agent with a specific task. Instructions must include the same 5-component context handoff as Claude
- `send_input(agent_id, message)`: send work or follow-up instructions to a running agent
- `wait(agent_id, [timeout])` / `resume_agent(agent_id)`: synchronous wait or resume after suspension
- `close_agent(agent_id)`: graceful shutdown with output collection
- `fork_context(instructions)`: clone current context into a new agent. Use for "what if" exploration or parallel approaches to the same problem

**Batch Processing**
- `spawn_agents_on_csv(csv_path, template)`: batch spawn from a CSV. Each row becomes an agent with templated instructions
- Use for: processing multiple files with the same operation, running the same test across multiple configurations, parallel research on multiple topics
- `max_threads` config: default to 3. Never exceed 7 (Gunther's USL applies here too)

**Conflict Prevention (Codex-specific)**
- Same pyramid as Claude but with Codex-specific implementation:
  - Research agents: shared context, read-only tools only
  - Build agents: each agent gets an explicit `scope` field listing owned files. Agent MUST check scope before modifying any file
  - Use `fork_context` for exploratory branches that might conflict — discard the fork if the approach doesn't work
- No worktree equivalent in Codex — rely on file ownership scoping and sequential merging
- Atomic state: if agents share state files (state.json, TODO.md), use read-modify-write with conflict detection. Write to agent-specific output files, let orchestrator merge

**Patterns from Session Log Analysis**
- Short focused sessions outperform long unfocused ones: keep each agent's task to one clear objective
- Ownership scoping is the #1 predictor of multi-agent success: always declare file ownership
- Queue-codex batch mode patterns: HALT/SKIP/IDLE/DONE signal protocol for unattended runs
- 887 spawn_agent calls analyzed: most successful pattern is fan-out with independent tasks, not pipeline

**Model Selection**
- Workers inherit main model. No `model` parameter override unless user explicitly requests cost optimization
- Codex default model applies if not specified — this is acceptable as long as the default matches the main session model

**Error Recovery**
- Agent failure: `close_agent` to collect partial output, then `spawn_agent` with fresh instructions including failure context
- Never `send_input` to a failed agent — spawn fresh
- Timeout: set reasonable `wait` timeouts. If an agent exceeds timeout, close and retry with simplified task

### Format
Practices guide (reference document). Parallel structure to forge-claude-teams.

### Metadata
```yaml
user-invocable: true
tags: [codex, multi-agent, spawn-agent, best-practices]
```

---

## Skill 3: forge-research (Layer 1 — Capability)

### Purpose
Pure autonomous research skill. Launches multi-agent research campaigns with hypothesis tracking, source verification, adversarial challenge, and iterative deepening. Can be used standalone or orchestrated by forge-orchestrator.

### Entry Point
User provides a research question, topic, or directive. Can also receive structured research requests from forge-orchestrator.

### Workflow

```
1. Parse research directive → extract questions, scope, constraints
2. Detect platform and read the corresponding practices guide:
   - Claude Code: read forge-claude-teams SKILL.md (check for Agent/TeamCreate tools)
   - Codex CLI: read forge-codex-multiagent SKILL.md (check for spawn_agent/AGENTS.md)
   - See "Platform Detection and Conditional Paths" in Cross-Cutting Concerns
3. Formulate initial hypotheses and create explicit **Questions to Resolve** list:
   ```markdown
   ## Questions to Resolve
   - [ ] {question 1}
   - [ ] {question 2}
   - [x] {resolved question} — answer: {brief answer}
   ```
   This list is the termination criteria — research cannot complete while unchecked questions remain. Each research cycle must resolve, reclassify, or explicitly mark questions as "unresolvable with available sources"
4. Launch research agents (phase 1 — breadth):
   - Spawn study sub-agents for web research (study skill)
   - Spawn codebase exploration agents for code analysis
   - Spawn session log analysis agents if workflow insights needed
   - DEFAULT: sequential launches. Parallelize ONLY for genuinely independent queries
5. Collect and synthesize phase 1 results
6. Adversarial challenge:
   - Self-critique: review findings for bias, gaps, contradictions
   - Spawn adversarial reviewer agent: "Find flaws in these findings"
7. Launch targeted research agents (phase 2 — depth):
   - Fill gaps identified by adversarial review
   - Cross-reference claims across 2+ sources
   - Deep crawl: follow links, read sub-pages, find actual docs
8. Synthesize final findings with confidence scores
9. Write output to specified location (default: architect/research/{topic}.md)
   - If topic already has research output: append new findings under a timestamped header, don't overwrite previous research
```

### Research Quality Standards
- Official documentation first, always
- Reject information older than 2 years (unless foundational)
- Cross-reference factual claims across 2+ sources
- Deep crawl: follow links, read sub-pages, find actual content
- Reject AI-generated SEO spam and low-quality blog posts
- Every claim must have a source citation

### Termination Conditions
- **Questions to Resolve list is empty**: At research start, maintain an explicit list of open questions. Each research cycle must resolve or reclassify questions. Research cannot terminate while questions remain unresolved (adapted from Gemini CLI's Codebase Investigator — the only agent with a formal "cannot terminate until complete" rule)
- All hypotheses confirmed or refuted with evidence
- Adversarial review finds no critical gaps
- Diminishing returns: last research cycle produced <10% new information
- Maximum 3 depth cycles (to prevent infinite loops)

### Sub-Agent Context
For each research sub-agent, draft a context handoff with:
- Task: specific research question
- Context: what's already known, hypotheses to test
- Scope: which sources/domains to search
- Boundaries: what NOT to research (avoid scope creep)
- Output: format (structured findings with sources), location (write to disk or return inline)

Persist context handoffs to disk (`architect/agent-contexts/{agent-name}.md`) for long-running research campaigns. Use ephemeral inline prompts for quick single-query agents.

### Relationship to Study Skill
forge-research spawns study agents as one tool among many. Study stays independent for standalone use. forge-research adds: multi-agent parallelism, hypothesis iteration, adversarial challenge of findings, cross-agent synthesis.

**Fallback if study skill is not installed**: forge-research falls back to direct WebSearch/WebFetch calls for web research. Study is preferred (structured output, source verification) but not required. Log a warning: "study skill not found, using direct web search (reduced source verification)."

### Output Format
```markdown
# Research: {topic}
## Summary
{2-3 sentence synthesis}

## Key Findings
1. {finding} — confidence: {high|medium|low} — sources: {list}
2. ...

## Hypotheses
| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| ... | confirmed/refuted/uncertain | ... |

## Gaps and Limitations
- {what couldn't be determined and why}

## Sources
- {url or reference} — {what it provided}
```

### Metadata
```yaml
user-invocable: true
tags: [research, autonomous, multi-agent, study]
```

---

## Skill 4: forge-builder (Layer 1 — Capability)

### Purpose
Autonomous building/coding skill with self-review, self-improvement, and quality validation loops. Can be used standalone or orchestrated by forge-orchestrator.

### Entry Point
Two modes:
- **Orchestrated** (invoked by forge-orchestrator with structured plan): skip auto-detect, use the provided plan directly. Do NOT ask the user anything — the orchestrator has already established the plan
- **Standalone** (invoked directly by user): first classify the request:
  - **Directive** (unambiguous request for action): "Build the auth module", "Add caching to the API" → proceed with auto-detect and build
  - **Inquiry** (request for analysis or advice): "How should we handle auth?", "What's the best caching strategy?" → respond with analysis only, do NOT modify files until a follow-up directive is issued
  This classification (adapted from Gemini CLI) prevents the builder from auto-implementing when the user is exploring options.

  For directives, auto-detect input:
  1. Check for `architect/` directory with plan artifacts
  2. If found: verify freshness (mtime vs git log, CLAUDE.md phase vs TODO.md state). "Stale" = architect/ mtime is older than the most recent 3 commits, OR CLAUDE.md phase doesn't match TODO.md state
  3. If stale or ambiguous: ask user — "Found architect/ from a previous iteration. Use it, start fresh, or describe what you want?"
  4. If no architect/: accept direct instructions or run a quick structuring pass

### Workflow

```
1. Parse build directive → extract goals, constraints, existing codebase context
2. Detect platform and read the corresponding practices guide:
   - Claude Code: read forge-claude-teams SKILL.md (check for Agent/TeamCreate tools)
   - Codex CLI: read forge-codex-multiagent SKILL.md (check for spawn_agent/AGENTS.md)
   - See "Platform Detection and Conditional Paths" in Cross-Cutting Concerns
3. Plan implementation approach (if no plan exists):
   - Break work into phases with clear milestones
   - Identify file ownership boundaries for each phase
   - Define quality gates for each milestone
4. Execute build phases:
   For each phase:
     a. Implement code changes (sequential by default)
     b. Self-review: structured review of own changes against requirements
     c. Run tests (if test infrastructure exists)
     d. Self-improvement scan:
        - Performance: obvious inefficiencies, unnecessary allocations, O(n²) in hot paths
        - Implementation quality: better patterns, clearer naming, reduced duplication
        - Error handling: missing edge cases in external boundaries
        - Test coverage: untested paths in modified code
     e. Implement improvements (scope: existing functionality only)
     f. Quality gate check:
        - Tests pass
        - Linting clean
        - Self-review finds no critical issues
        - Changes match requirements
     g. If gate fails: fix issues, re-run gate (max 2 retries)
     h. Update TODO.md with phase completion status
5. New feature detection:
   - During implementation, if the agent identifies potential new features:
     a. Classify: improvement (implement) vs new feature (suggest)
     b. Improvement = changes to existing functionality: performance, readability, error handling for existing code paths → implement directly
     c. New feature = new functionality that doesn't exist yet: new endpoints, new commands, new user-facing behavior → write to SUGGESTIONS.md
     d. For suggestions: research the feature, draft a plan, iterate with self-review, assign confidence score, save to SUGGESTIONS.md
6. Final validation:
   - Run full test suite
   - Verify all TODO.md items completed or documented as deferred
   - Generate completion summary
```

### SUGGESTIONS.md Format (Bidirectional)

SUGGESTIONS.md is a **bidirectional async communication channel** — the agent writes suggestions, the human writes feedback. This allows human steering of autonomous development without interrupting the workflow.

```markdown
# Suggestions

## {Feature Title}
- **Confidence**: {1-5} — {rationale for score}
- **Type**: new-feature | enhancement | optimization
- **Impact**: {what it improves and for whom}
- **Effort**: {rough estimate: small/medium/large}
- **Research**: {summary of research done}
- **Plan**: {implementation approach}
- **Files affected**: {list}
- **Dependencies**: {what must exist first}
- **Status**: proposed | researched | planned | ready-for-review | approved | rejected | implemented

### Human Feedback
<!-- Human: write comments, approve, or reject below. Agent reads this on each pass. -->
- Decision: {approved | rejected | needs-revision}
- Comments: {any notes, constraints, or direction from human}
```

**Status lifecycle**:
1. Agent creates suggestion → status: `proposed`
2. Agent researches → status: `researched`
3. Agent drafts plan → status: `planned`
4. Agent self-reviews plan → status: `ready-for-review`
5. Human writes decision in `### Human Feedback` section:
   - `approved` → agent proceeds to implement in next build cycle
   - `rejected` → agent skips, leaves suggestion for reference
   - `needs-revision` + comments → agent refines the plan incorporating feedback, cycles back to `planned`
6. Agent implements approved suggestion → status: `implemented`

**How the agent processes human feedback**: At every milestone boundary and during the COMPOUND STEP, the orchestrator re-reads SUGGESTIONS.md and checks for human feedback:
- **Approved suggestions** with status `ready-for-review` or `planned`: promote to a new milestone or add to the next milestone's scope. The plan is already drafted — proceed to build
- **Rejected suggestions**: update status to `rejected`, leave in file for reference. Do not re-suggest unless the human explicitly revises their decision
- **Needs-revision suggestions**: incorporate human comments into the plan, re-run self-review, update status back to `planned`
- **No feedback yet**: leave as-is. The agent does NOT block waiting for feedback — it continues with other work

**Write ownership**: Only the orchestrator (or the standalone skill's main thread) writes to the agent-authored sections of SUGGESTIONS.md (everything except `### Human Feedback`). Sub-agents return suggestions inline in their output. The orchestrator collects and appends them to SUGGESTIONS.md in a single write after the review phase completes. The `### Human Feedback` section under each suggestion is exclusively human-written — the agent reads it but never modifies it.

### Improvement vs New Feature Decision Boundary
- **Implement directly** (improvement): performance optimization of existing code, refactoring for clarity, adding error handling to existing external-facing boundaries, adding tests for existing untested code, fixing inconsistencies in existing patterns
- **Save to SUGGESTIONS.md** (new feature): any new user-facing behavior, new API endpoints/commands/UI elements, new integrations, new configuration options, significant architectural changes

When in doubt, save to SUGGESTIONS.md. The cost of suggesting something the user implements is far lower than the cost of implementing something the user rejects.

### Quality Gate Criteria
**"Validation is the only path to finality."** (Gemini CLI — the strongest validation mandate across all major agent platforms.) Never assume success or settle for unverified changes. A milestone passes when ALL of:
1. All tests pass (if test infrastructure exists; if not, skip this check)
2. Lint/format clean (if configured; if not, skip)
3. Self-review: no critical issues (broken functionality, security vulnerabilities, data loss risks)
4. Changes satisfy the milestone's stated requirements
5. No regressions in existing functionality

Gate failure protocol: fix → re-gate (max 2 retries) → escalate to user with details

### Long-Running Build Sessions
For builds spanning multiple milestones or exceeding context limits (from Anthropic's "Effective Harnesses for Long-Running Agents"):
- **Single-feature focus**: Each build agent targets exactly one milestone or feature. Don't combine unrelated work in a single agent session
- **Git-based checkpointing**: Commit after each completed feature/milestone. This enables rollback and state recovery
- **Compaction-resilient state persistence**: Auto-compaction will happen — the agent cannot prevent or invoke it. Design for graceful survival: persist all meaningful state to disk (FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md) continuously, so that after compaction the agent can re-read state files and recover lost detail. CLAUDE.md survives compaction verbatim (re-read from disk, not summarized) and serves as the anchor containing re-read instructions. Research confirms quality degrades after 2+ compactions (Amp abandoned compaction entirely; Codex users report agents "losing track of current turn"; Claude Code known issue #6004 infinite compaction loops). Mitigation is continuous state persistence + sub-agent delegation to keep the main context leaner
- **Test-first development**: When test infrastructure exists, write/update tests before implementation. Tests serve as both specification and verification (Simon Willison's Red/Green TDD pattern)
- **Verification tools**: Use browser automation (if available) for UI testing. Anthropic reports this "dramatically improved performance"

### Conflict Prevention (Build-Specific)
When forge-builder is orchestrated and multiple build agents run:
- Each agent gets exclusive file ownership via context handoff
- Agents MUST NOT modify files outside their declared scope
- If an agent discovers it needs to modify an out-of-scope file: write the needed change to a `DEFERRED-CHANGES.md` file, continue with current scope
- Orchestrator processes deferred changes after the current phase completes. If multiple agents defer changes to the same file, orchestrator reviews all deferred changes for that file together, reconciles conflicts, and applies as a single coherent edit

### Metadata
```yaml
user-invocable: true
tags: [builder, autonomous, self-review, self-improvement, coding]
```

---

## Skill 5: forge-orchestrator (Layer 2 — Orchestrator)

### Purpose
Master orchestrator that sequences forge-research and forge-builder through milestone-gated cycles with adversarial review, testing, brainstorming, documentation, and second-opinion agents. Designed for long-running autonomous sessions.

### Entry Point
User provides a goal: feature to build, problem to solve, or codebase to improve. Open-ended directives ("make this better") require the orchestrator to first scope the work: scan the codebase, identify the top 5-10 most impactful improvements, present them to the user for approval, then proceed with approved items only. The orchestrator MUST NOT generate unbounded milestone lists from vague goals.

The orchestrator determines "done" through milestone gates + diminishing returns:
- Each milestone has explicit pass criteria
- Iteration within a milestone stops when the last cycle improved <10% (diminishing returns)
- The overall orchestration stops when all milestones pass or the user intervenes

### Workflow

```
1. Intake and orientation:
   a. Read FORGE-HANDOFF.md (if exists — indicates resumption after compaction or session restart). Follow its Bootstrap sequence
   b. Read FORGE-STATUS.md, CLAUDE.md, TODO.md, FORGE-MEMORY.md, architect/ if they exist
   c. If none exist: create CLAUDE.md and TODO.md from project scan
   d. Detect platform and read the corresponding practices guide:
      - Claude Code: read forge-claude-teams SKILL.md (check for Agent/TeamCreate tools)
      - Codex CLI: read forge-codex-multiagent SKILL.md (check for spawn_agent/AGENTS.md)
      - See "Platform Detection and Conditional Paths" in Cross-Cutting Concerns
   e. Create HUMAN-INPUT.md, MISSION-CONTROL.md, and FORGE-HANDOFF.md (empty templates) if they don't exist
   f. Check HUMAN-INPUT.md and MISSION-CONTROL.md for any pre-existing human directives
   g. Parse user's goal into structured milestones (incorporating any human directives)
   h. Write initial plan to TODO.md

2. For each milestone (CHECK HUMAN STEERING FILES + SUGGESTIONS.md AT EVERY PHASE TRANSITION):
   a. RESEARCH PHASE
      - Launch forge-research for any unknowns in the milestone
      - Research runs to completion before building starts
      - Output: research findings in architect/research/

   b. PLANNING PHASE (complexity-adaptive — from Gemini CLI)
      - **Simple milestones** (single file, clear spec): skip detailed planning, proceed directly to build with inline approach notes
      - **Standard milestones**: draft concise approach summary with key decisions
      - **Complex milestones** (multi-file, unknowns, architectural choices): draft detailed plan with at least two approaches and trade-off analysis
      - Draft implementation plan for this milestone
      - Self-critique the plan
      - Spawn adversarial review agent: "Find flaws in this plan"
      - Iterate plan until adversarial review passes (max 3 iterations). "Passes" = no CRITICAL or HIGH severity findings remain. MEDIUM and LOW findings are acceptable and noted for implementation awareness

   c. BUILD PHASE
      - Launch forge-builder with the refined plan
      - Builder executes with self-review and self-improvement loops
      - Builder writes completion signal when done

   d. REVIEW PHASE (parallel fan-out — these are read-only independent reviewers)
      **Critical**: All review agents run in FRESH context windows. They receive only: (1) the milestone spec/requirements, (2) the git diff of changes, (3) relevant test results. They do NOT receive the builder's conversation history. Same-model self-review in the same context exhibits confirmation bias at scale — the model hallucinates correctness because the output matches patterns it just generated (ASDLC adversarial code review research: 40-60% quality improvement with separated review)
      - Spawn up to 3 review agents at a time to avoid rate limits:
        Batch 1 (critical reviews):
        - Adversarial review agent: "Find bugs, logic errors, security issues"
        - Performance review agent: "Find performance issues, inefficiencies"
        - Test review agent: "Are tests comprehensive? What's missing?"
        Batch 2 (enhancement reviews, after batch 1 completes):
        - Documentation agent: "Update/create docs for changes made"
        - Brainstorm agent: "What improvements or optimizations could be made?"
      - All review agents return findings inline to the orchestrator (not to shared files)
      - Orchestrator collects all findings in memory AND proactively serializes them to `architect/review-findings/{milestone}.md` at the end of each review batch. This dual strategy means findings are available inline for immediate use AND on disk for context overflow recovery (see Error Recovery)

   e. SECOND-OPINION PHASE (optional, graceful degradation)
      - This phase is experimental and may be skipped entirely if unreliable
      - Try launching second-opinion agents via other CLIs (requires separate auth + CLI installed):
        - Codex CLI (if available): send git diff of milestone changes + intent summary
        - Gemini CLI (if available): send git diff of milestone changes + intent summary
        - Claude CLI (if in Codex): send git diff of milestone changes + intent summary
      - Skip any unavailable CLIs. Note which opinions were unavailable
      - If ALL CLIs unavailable or fail: skip entire phase (common case), note in summary
      - Collect any findings and reconcile with internal review results

   f. IMPROVEMENT PHASE
      - Consolidate all review findings
      - Classify: bug fix (apply) | improvement (apply) | new feature (SUGGESTIONS.md)
      - Launch forge-builder with consolidated fixes and improvements
      - Re-run quality gates

   g. QUALITY GATE
      - Tests pass
      - All critical review findings addressed
      - No regressions
      - Diminishing returns check: did this cycle improve substantially over last?
      - If gate passes: proceed to COMPOUND step
      - If gate fails: loop back to BUILD PHASE (max 2 retries per milestone)

   h. COMPOUND STEP (after gate passes)
      - Codify learnings from this milestone into persistent project context:
        - Update CLAUDE.md with new conventions/patterns/decisions discovered
        - Consolidate SUGGESTIONS.md with new suggestions from review agents
        - **Check SUGGESTIONS.md for human feedback**:
          - Approved suggestions → add as new milestones or append to upcoming milestone scope
          - Rejected suggestions → mark status `rejected`, skip
          - Needs-revision suggestions → incorporate comments, refine plan, mark `planned`
        - Update TODO.md with deferred items, next steps, and any newly approved suggestions
        - Note any reusable test patterns or fixtures for future milestones
      - This step ensures each milestone makes the next milestone easier AND incorporates human steering

3. Finalization:
   a. Run full test suite
   b. Update CLAUDE.md with what was built
   c. Update TODO.md with completion status
   d. Consolidate SUGGESTIONS.md (deduplicate, reconcile)
   e. Generate summary: what was done, what was deferred, what needs human attention
   f. Update FORGE-STATUS.md with final state
```

### Milestone Structure
Each milestone is defined with explicit **per-step success criteria** (from Claude Code's Skillify pattern — without success criteria, agents frequently skip steps or declare premature completion):
```markdown
## Milestone: {name}
- Goal: {what this milestone achieves}
- Dependencies: {which milestones must complete first}
- Files in scope: {directories/files this milestone owns}
- Quality criteria: {specific pass conditions}
- Research needed: {unknowns to resolve before building}
- Steps:
  1. {step name}
     - Success criteria: {concrete, verifiable condition proving this step is done}
     - Artifacts: {files/data this step produces for later steps}
  2. {step name}
     - Success criteria: ...
     - Artifacts: ...
```

### Parallelism Model: Parallelized Serial Threads

The orchestrator uses a **parallelized serial threads** model — NOT pure parallelism or pure sequential.

**Core concept**: Launch parallel THREADS where each thread takes ownership of a coherent chunk of work and runs serial/sequential steps within it. Each thread:
- Owns a complete sub-pipeline (research → plan → build → review within its scope)
- Accumulates context as it progresses (the key advantage of sequential work)
- Can spawn its OWN sub-agents for exploration, review, research
- Has exclusive file ownership boundaries

This is how a dev team works: each developer owns a feature, works sequentially on it, but multiple developers work in parallel on different features.

**Thread allocation**:
- Independent milestones → separate threads (max 2-3 concurrent build threads)
- Within a thread: strictly sequential (research → plan → build → review → improve)
- Review agents within a thread: can fan out read-only (3 max)
- Research queries: can fan out within a thread (3-5 independent queries)

**Rules**:

| Pattern | Parallelism | Rationale |
|---------|------------|-----------|
| Independent milestones | Parallel threads (2-3 max) | Each thread owns its files, sequential internally |
| Phases within a milestone | Sequential within thread | Context accumulation, data dependency |
| Build agents on related files | Sequential within thread | Cascading changes need prior context |
| Review/audit after build | Fan-out within thread (3 max) | Independent read-only reviewers |
| Research queries | Fan-out within thread (3-5 max) | Independent information gathering |
| Two threads modifying same file | NEVER | Redesign decomposition |
| Build and review simultaneously | NEVER | Review needs completed code |
| Multiple threads writing same output | NEVER | Use orchestrator as single writer |

### Agent Spawning Protocol
For every sub-agent, the orchestrator:
1. Drafts a context handoff using the Sub-Agent Prompt Template from Prompt Engineering Standards (5 concerns → 7 XML tags: objective, context, output-format, tools, boundaries, quality-bar, task)
2. Validates: spawn prompt under 4K tokens, objective describes end-state not procedure, output-format includes parseable schema, context is task-specific only
3. For workers/validators: writes handoff to `architect/agent-contexts/{agent-name}.md`
4. For quick explorers/researchers: uses inline ephemeral prompts
5. Sets model: inherit main model (no `model` parameter override)
6. Sets isolation: `"worktree"` for build agents on different files; shared working tree for research/review agents
7. Chooses agent type:
   - **Custom agent** (`.claude/agents/forge-*`): for leaf-level workers needing tool restrictions and context isolation (reviewers, auditors, focused builders). These cannot spawn sub-agents
   - **Agent tool sub-agent** (general-purpose): for thread coordinators that need to spawn their own sub-agents within their scope. These retain full tool access including the Agent tool
8. Validates output on return: quick sanity check before passing to next step (see "Inter-Agent Validation")

### Merge Strategy
When build agents use worktrees:
1. Each worktree creates a branch from the current HEAD
2. After an agent completes, orchestrator validates its output
3. Orchestrator merges worktree branches ONE AT A TIME: first by dependency order (if dependencies exist between agents), then by completion order (first-to-finish merges first) for independent agents
4. If merge conflicts: STOP. Present conflicts to user. Do not auto-resolve cross-agent conflicts
5. After successful merge: next agent's branch merges on top

### Error Recovery
- Agent crash: **spawn a FRESH agent** with the same context handoff + failure note. Include failure context: "Previous agent failed with: {reason}. Start fresh." Leave the failure details in context — error traces help the model avoid repeating mistakes. **Critical principle**: restarting with fresh instructions often succeeds faster than continued iteration in a degraded context (Devin Agents 101). Never `send_input` to a failed agent or try to recover a crashed context — spawn fresh
- Quality gate failure: fix → re-gate (max 2 retries) → escalate to user
- Merge conflict: present to user, pause orchestration
- All CLIs unavailable for second opinion: skip second-opinion phase, note in summary
- Context overflow in orchestrator — compaction survival protocol:
  1. The orchestrator cannot detect or prevent auto-compaction directly (context usage is not exposed to the agent — Issue #23457). Mitigation: persist state continuously so compaction at any point is survivable
  2. After auto-compaction occurs: CLAUDE.md is re-loaded from disk (verbatim, not summarized). The `## Forge Pipeline State` section in CLAUDE.md instructs the agent to re-read FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md, and FORGE-MEMORY.md
  3. The agent re-reads these files and recovers session-level context that was lost in summarization
  4. The orchestrator MUST persist state continuously (after every phase transition) so that compaction mid-phase loses at most one phase of context
  5. Resumption: agent reads FORGE-HANDOFF.md → FORGE-STATUS.md → picks up from last completed phase transition. Partially-completed phases are re-run from scratch (idempotent by design)
  6. If an external orchestrator (Ralph loop, CI, cron) kills and restarts the agent: the same files work — the fresh agent reads FORGE-HANDOFF.md and bootstraps from scratch. This is a bonus optimization, not a requirement

### Context Recovery: Compaction-Resilient State Persistence

**The agent cannot kill and restart itself.** This is a confirmed, well-documented limitation across all major agent CLIs:
- Slash commands (`/clear`, `/compact`, Codex `/new`) are user-typed only — the agent cannot invoke them (Claude Code Issue #19877)
- The Ralph Wiggum plugin (Anthropic official) accumulates context instead of resetting (Issue #125). PR #126 attempted `--fresh-context` but failed — Stop hooks run in non-terminal context, cannot spawn interactive sessions
- Feature requests for agent-invocable fresh-context (#12665, #16440) remain unimplemented
- `claude -p` from Bash spawns a nested child process — the parent session continues with its accumulated context
- At the API level, `pause_after_compaction` exists but is not exposed to the CLI agent

**Therefore: auto-compaction WILL happen, and the forge pipeline designs for graceful survival, not escape.**

**The compaction survival mechanism**:
1. **CLAUDE.md is the anchor** — re-read verbatim from disk after every compaction (confirmed behavior, not summarized). This is the single most important survival property
2. **CLAUDE.md contains a `## Forge Pipeline State` section** that instructs the agent to re-read state files after compaction. Because CLAUDE.md survives verbatim, this instruction persists across unlimited compaction cycles
3. **State files on disk** (FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md, FORGE-MEMORY.md) are the authoritative source of truth — not conversation context. After compaction strips detail from conversation history, the agent re-reads these files to recover
4. **Sub-agents provide natural context isolation** — short-lived, fresh context windows. Heavy work (research, reviews, builds) runs in sub-agents, keeping the orchestrator's context leaner and delaying compaction triggers
5. **Git commits as checkpoints** — even if all context is severely degraded, git log + state files enable recovery

**CLAUDE.md forge sections** (written by the orchestrator during intake):

Two sections serve distinct purposes — one guides what the compaction *summarizer* preserves, the other guides the agent *after* compaction:

```markdown
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
```

**Important nuance**: After compaction, the agent is NOT starting from zero. It still has: the compaction summary (lossy but present), CLAUDE.md (verbatim), system prompt, tool definitions, and potentially recent messages. FORGE-HANDOFF.md *supplements* this existing context by filling in session-level details the summary likely lost — it does not need to replicate what CLAUDE.md already provides. This is why FORGE-HANDOFF.md can be concise (~600 tokens) rather than a full onboarding bundle.

**Known limitation**: Issue #13919 reports that agents sometimes ignore CLAUDE.md instructions to re-read files after compaction (training bias overrides explicit instructions). Mitigations:
- Keep the `## Forge Pipeline State` section short, prominent, and imperative
- FORGE-HANDOFF.md's "What's In Progress" section is self-describing — even if the agent doesn't proactively re-read, it recovers context when it naturally encounters the file
- Continuous state persistence means state files are always current, not stale snapshots from far back
- Optional: configure a SessionStart hook with `compact` matcher to inject a post-compaction reminder (see below)

**Optional SessionStart hook enhancement** (Claude Code only):
```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "compact",
      "hooks": [{
        "type": "command",
        "command": "echo 'COMPACTION DETECTED: Re-read FORGE-HANDOFF.md and FORGE-STATUS.md now.'"
      }]
    }]
  }
}
```
Note: Issue #15174 reports that SessionStart hook stdout is not reliably injected into context after compaction. This is a secondary signal, not the primary mechanism. The primary mechanism is CLAUDE.md surviving verbatim.

**Compaction policy**:
- Auto-compaction is expected and accepted — the agent cannot prevent or invoke it
- A single compaction in a short-lived sub-agent is harmless — the agent typically completes before quality degrades
- For the orchestrator and long-running build agents: compaction WILL degrade quality over 2+ cycles (summary stacking — after 3+ rounds, ~30% of context is consumed by cumulative summaries). Mitigation: continuous state persistence to disk + CLAUDE.md anchor ensures re-read instructions survive every compaction cycle
- Each compaction degrades conversation quality, but each re-read from disk recovers meaningful state — a **degradation-recovery cycle** that prevents the catastrophic context loss seen without state files
- **Compaction count tracking**: FORGE-HANDOFF.md Health section tracks `compaction_count`. After each post-compaction re-read, the agent increments this counter. This enables degradation-aware behavior:
  - Compactions 1-3: normal operation. Re-read state files, continue working
  - Compactions 4-5: delegate more aggressively to sub-agents. Reduce orchestrator's direct work to coordination only
  - After compaction 5: if an external orchestrator is available, trigger fresh-agent handoff. If not, continue with maximum sub-agent delegation and note degradation risk in FORGE-STATUS.md
- **User-configurable**: Claude Code's `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE` environment variable controls the auto-compact trigger threshold (1-100%, default ~95%). Users running long forge sessions may benefit from setting this to 50-80% for more frequent but higher-quality compaction cycles

**FORGE-HANDOFF.md** is a continuously-maintained state file. After compaction, the agent reads it and recovers session-level context. If an external orchestrator (Ralph loop, CI, cron) kills and restarts the agent, the same file enables instant bootstrapping. It serves both purposes with the same structure.

**Structure**:
```markdown
# Forge Handoff — {timestamp}

## Bootstrap
CLAUDE.md is already loaded (survives compaction). Re-read the mutable state files:
1. This file (session-level context snapshot)
2. FORGE-STATUS.md (milestone/phase state)
3. TODO.md (task checklist)
4. FORGE-MEMORY.md (cross-session learnings)

After reading, verify: current milestone matches FORGE-STATUS.md,
current step matches TODO.md. If mismatch, trust FORGE-STATUS.md.

## Active Work
- **Milestone**: {N/total} — {name}
- **Step**: {N/total} — {name}
- **Status**: IN_PROGRESS | BLOCKED | COMPLETED
- **Working files**: {list}
- **Branch**: {current branch}

## What Was Just Completed
- [x] {step} (commit {hash})

## What's In Progress
{Specific description of current work, including last meaningful action}

## Failed Approaches (This Session)
- Tried {X} → {why it failed}

## Blockers / Open Questions
- {or "None currently"}

## Key Context (Not in Other Files)
- {Pattern or discovery not yet in CLAUDE.md}

## Session Log Digest
{Token-budgeted, high-signal decisions — max ~500 tokens.
Priority: direction changes > rejected alternatives > constraints > debugging pivots}

## Health
- last_updated: {ISO timestamp}
- steps_since_last_checkpoint: {N}
- compaction_count: {N — incremented each time agent detects post-compaction state}
- stuck_indicator: {true|false}
- consecutive_failures: {N}
```

**Update frequency and cost**:

| Trigger | Write Type | Token Cost |
|---------|-----------|------------|
| Step completed | TODO.md mark `[x]` | ~20 tokens |
| Every 5 steps | Lightweight update to Active Work + What's In Progress | ~200 tokens |
| Milestone completed | Full checkpoint (overwrite FORGE-HANDOFF.md) | ~600 tokens |
| Failed approach | Append to Failed Approaches | ~100 tokens |
| Post-compaction recovery | Update compaction_count in Health, verify state consistency | ~100 tokens |

Total for a 4-milestone run: ~3,000 output tokens — negligible vs 10,000+ tokens wasted re-discovering context from scratch.

**Context recovery protocol** (after compaction or external restart):
1. CLAUDE.md is in context (survives compaction verbatim; loaded fresh on external restart)
2. `## Forge Pipeline State` section instructs: re-read FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md, FORGE-MEMORY.md
3. Agent reads FORGE-HANDOFF.md → learns what it was doing, what was completed, what failed
4. Agent reads FORGE-STATUS.md → confirms current milestone and phase
5. Agent resumes from the point described in "What's In Progress"
6. Agent increments `compaction_count` in FORGE-HANDOFF.md Health section

**Design principle**: FORGE-STATUS.md tracks orchestrator-level state (milestones, phases). TODO.md tracks tasks. FORGE-MEMORY.md tracks cross-session learnings. FORGE-HANDOFF.md fills the gap none of them cover: **session-level context** — "what was the agent doing RIGHT NOW when it was compacted?" Without this, the agent must reconstruct from git diff and guesswork, costing 10K+ tokens of wasted exploration.

**Write ownership**: Only the orchestrator (main thread) writes FORGE-HANDOFF.md. Sub-agents report state inline to the orchestrator. The orchestrator consolidates into the handoff file.

**External orchestration compatibility**: If the user sets up an external loop (Ralph Wiggum technique, CI pipeline, cron job) that kills and restarts the agent, the same state files work without modification. The external loop runs `claude -p "Read FORGE-HANDOFF.md and continue the forge pipeline."` — the agent bootstraps from disk. This is the optimal path (true fresh context), but it requires user setup outside the agent's control.

### Progress Observability
- FORGE-STATUS.md: updated at every phase transition within every milestone
  ```markdown
  # Forge Status
  ## Current Milestone: {name} — Phase: {research|planning|build|review|improvement|gate}
  ## Milestones
  - [x] Milestone 1: {name} — completed
  - [ ] Milestone 2: {name} — in progress (build phase)
  - [ ] Milestone 3: {name} — pending (blocked by Milestone 2)
  ## Active Agents
  - {agent-name}: {status} — {brief description}
  ## Last Update: {timestamp}
  ```
- TODO.md: updated at milestone completion (human-facing persistent task tracker)
- CLAUDE.md: updated at milestone completion (current phase, phase progress)
- Distinction: TODO.md is for humans and session continuity. FORGE-STATUS.md is the orchestrator's internal state (current phase, active agents, phase transitions). Both are updated but serve different audiences
- **Consolidated write ownership rule**: Only the orchestrator (main thread) writes to: FORGE-STATUS.md, FORGE-HANDOFF.md, SUGGESTIONS.md (agent-authored sections), HUMAN-INPUT.md (Processed section), MISSION-CONTROL.md (Acknowledged section). Sub-agents return data inline; the orchestrator consolidates into shared files

### Concurrent Invocation Protection
On startup, check for FORGE-STATUS.md. If it exists and shows an active run ("in progress" status):
- Check staleness: if `Last Update` timestamp is older than 1 hour, treat as abandoned (previous run crashed without cleanup)
- If recent (< 1 hour): warn user — "A forge orchestration appears to be in progress. Resume it, or start fresh?"
- If stale (> 1 hour): warn user — "Found an abandoned forge run from {timestamp}. Resume it, or start fresh?"
- If resume: read FORGE-STATUS.md, pick up from last phase transition
- If fresh: archive existing FORGE-STATUS.md to FORGE-STATUS.{timestamp}.md, start clean

### Existing Project State
If invoked mid-project:
- CLAUDE.md exists → read it, use its conventions and structure
- TODO.md exists → read it, continue from current state, don't overwrite
- architect/ exists → check freshness, use if current, ask user if stale
- None exist → create CLAUDE.md from project scan, create TODO.md with milestone plan

### SUGGESTIONS.md Consolidation
The orchestrator is responsible for consolidating SUGGESTIONS.md:
- Deduplicate: merge suggestions from different agents that describe the same feature
- Reconcile: if two agents suggest conflicting approaches, note both with rationale
- Sort by confidence score (highest first)
- Process human feedback: promote approved items, skip rejected items, refine needs-revision items
- Update status of implemented suggestions to `implemented`
- Remove suggestions that were implemented during the current run (move to a `## Completed` archive section at the bottom)

### Human Steering Interface

The orchestrator supports **asynchronous human-to-agent communication** via three files that the human can write to at any time, without interrupting the autonomous workflow:
- **SUGGESTIONS.md** — bidirectional: agent writes suggestions, human writes approvals/rejections/comments. Agent checks at every COMPOUND STEP (see "SUGGESTIONS.md Format" in forge-builder)
- **HUMAN-INPUT.md** — human → agent: new work items and brainstorming ideas
- **MISSION-CONTROL.md** — human → agent: steering directives and course corrections

**HUMAN-INPUT.md** (human → agent: new work and brainstorming)
Human writes brainstorming ideas, feature suggestions, and new work items here. The orchestrator checks this file at every milestone boundary and at every phase transition. New entries are integrated as either:
- New milestones (if significant enough)
- Additions to the current milestone's scope
- New entries in SUGGESTIONS.md (if they're ideas, not directives)

Format:
```markdown
# Human Input

## New
<!-- Write new items here. Agent will process and move to Processed. -->
- Consider adding a caching layer to the API — I've seen performance issues in production
- Bug: the login flow breaks when email has a + character

## Processed
<!-- Agent moves items here after integrating them. -->
- [2026-03-03 14:22] Added caching investigation to Milestone 3 research phase
```

**MISSION-CONTROL.md** (human → agent: real-time steering and course correction)
Human writes directions, annotations, priority changes, stop/start directives. This is the "steering wheel" for long-running autonomous sessions. The orchestrator checks this file at every phase transition (research → planning → build → review → improve → gate).

Format:
```markdown
# Mission Control

## Active Directives
<!-- Human writes steering directives here. Agent acknowledges and follows. -->
- PRIORITY: Focus on the auth module first, defer the dashboard work
- STOP: Don't refactor the payment service — it's being replaced next sprint
- NOTE: The CI pipeline is flaky right now, don't block on test failures for integration tests

## Acknowledged
<!-- Agent moves processed directives here with timestamp and action taken. -->
- [2026-03-03 14:30] PRIORITY acknowledged — reordered milestones, auth is now Milestone 1
- [2026-03-03 14:35] STOP acknowledged — payment service excluded from scope
```

**Change detection**: At each check point, the orchestrator:
1. Reads the file
2. Compares hash against last-seen hash (stored in FORGE-STATUS.md)
3. If changed: parses `## New` / `## Active Directives` sections for unprocessed items
4. Processes items, moves them to `## Processed` / `## Acknowledged`
5. Updates hash in FORGE-STATUS.md

**Both files are created by the orchestrator at startup** (empty templates) if they don't exist. Human can start writing to them at any time.

### Metadata
```yaml
user-invocable: true
tags: [orchestrator, autonomous, forge, milestone, review, multi-agent]
```

---

## Cross-Cutting Concerns

### Model Selection
ALL sub-agents, teammates, and spawned agents — without exception — use the main session's model. No multi-model routing. No cost optimization via model downgrades. Zero sacrifices to output quality. Custom agents MUST set `model: inherit` in their YAML frontmatter to enforce this — omitting the field may cause platform defaults to apply.

This applies to: research agents, build agents, review agents, adversarial agents, documentation agents, brainstorm agents, second-opinion agents, and any agent spawned by those agents.

Do NOT downgrade models unless the user has explicitly stated they want cost optimization and have confirmed they accept quality trade-offs. This is not a default — it is a user override that requires explicit confirmation.

The only platform constraint (not a design choice): Claude Code's Explore subagent type uses haiku by default. This is a read-only file search tool, not a reasoning agent. Acceptable.

Rationale: Lusser's Law — 3% per-step quality drop compounds to 22% system failure at 10 agents in a chain. Expected value: $0.40 savings from weaker model vs $8.00 cascade failure cost. Every platform (Claude Code, Codex, Factory, Hydra) only downgrades read-only exploration — everything else uses frontier.

### Context Engineering

**Core principle** (from Gemini CLI): The orchestrator's own context window is its most precious resource. Every turn adds to permanent session history. When you delegate, the sub-agent's entire execution is consolidated into a single summary in your history, keeping your main loop lean. Design every delegation to maximize the ratio of useful insight returned per token consumed in the main context.

Sub-agent context handoff — 5 conceptual concerns, implemented as 7 XML tags per Prompt Engineering Standards:
1. **Task** (`<objective>` + `<task>`) — what to accomplish (end-state description, not step-by-step) and the specific action (task goes last per information ordering). Two tags serve one concern: objective at start, task at end
2. **Context** (`<context>`) — project state, decisions made, constraints. Maximum 2000 tokens. Only what this agent needs — fresh, minimal context is the rule
3. **Scope & Boundaries** (`<boundaries>`) — three-tier system: ALWAYS (mandatory behaviors + file/directory ownership), ASK FIRST (actions requiring orchestrator approval), NEVER (hard prohibitions including out-of-scope files)
4. **Output contract** (`<output-format>`) — YAML frontmatter for metadata (status, confidence, evidence) + Markdown body with role-specific structure. Structured output achieves >99% schema adherence. Sub-agents MUST return complete, self-contained responses — they cannot reference "above" or their own internal context (Harrison Chase, Sequoia 2025)
5. **Quality assurance** (`<tools>` + `<quality-bar>`) — neutral tool guidance and pre-flight verification checklist. Two additional XML tags that support quality: tool guidance prevents overtriggering, quality-bar ensures self-verification before output

See the full 7-tag XML template and role-specific contracts in Prompt Engineering Standards below.

Persistence:
- Workers and validators: write to `architect/agent-contexts/{name}.md` (survives context clears)
- Short-lived explorers and researchers: ephemeral inline prompts (no disk persistence)

**Context optimization principles** (from Anthropic context engineering guide + Manus production data + compaction research):
- **Just-in-time loading**: Maintain lightweight identifiers (file paths, queries). Load data at runtime via tools, not preloaded in context. Mirrors Claude Code's glob/grep for JIT file retrieval
- **Append-only context**: Never modify prior actions/observations in context. Even single-token differences invalidate downstream KV-cache (cached tokens cost 10x less than uncached — Manus production data)
- **Leave failed actions in context**: Error traces help the model update internal beliefs. Hiding failures hurts performance
- **Sub-agent return compression**: Each sub-agent explores extensively (tens of thousands of tokens) but returns condensed summaries (1-2K tokens). Memory + context editing improved agent search performance by 39% (Anthropic)
- **Structured note-taking**: Agents write progress notes to files (TODO.md, FORGE-STATUS.md, FORGE-HANDOFF.md) persisted outside context window. At each milestone boundary, the orchestrator writes current objectives to the end of the active context — this "recites objectives" to address lost-in-the-middle attention issues (Manus pattern)
- **Compaction survival via disk-based state**: Auto-compaction will happen — the agent cannot prevent it. Design for it: persist all meaningful state to disk continuously (FORGE-HANDOFF.md every 5 steps + at milestones). CLAUDE.md survives compaction verbatim and contains re-read instructions that point the agent back to state files. Compaction loses all tool outputs (Codex), degrades after 2+ cycles (all platforms), and can trigger infinite loops (Claude Code #6004). FORGE-HANDOFF.md is ~600 tokens to maintain; re-discovering context from scratch costs 10K+. Continuous persistence is always cheaper than re-discovery

### Prompt Engineering Standards

Universal rules for all prompts in the forge pipeline — SKILL.md files, custom agent definitions, sub-agent spawn prompts, and steering files. Grounded in cross-validated research from TurboDraft production data, Anthropic/OpenAI/Google vendor guidance, ICML 2025, TACL 2024, SWE-bench winners, and practitioner reports.

**XML structure as primary organization**
All forge prompts exceeding ~200 words use XML tags to delineate sections. Use semantic, descriptive tag names:

```xml
<objective>
Build the authentication middleware with RS256 JWT validation and refresh token rotation.
</objective>

<context>
{Minimal, task-specific context — only what this agent needs. Maximum 2000 tokens.}
</context>

<output-format>
{Parseable schema. YAML frontmatter for metadata, Markdown for content.}
</output-format>

<tools>
{Which tools to use and for what purpose. Neutral guidance, not pressure.}
</tools>

<boundaries>
ALWAYS: {mandatory behaviors, 2-4 items}
ASK FIRST: {actions requiring orchestrator approval, 1-3 items}
NEVER: {hard prohibitions, 2-4 items}
</boundaries>

<quality-bar>
{Pre-flight checklist the agent verifies before returning output.}
</quality-bar>

<task>
{The specific action to take — goes LAST per information ordering rules.}
</task>
```

XML is endorsed by all three major vendors (Anthropic, OpenAI, Google). Use XML for prompt structure, Markdown for content, YAML for metadata — they coexist.

**Information ordering: critical content at start and end**
Lost-in-the-middle: 30%+ accuracy degradation for information placed in the middle of long contexts (Liu et al., TACL 2024). All forge prompts follow this order:
1. OBJECTIVE (first — what to accomplish)
2. CONTEXT (reference material, specs)
3. CONSTRAINTS and BOUNDARIES (rules, limits)
4. OUTPUT FORMAT (schema, structure)
5. TASK INSTRUCTION (last — the specific action)

**Constraint formatting: explicit and measurable**
Explicit constraints reduce output variance 9x (0.8% vs 7.1%). Replace vague guidance with concrete thresholds: "Maximum 200 lines per file" not "Keep it concise." "Cover all public API endpoints, minimum 3 test cases per endpoint" not "Be thorough."

**Positive framing**
Write instructions as what TO DO, not what to avoid: "Write comments only for non-obvious logic" not "Don't write verbose comments." Reserve "NEVER" for the three-tier boundary system only. Vendor guidance consistently shows positive framing outperforms negative framing.

**Context budget rules**
Context rot: 20-50% accuracy drop from 10K to 100K tokens (Chroma, 18 models validated). Stay under 40% context utilization at spawn time.

| Surface | Budget | Enforcement |
|---------|--------|-------------|
| Sub-agent spawn prompt | Under 4K tokens | Orchestrator validates before spawning |
| Steering files total (all FORGE-*.md) | Under 8K tokens | Checked at generation time |
| Single SKILL.md body | Under 500 lines | Existing audit rule |
| Conversation context at spawn | Under 40% utilization | Orchestrator monitors |

**End-state descriptions for builders, numbered steps for orchestrator**
Frontier models perform better with goal descriptions than step-by-step procedures (Spotify, 1500+ PRs; Addy Osmani spec-driven development). Builder spawn prompts describe WHAT the output should be: "Build X that passes Y" beats "First do A, then B, then C." Orchestrator workflow stages remain numbered (sequential deterministic procedures benefit from explicit ordering).

**Selective CoT**
Chain-of-thought hurts by up to 36.3% on pattern recognition and classification tasks (ICML 2025, 9 models). Do NOT force "think step by step" uniformly. Use CoT only for genuine multi-step reasoning (debugging complex logic, architectural decisions). Skip it for structured tasks (code formatting, schema validation, simple transformations).

**Role prompting: only as container for behavioral instructions**
Role prompting alone has little/no measurable effect on accuracy (Schulhoff meta-analysis, 2500+ papers). "You are an expert senior engineer" wastes tokens. "You are a code reviewer. Report only issues with confidence >80%. Use this severity scale: [...]" works — the value comes from the behavioral instructions, not the role label.

**Few-shot examples: 1-2 optimal**
1-3 examples provide the benefit; diminishing returns after 2 and increasing context cost. Include 1-2 examples of desired output format in agent prompts, not more.

**Tool guidance: neutral, not aggressive**
Claude 4.6 overtriggers on aggressive tool-use prompting ("You MUST use tools", "ALWAYS call a tool"). Use neutral, purposeful guidance: "Use Read to examine files before modifying them. Use Bash to run tests after changes."

#### Sub-Agent Prompt Template

Reusable template for ALL sub-agent spawning. Implements the 5 conceptual concerns as 7 XML tags (task splits into objective+task for information ordering; quality assurance adds tools+quality-bar):

```xml
<agent-prompt>

<objective>
{1-3 sentences describing the end state. End-state, not procedure.}
</objective>

<context>
{Minimal, task-specific. Maximum 2000 tokens. Only what this agent needs.}
</context>

<output-format>
---
status: complete | blocked | partial
confidence: high | medium | low
evidence: [{file paths, line numbers, URLs}]
---

## Result
{Structured content per role-specific contract below}

## Verification
{How the agent verified its own output}
</output-format>

<tools>
{Explicit but neutral tool guidance. List only relevant tools.}
</tools>

<boundaries>
ALWAYS:
- {mandatory behaviors, 2-4 items}
ASK FIRST:
- {actions requiring orchestrator approval, 1-3 items}
NEVER:
- {hard prohibitions, 2-4 items}
</boundaries>

<quality-bar>
Before returning output, verify:
- [ ] Output matches the schema in output-format exactly
- [ ] All file references use absolute paths and exist
- [ ] Confidence level is justified by evidence
- [ ] No placeholder text remains
</quality-bar>

<task>
{Concrete action instruction — goes LAST. Specific: "Analyze src/auth/ for
SQL injection vulnerabilities" not "Review the code".}
</task>

</agent-prompt>
```

Template rationale: `<objective>` first (start placement), end-state description (frontier model performance), minimal `<context>` (40% budget), structured `<output-format>` (>99% schema adherence), neutral `<tools>` (overtrigger prevention), three-tier `<boundaries>` (Addy Osmani), `<quality-bar>` (fidelity ledger), `<task>` last (end placement, 30% improvement).

#### Role-Specific Prompt Contracts

**Research worker**: hypothesis-driven with source citation requirements
- Confidence rated per-claim, not just overall
- Every factual claim must cite source (URL or file:line)
- Counter-evidence included when found
- Output: findings table with confidence + evidence columns

**Build worker**: spec-driven with self-verification
- End-state objective from spec, not step-by-step procedure
- Run tests after each change (not batched at end)
- Self-review checklist: spec requirements met, existing tests pass, new tests added, scope respected
- Temperature 0.0 for code generation (SWE-bench winner pattern)
- Step limit: 60 tool calls max, then report status

**Adversarial reviewer**: confidence-gated with evidence requirements
- Report only issues with confidence >80%
- Every finding requires file:line evidence + code snippet
- Severity-confidence matrix (BugBot pattern): S3C3=critical, S2C2=warning, S1C1=info
- List excluded sub-80% findings separately (transparent, not hidden)
- Include at least one positive observation (counterbalances overcorrection bias)
- Explicit exclusion list: do not flag style preferences, known non-issues, theoretical concerns
- Overcorrection bias mitigation: LLM reviewers prompted to "explain and propose corrections" assume flaws exist even in correct code (arXiv 2602.16741). Confidence gating + evidence requirements are the primary defense

**Performance auditor**: metric-driven with reproducible benchmarks
- Every finding backed by profiling data, not opinion
- Provide before/after metrics (or baseline + projected)
- Include exact commands to reproduce measurements
- Never report "feels slow" without measurements

**Brainstorm agent**: scoped ideation with impact/effort assessment
- Scope budget: maximum N proposals (prevents unbounded lists)
- Every proposal includes effort + impact + trade-offs
- Rank by impact/effort ratio
- Separate ideation from evaluation (diverge then converge)

#### Orchestrator Quality Bar for Sub-Agent Output

When a sub-agent returns output, the orchestrator scores it before proceeding:

| Dimension | Pass (2) | Marginal (1) | Fail (0) |
|-----------|----------|--------------|----------|
| Schema compliance | Matches output-format exactly | Minor deviations | Missing sections |
| Evidence quality | All claims have file:line or URL | Some claims unsourced | Assertions without evidence |
| Scope adherence | Stays within boundaries | Minor scope creep | Significant out-of-scope |
| Completeness | All task requirements addressed | Most addressed | Key requirements missing |
| Actionability | Output is immediately usable | Needs minor interpretation | Requires significant rework |

Minimum passing score: 8/10. Score 6-7: request specific corrections (max 1 retry). Below 6: re-spawn with revised prompt. Do not report scores to the user — this is internal quality control.

#### Guardrail Simplicity Rules

Complex guardrails reduce performance (TurboDraft production data). Rules:
- Maximum 5 items per boundary tier (more causes selective attention)
- Each boundary item is one sentence (compound rules get partially followed)
- No conditional boundaries ("If X then never Y") — conditions introduce ambiguity
- If you need more than 5 rules, decompose into multiple agents instead

#### Prompt Anti-Patterns

Things to NEVER do in forge pipeline prompts:

| Anti-Pattern | Why It Fails | Source |
|-------------|--------------|--------|
| "You are an expert {role}" preamble without behavioral instructions | Role prompting has no measurable effect on accuracy. Wastes tokens | Schulhoff meta-analysis |
| "Think step by step" on all tasks | CoT degrades performance up to 36.3% on pattern recognition | ICML 2025 |
| Dumping full project context into sub-agent prompts | Context rot: 20-50% accuracy drop at large context sizes | Chroma, TACL 2024 |
| "You MUST use tools", "ALWAYS call a tool" | Claude 4.6 overtriggers, making unnecessary tool calls | Practitioner reports |
| Burying the task in the middle of a long prompt | Lost-in-the-middle: 30%+ degradation | Liu et al., TACL 2024 |
| Vague constraints ("be efficient") | Explicit constraints produce 9x less output variance | Production data |
| "Don't do X" as primary instruction style | Positive framing outperforms negative framing | Vendor guidance |
| Loading all steering files at spawn time | Violates progressive disclosure; wastes context budget | Anthropic, Manus |
| More than 3 few-shot examples | Diminishing returns after 2; increasing context cost | Production data |
| Complex conditional guardrails | Compound rules are partially followed or ignored | TurboDraft |
| Review prompts without confidence thresholds | Overcorrection bias: excessive false positives | arXiv 2602.16741 |
| Step-by-step procedures for frontier model builders | End-state descriptions outperform on Claude 4.6 | Spotify, SWE-bench |

#### Human Steering File Formatting

Apply prompt engineering principles to the files humans write and agents read:

**FORGE-STATUS.md** — YAML frontmatter for metadata, current state in first 5 lines (critical info at start), completed tasks in `<details>` (progressive disclosure), tables for structured data:
```markdown
---
milestone: 3
phase: build
updated: 2026-03-03T14:30:00Z
---
## Current State
Milestone 3 (API Layer), Phase: Build. 4 of 7 tasks complete.
Blocked on: Redis connection pooling (Task 3.5).
Next action: Resolve Redis config, then continue.
```

**SUGGESTIONS.md** — Decision checkboxes for human interface, structured per-suggestion format with impact/effort/rationale, sorted by confidence (highest first):
```markdown
### S-001: Add circuit breaker to external API calls
- **Impact:** high | **Effort:** medium | **Confidence:** 0.85
- **Rationale:** {evidence-backed justification}
- **Trade-off:** {what you give up}
- **Decision:** [ ] approve  [ ] reject  [ ] defer
```

**FORGE-MEMORY.md** — Sections for architectural decisions (stable), failed approaches (prevent re-trying dead ends), patterns learned (reusable). Each entry with date, context, decision, alternatives rejected. Under 3K tokens enforced by aggressive deduplication.

### Platform Detection and Conditional Paths
Skills MUST detect which platform they are running on and branch accordingly:
- **Claude Code detection**: check for `Agent` tool availability, `TeamCreate` tool, or `EnterWorktree` tool. If any exist → Claude Code
- **Codex detection**: check for `spawn_agent` function availability or presence of `AGENTS.md` at project root. If found → Codex CLI
- **Fallback**: if neither detected, assume Claude Code (more common) and log a warning

Platform-specific behavior:
- **Build agent isolation**: Claude → worktrees (`isolation: "worktree"` or `EnterWorktree`). Codex → file ownership scoping only (no worktree equivalent)
- **Practices guide loading**: Claude → auto-inject may load Layer 0 skills. Codex → MUST read Layer 0 SKILL.md explicitly (the only path)
- **Context overflow recovery**: All platforms → auto-compaction is the primary mechanism (agent cannot prevent it). CLAUDE.md survives verbatim on Claude Code; AGENTS.md is the Codex equivalent. Both contain `## Forge Pipeline State` with re-read instructions. State files on disk (FORGE-HANDOFF.md, FORGE-STATUS.md, TODO.md) provide recovery context after compaction
- **Teams vs multi-agent**: Claude → use TeamCreate/SendMessage for coordinated work. Codex → use spawn_agent/send_input for independent work

### AGENTS.md Requirements (Codex)
For Codex, AGENTS.md is the skill discovery mechanism. The implementing agent MUST:
1. Add entries for all 5 forge-* skills to AGENTS.md
2. Include explicit cross-references: forge-research and forge-builder entries must mention "read forge-claude-teams or forge-codex-multiagent for platform practices"
3. forge-orchestrator entry must mention both Layer 1 skills

This is unnecessary for Claude Code (auto-inject + description matching handles discovery) but harmless to include.

### Queue-Codex Integration
forge-codex-multiagent documents shared patterns from queue-codex (state persistence, phase gates, output signals, branch discipline) but the two systems are NOT directly coupled. Both use the same patterns independently.

### Implementation Order
Skills MUST be implemented in layer order (dependencies first):
1. **Layer 0**: forge-claude-teams + forge-codex-multiagent (can be parallel — no dependency between them)
2. **Layer 1**: forge-research + forge-builder (can be parallel — both reference Layer 0 but not each other)
3. **Custom agents**: forge-adversarial-reviewer, forge-build-worker, forge-research-worker, forge-performance-auditor (depend on Layer 0 practices for context handoff patterns)
4. **Layer 2**: forge-orchestrator (depends on both Layer 1 skills + custom agent definitions)

Within each layer, skills that reference Layer 0 must verify the Layer 0 SKILL.md files exist before adding `read` instructions.

### Naming Convention
All skills use the `forge-` prefix. Skill directories:
- `.claude/skills/forge-orchestrator/`
- `.claude/skills/forge-research/`
- `.claude/skills/forge-builder/`
- `.claude/skills/forge-claude-teams/`
- `.claude/skills/forge-codex-multiagent/`

Custom agent definitions (bundled with forge-orchestrator, installed to `.claude/agents/`):
- `.claude/agents/forge-adversarial-reviewer.md`
- `.claude/agents/forge-build-worker.md`
- `.claude/agents/forge-research-worker.md`
- `.claude/agents/forge-performance-auditor.md`

### Pattern Sources
Architecture follows a hybrid of:
- **Droid structure**: orchestrator-worker-validator triangle, milestone-gated validation, quality signals over human checkpoints
- **User's proven patterns**: fan-out with self-review, ownership scoping, adversarial challenge, planning-first invariant

### Exit Conditions
- **Milestone gate**: explicit pass criteria defined per milestone
- **Diminishing returns**: last cycle produced fewer than 10% new actionable findings compared to the previous cycle (measured by count of new issues/improvements identified). "Actionable" = requires a code change, not just an observation
- **Maximum iterations**: 2 retries per quality gate, 3 iterations per adversarial plan review, 3 depth cycles per research campaign
- **User intervention**: user can stop at any time; orchestrator saves state to FORGE-STATUS.md
- **Global circuit breaker**: orchestrator tracks total agent spawns and total milestones. Defaults:
  - Max 10 milestones per orchestration run
  - Max 50 total agent spawns per run (across all milestones)
  - If either limit is hit: save state, present summary to user, ask to continue or stop
  - These are safety caps, not targets. Most runs should complete well below them

### Security: Rule of Two
For any autonomous agent in the forge pipeline, apply the **Rule of Two** (Meta AI / Simon Willison): an agent must satisfy no more than two of:
- (A) Process untrustworthy inputs (web content, external APIs)
- (B) Access sensitive systems or private data (production configs, credentials)
- (C) Change state or communicate externally (write files, push code, send messages)

If all three are needed, require human approval or a fresh context window to separate the operations. This is architectural, not defensive — no reliable prompt injection defense exists (12/12 published defenses bypassed at >90% success rates).

**Practical application**: Research agents (A: web content + B: read codebase) should NOT also have write access to production code (C). The forge-research-worker custom agent enforces this via tool restrictions (no Write/Edit tools). Build workers (B: codebase access + C: write files) should NOT also process untrusted web content (A) — they receive distilled research findings from the orchestrator, not raw web content.

### Git Ignore Policy for Forge Artifacts
On first run, add to `.git/info/exclude` (local-only, does not pollute .gitignore):
```
architect/agent-contexts/
architect/review-findings/
FORGE-STATUS.md
FORGE-HANDOFF.md
DEFERRED-CHANGES.md
HUMAN-INPUT.md
MISSION-CONTROL.md
```
These files are git-ignored (not committed) but **kept on disk** between sessions. They persist for orchestrator resumption and cross-session continuity — they are not ephemeral in the sense of being deleted. The truly ephemeral files (agent-contexts/, review-findings/, DEFERRED-CHANGES.md) are cleaned up in the Cleanup step.

### Custom Agent Definitions (Claude Code)

The forge pipeline uses a **hybrid architecture**: skills for orchestration and knowledge (Layer 0-2 SKILL.md files), custom agent definitions (`.claude/agents/`) for isolated execution workers.

**Why custom agents for workers**: Custom agents run in separate context windows with architectural tool guarantees (not advisory). A research agent that fetches 50 web pages doesn't pollute the orchestrator's context. A reviewer with `tools: Read, Grep, Glob` genuinely cannot modify files. Workers with `isolation: worktree` get their own copy of the repo.

**Key constraint**: Custom agents (`.claude/agents/` definitions) cannot spawn sub-agents — only the main thread can. This means the orchestrator (running as skill in the main thread) must spawn all agents directly. For the parallelized serial threads model, each "thread" is an Agent tool sub-agent (general-purpose type, which retains Agent tool access and CAN spawn further sub-agents), not a custom agent. Custom agents are used for leaf-level workers within threads.

**Agent definitions to create** (in `.claude/skills/forge-orchestrator/agents/` — copied to `.claude/agents/` during installation):

| Agent | Purpose | Tools | Isolation |
|-------|---------|-------|-----------|
| `forge-adversarial-reviewer` | Critical review: find flaws, gaps, security issues | Read, Grep, Glob, Bash | none (read-only) |
| `forge-build-worker` | Implementation with file ownership scope | Read, Write, Edit, Bash, Grep, Glob | worktree |
| `forge-research-worker` | Web research and codebase exploration | Read, Grep, Glob, Bash, WebSearch, WebFetch | none (read-only) |
| `forge-performance-auditor` | Run tests, benchmarks, profile performance | Read, Bash, Grep, Glob | none (read-only) |

Each agent definition is a Markdown file with YAML frontmatter:
```yaml
---
name: forge-adversarial-reviewer
description: Critical reviewer for code, plans, and prompts. Finds flaws, gaps, ambiguities, security issues. Use proactively after drafting code, plans, or specifications.
tools: Read, Grep, Glob, Bash
model: inherit
---
```
System prompt follows the adversarial reviewer contract from Prompt Engineering Standards: confidence-gated (>80% threshold), evidence-required (file:line + code snippet), severity-confidence matrix (BugBot pattern), explicit exclusion of style preferences and theoretical concerns, mandatory positive observations. Overcorrection bias mitigated per arXiv 2602.16741 findings.

**All custom agents use `model: inherit`** — inheriting the main session's model. This aligns with the zero-sacrifices model fidelity requirement. The `model` field exists for users who explicitly want to override this for cost optimization (their choice, not ours).

**Codex equivalents**: For Codex, create parallel TOML definitions in `.codex/config.toml` + `agents/` directory. Codex has coarser tool restrictions (`sandbox_mode: "read-only"` or full) — accept this limitation for cross-platform support.

**When to use custom agents vs Agent tool sub-agents**:
- Custom agents: leaf-level workers that need tool restrictions and context isolation (reviewers, auditors, focused builders)
- Agent tool sub-agents (general-purpose): thread coordinators that need to spawn further sub-agents within their thread

### Compound Learning

After each milestone (and at orchestration completion), the orchestrator runs a **compounding step** — codifying learnings from the current cycle into persistent project context. This is the key differentiator between a system that repeats the same mistakes and one that gets smarter with each cycle.

**What to compound** (after each milestone):
1. **CLAUDE.md** — update conventions, patterns, or decisions discovered during this milestone
2. **TODO.md** — update with deferred items, discovered dependencies, lessons learned
3. **SUGGESTIONS.md** — consolidate new suggestions from this milestone's review agents
4. **Test infrastructure** — any new test patterns or fixtures created during this milestone should be documented for reuse

**What NOT to compound**: Ephemeral coordination state (agent contexts, review findings, deferred changes) — these are cleaned up, not persisted.

**Minimum-signal gate** (from OpenAI Codex memory system): Before persisting any learning, ask: "Will a future agent plausibly act better because of what I write here?" If no, discard. This prevents memory pollution — most agent outputs are situational, not generalizable. Only high-signal entries survive.

**Cross-session learning**: Maintain a `FORGE-MEMORY.md` file that accumulates patterns, decisions, and lessons across forge runs (not just within one run). At the end of each orchestration:
1. Extract high-signal entries from this run's learnings (minimum-signal gate)
2. Merge into FORGE-MEMORY.md with deduplication
3. Future forge runs read FORGE-MEMORY.md during intake (Step 1a)
This implements the A-MEM pattern (NeurIPS 2025) — connected knowledge networks at 1,200-2,500 tokens outperform raw history dumps at 16,900 tokens. FORGE-MEMORY.md is kept under 3,000 tokens by aggressive deduplication and pruning of superseded entries.

**Update strategy: incremental deltas, not full rewrites** (ACE paper, arXiv 2510.04618). When updating FORGE-MEMORY.md: append new entries, update existing entries in-place, deduplicate by semantic similarity. Never regenerate the entire file — iterative full rewrites cause "context collapse" where detailed knowledge erodes over time. The ACE framework showed incremental deltas achieve +10.6% improvement over full-rewrite baselines while reducing latency by 86.9%.

**The compounding loop** (runs at milestone boundary):
1. Collect: gather all review findings, improvement suggestions, and deferred items from the milestone
2. Classify: bug fix (done) | improvement (done) | new feature (SUGGESTIONS.md) | convention (CLAUDE.md) | task (TODO.md)
3. Persist: write classified items to their target files
4. Verify: quick self-check that persisted items are accurate and non-redundant

This is inspired by the Compound Engineering pattern (Every.to) — the principle that each unit of engineering work should make subsequent units easier, not harder. Empirically, teams using explicit compounding steps report 5x productivity multipliers.

### Design Justification (Key Research Metrics)

The architectural decisions in this specification are grounded in empirical research:

| Finding | Source | Implication for Forge |
|---------|--------|----------------------|
| Centralized coordination: +80.9% on parallelizable tasks | Google/DeepMind 2025 (tested on GPT-5, Gemini 2.5 Pro, Claude 4.5) | Orchestrator as central coordinator, not peer-to-peer |
| Multi-agent on sequential reasoning: -39% to -70% | Google/DeepMind 2025 (same study, near-frontier models) | Sequential within threads, parallel only across independent milestones |
| Error amplification: 17.2x (independent) vs 4.4x (centralized) | Google/DeepMind 2025 (architectural property, model-agnostic) | All agents report to orchestrator, not to each other |
| Multi-agent vs single-agent on research: +90.2% | Anthropic 2025 (Opus 4 + Sonnet 4; Opus 4.6 Agent Teams likely improves on this) | forge-research uses multi-agent, not single-agent research |
| 37% specification / 31% coordination / 31% verification failures | MASFT, Berkeley 2025 (tested on GPT-4/4o and Claude-3; pattern holds with better models) | 5-component context handoff, file ownership, merge protocol, validation gates |
| Token usage: multi-agent = 15x single-agent | Anthropic 2025 | Custom agents for context isolation, not all work in main thread |
| System design yields 80% vs 35% from scaling model | Berkeley 2024 (reinforced by all 2025-2026 data; Cursor, Google, Anthropic all validate) | Architecture matters more than model choice |
| Lusser's Law: per-step quality drops compound exponentially in chains | Engineering reliability (illustrative: 3% per-step → 22% at 10 agents; actual rates vary by task) | Minimize agent chain length, validate between handoffs |
| Agent drift accelerates over time | Agent Drift, arXiv 2026 (measured on GPT-4/Claude-3; Opus 4.6 likely shows lower absolute rates but acceleration pattern persists) | Fresh context windows over compaction; don't let agents accumulate indefinitely |
| Separated review: 40-60% quality improvement over self-review | ASDLC adversarial code review | Review agents must run in fresh context with spec+diff only, never builder's history |
| Tactical prompt fixes achieve only 14% improvement | MASFT, Berkeley 2025 | Structural solutions (architecture, coordination) matter more than prompt tweaks |
| A-MEM: 2x performance at 7x fewer tokens for cross-session memory | NeurIPS 2025 (tested across 6 models; model-agnostic architectural principle) | FORGE-MEMORY.md with structured, deduplicated entries under 3K tokens |
| Focused compressed context outperforms raw context dumps | Anthropic context engineering 2025 (Opus 4.6's 1M context narrows but doesn't eliminate this gap) | Handoff docs under 2K tokens; compress aggressively |
| Restart fresh > continue iterating for failed agents | Devin Agents 101 | Always spawn fresh on failure; never try to recover crashed contexts |
| Cursor hierarchical planner-worker: validated at scale | Cursor Jan 2026 (1,000 commits/hr, 10M tool calls) | Orchestrator-worker hierarchy works at massive scale |
| Compaction quality degrades after 2+ cycles | Amp production data 2025; Codex CLI issues #10346, #8481, #5799; Claude Code issue #6004 | Continuous state persistence to disk; CLAUDE.md anchor survives compaction verbatim |
| Agent cannot kill/restart itself | Claude Code #19877, #12665, #16440; Ralph Wiggum plugin #125, PR #126 failed | Design for compaction survival, not escape. External restart is a bonus, not primary mechanism |
| CLAUDE.md survives compaction verbatim (re-read from disk) | Claude Code confirmed behavior; Issue #14258 discussion | CLAUDE.md as anchor with `## Forge Pipeline State` re-read instructions |
| Agent may ignore post-compaction re-read instructions | Claude Code Issue #13919 (training bias) | Multiple mitigations: prominent CLAUDE.md section + self-describing state files + optional SessionStart hook |
| Anthropic: "Compaction isn't sufficient" for multi-window work | Anthropic "Effective Harnesses" 2025 | Sub-agent delegation + disk-based state persistence, not compaction |
| Gemini three-phase compression: truncate → summarize → verify | Gemini CLI source (chatCompressionService.ts) | Most sophisticated approach, but still degrades; validates disk-based state |
| Handoff state file: ~600 tokens vs re-discovery cost ~10K+ tokens | Handoff skill evaluation (this project) | FORGE-HANDOFF.md maintenance cost << post-compaction re-discovery cost |
| Structured summaries score 3.70/5 vs freeform 3.44/5 for state preservation | Factory AI compression evaluation 2025 | FORGE-HANDOFF.md uses mandatory sections (prevents silent information loss) |
| Summary stacking: 3+ compaction rounds = ~30% context consumed by summaries | OpenClaw research, community consensus | Track compaction count; after 5, maximize sub-agent delegation |
| Lost-in-the-middle: 30%+ accuracy degradation for middle-placed information | Liu et al., TACL 2024 (peer-reviewed) | Objective first, task last in all sub-agent prompts |
| Explicit constraints: 0.8% vs 7.1% output variance (9x difference) | Production prompt engineering data | Every constraint must be specific and measurable |
| CoT hurts up to 36.3% on pattern recognition tasks | ICML 2025, 9 models tested | Selective CoT: use for reasoning, skip for structured tasks |
| Overcorrection bias: review agents flag false positives without confidence gating | arXiv 2602.16741 (LLM code review study) | >80% confidence threshold + file:line evidence requirement for all reviewers |
| End-state > step-by-step for frontier model builders | Spotify (1500+ PRs), SWE-bench winners | Builder prompts describe goal, not procedure |
| XML tags as prompt structure: endorsed by all three major vendors | Anthropic, OpenAI, Google official docs (cross-validated) | All forge prompts use XML-delimited sections |
| Context rot: 20-50% accuracy drop from 10K to 100K tokens | Chroma evaluation, 18 models tested | Sub-agent context budget: under 4K tokens, <40% utilization |
| Two-layer evaluation: deterministic checks + LLM judgment | BugBot production, multiple CI/CD systems | Run linter/tests first, then LLM reviewer on results + code |
| Temperature 0.0 for code generation | SWE-bench Verified winner (Refact.ai, 74.4%) | All build workers use temperature 0.0 |

### Inter-Agent Validation

Never pass raw agent output to the next agent without validation. Between every agent handoff:
1. Orchestrator receives agent output
2. Quick sanity check: is the output in the expected format? Does it address the task?
3. If malformed or off-topic: re-spawn agent with clarified instructions (max 1 retry)
4. If valid: extract relevant findings, discard noise, pass distilled context to next agent

This prevents the 17.2x error amplification found in independent multi-agent systems. The orchestrator acts as a quality filter between all agent boundaries.

### Cleanup
After orchestration completes:
- `architect/agent-contexts/` — delete (ephemeral coordination artifacts)
- `architect/review-findings/` — delete (serialized for context overflow recovery only)
- `DEFERRED-CHANGES.md` — delete (processed during run)
- Worktree branches — merged or deleted. Stale worktrees from failed runs: list with `git worktree list`, prune with `git worktree prune`
- FORGE-STATUS.md — keep (useful for next session resumption)
- FORGE-HANDOFF.md — keep (enables instant resumption if session is interrupted)
- SUGGESTIONS.md — keep (human review needed)
- HUMAN-INPUT.md — keep (human may have pending items for next run)
- MISSION-CONTROL.md — keep (human may have standing directives)
- FORGE-MEMORY.md — keep (cross-session learning, feeds into future forge runs)
- Research outputs in `architect/research/` — keep (reference material)

### Research Provenance and Recency

**Recency policy**: Prefer 2026 sources over 2025 sources. Treat 2024 and earlier as foundational only (principles, not specific numbers). When citing quantitative findings, note which models were tested. Architectural principles (coordination overhead, compounding errors, structured memory) are more durable than specific benchmarks.

**Evaluated and excluded**: Every.to's compound engineering plugin (github.com/EveryInc/compound-engineering-plugin). Evaluated critically: 9,735 stars, but 35K lines of markdown vs 2,495 lines of executable code (14:1 ratio). The "four phases" are prompts, not systems. 36K token context overhead when installed. Productivity claims are self-reported by the CEO of the media company selling the narrative. **Verdict: Moderate quality — genuine methodology, mediocre engineering.** Patterns worth learning from (knowledge capture workflow, per-project review config) have been absorbed into this spec's Compound Learning and FORGE-MEMORY.md sections. The plugin itself is not integrated — its value has been extracted.

**Compaction research** (Claude Code + Codex CLI + Gemini CLI source analysis + kill-and-restart feasibility): All three major agent CLIs implement compaction differently (Claude: server-side same-model; Codex: 90% trigger, loses all tool output; Gemini: three-phase with verification, 50% trigger). All three share the same fundamental limitation: quality degrades after 2+ compactions. Amp abandoned compaction entirely. Critically: the agent cannot kill and restart itself — `/clear`, `/compact`, Codex `/new` are all user-typed only. The Ralph Wiggum plugin (Anthropic official) accumulates context instead of resetting (Issue #125). Feature requests #12665, #16440 for agent-invocable fresh-context remain unimplemented. However, CLAUDE.md survives compaction verbatim (re-read from disk), making it the ideal anchor for post-compaction recovery instructions. This validates the forge pipeline's compaction-resilient state persistence design: continuous state files on disk + CLAUDE.md anchor.

**Handoff workflow evaluation**: Existing handoff/wrap skills provide battle-tested information schema (What Was Done, Current State, What's Next, Failed Approaches, Key Context) and design principles (complete-snapshot, Bootstrap Read Rule, token-budgeted signal selection). These patterns are extracted into FORGE-HANDOFF.md. The skills themselves are NOT adapted directly — too much human-interaction ceremony for autonomous use.

**Prompt engineering research** (4 independent research streams + adversarial cross-validation): TurboDraft production data (21 research files: fidelity ledger, silent quality bar, guardrail complexity trap, preset-specific contracts), agentic prompt engineering (ICML 2025 CoT study, Schulhoff meta-analysis on role prompting, Chroma context rot evaluation), multi-agent coordination prompts (Anthropic orchestrator-worker patterns, BugBot severity-confidence matrix, Block dialectical autocoding, SWE-bench winning strategies, Claude Code Agent Teams documentation, Addy Osmani spec-driven development), prompt format and structure (TACL 2024 lost-in-the-middle, vendor XML endorsement, explicit constraint variance). Adversarial cross-validation: ~60% of findings validated across multiple sources, ~25% single-source but plausible, ~15% with suspicious specific numbers treated as illustrative. Zero contradictions that were irreconcilable — all resolved as context-dependent (CoT task-dependent, step-by-step vs end-state domain-dependent, role prompting style-only). Key integration: Sub-Agent Prompt Template (XML-structured, 7-component), role-specific contracts, orchestrator quality bar, human steering file formatting, anti-pattern list.

**2026 developments to track**: Anthropic Agent Teams (Feb 2026) extends our subagent model with direct teammate-to-teammate communication. PostCompact hook (Issue #14258, actively discussed) would enable direct post-compaction context injection — if implemented, integrate as a primary recovery signal alongside CLAUDE.md anchor. Agent-invocable fresh-context (Issue #12665) would enable true kill-and-restart — if implemented, FORGE-HANDOFF.md structure supports it without modification. Cursor validated hierarchical planner-worker at 1,000 commits/hr scale (Jan 2026). These reinforce, not contradict, the spec's architecture.
