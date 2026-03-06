---
name: forge-builder
description: "Autonomous building/coding skill with self-review, self-improvement, and quality validation loops. Classifies input as directive (build) or inquiry (analyze). Can be used standalone or orchestrated by forge-orchestrator. Invoke with /forge-builder [task]. Do NOT use for research — use forge-research instead."
license: MIT
metadata:
  version: "1.2.0"
  author: gradigit
  category: forge
  tags:
    - builder
    - autonomous
    - self-review
    - self-improvement
    - coding
  triggers:
    - "forge build"
    - "forge builder"
    - "autonomous build"
    - "build with review"
---

# Forge Builder

Autonomous building with self-review, self-improvement, and quality gates.

## Entry Point

Two modes of invocation:

**Orchestrated** (from forge-orchestrator): Skip auto-detect. Use the provided plan directly. Do NOT ask the user anything — the orchestrator has already established the plan. Proceed to Step 1 with the plan as input.

**Standalone** (direct user invocation): Classify the request first:

- **Directive** (unambiguous action): "Build the auth module", "Add caching to the API" — proceed with build
- **Inquiry** (analysis/advice): "How should we handle auth?", "What's the best caching strategy?" — respond with analysis only, do NOT modify files until a follow-up directive is issued

This classification prevents auto-implementing when the user is still exploring options.

For directives, auto-detect input:
1. Check for `architect/` directory with plan artifacts
2. If found: verify freshness — "stale" means `architect/` mtime is older than the most recent 3 commits, OR CLAUDE.md phase does not match TODO.md state
3. If stale or ambiguous: ask user — "Found architect/ from a previous iteration. Use it, start fresh, or describe what you want?"
4. If no `architect/`: accept direct instructions or run a quick structuring pass

## Workflow

```
- [ ] 1. Parse build directive              → produces: Goals/Constraints/Context extracted
- [ ] 2. Detect platform + read practices   → produces: platform name logged
  ── GATE A: directive parsed + practices read ──
- [ ] 3. Plan implementation approach       → produces: phased plan in TODO.md
  ── GATE B: plan visible before any code changes ──
- [ ] 4. Execute build phases               → per-phase: implement → review → test → improve → gate
- [ ] 5. New feature detection              → produces: SUGGESTIONS.md entries (if any)
- [ ] 6. Final validation                   → produces: completion summary
```

### Step Completion Protocol

**Every step must produce visible output before the next step begins.** GATE markers are hard checkpoints.

- **GATE A** (after Steps 1-2): You must have extracted goals/constraints AND read the practices guide. If you haven't read the practices guide file, STOP and read it now.
- **GATE B** (after Step 3): You must have a phased plan (in TODO.md or output). If you are about to write code without a plan, STOP — even simple tasks benefit from a brief phase list.

**Why gates matter:** Without them, the natural tendency is to skip directly from reading the task to writing code, bypassing platform detection (which governs isolation and conflict prevention) and planning (which prevents rework). The build phases (Step 4) have their own quality gates already — the risk is in the pre-build steps.

---

## Step 1: Parse Build Directive

**You MUST extract and output these before proceeding:**

- **Goals**: what must be built and what success looks like
- **Constraints**: technology, performance, compatibility requirements
- **Codebase context**: existing patterns, conventions, test infrastructure

Read CLAUDE.md and TODO.md if they exist. Use their conventions as binding constraints.

## Step 2: Platform Detection

**MANDATORY.** Detect the agent platform and read the practices guide BEFORE writing any code.

| Signal | Platform | Action |
|--------|----------|--------|
| Agent tool, TeamCreate, SendMessage, or EnterWorktree available | Claude Code | Read `.claude/skills/forge-claude-teams/SKILL.md` |
| spawn_agent, AGENTS.md, fork_context available | Codex CLI | Read `.claude/skills/forge-codex-multiagent/SKILL.md` |
| Neither detected | Fallback | Assume Claude Code, log warning: "Platform not detected, defaulting to Claude Code practices" |

**You MUST read the practices guide file** — it contains isolation methods, conflict prevention, and context handoff templates that govern how build agents are spawned. Log which platform was detected.

> **GATE A checkpoint**: Do not proceed to Step 3 unless you have (1) extracted goals/constraints from Step 1 and (2) read the practices guide file. If you skipped either, go back now.

## Step 3: Plan Implementation

**MANDATORY.** You must have a phased plan before writing any code — even for "simple" tasks. A brief 3-line phase list counts; no plan at all does not.

If a plan already exists (orchestrated mode or `architect/` directory), use it. Otherwise:

1. Break work into phases with clear milestones
2. Identify file ownership boundaries per phase
3. Define quality gates per milestone — what "done" means for each phase
4. Write the plan to TODO.md (or update existing TODO.md)

Keep phases small. Each phase should produce a working, testable increment.

> **GATE B checkpoint**: Do not proceed to Step 4 unless you have a phased plan (in TODO.md or output). If you are about to write code without any plan, STOP and create one now — even a 3-line phase list prevents rework.

## Step 4: Execute Build Phases

For each phase, execute these sub-steps in order:

### a. Implement

Write code changes. Sequential by default — parallelize only when phases are genuinely independent and own different files. If `forge-build-worker` is available (`.claude/agents/forge-build-worker.md` exists), spawn it for implementation in worktree isolation. Describe the end-state, not step-by-step procedure: "Build X that passes Y" is better than "First do A, then B, then C."

### b. Self-Review (or Adversarial Review)

**Self-review** (default for standalone use): Structured review of own changes against requirements.

**Adversarial review** (when orchestrated or for critical builds): If `forge-adversarial-reviewer` is available (`.claude/agents/forge-adversarial-reviewer.md` exists), spawn it with the diff and requirements for independent critique. Fresh-context review catches issues self-review misses.

Structured review of own changes against requirements:
- Does this satisfy the phase goals?
- Are there logic errors or missed edge cases?
- Do the changes follow existing codebase conventions?
- Are there any security or data-loss risks?

### c. Run Tests

If test infrastructure exists, run the relevant test suite. If no tests exist, skip this sub-step (do not fabricate test infrastructure unless the directive asks for it).

### d. Self-Improvement Scan

Scan the code just written for actionable improvements:

- **Performance**: obvious inefficiencies, unnecessary allocations, O(n^2) in hot paths
- **Quality**: better patterns available, clearer naming, reduced duplication
- **Error handling**: missing edge cases at external boundaries (I/O, API calls, user input)
- **Test coverage**: untested paths in modified code

### e. Implement Improvements

Apply improvements from the scan. Scope: **existing functionality only**. See [Improvement vs New Feature Boundary](#improvement-vs-new-feature-boundary) for the decision table.

### f. Quality Gate Check

ALL must pass (see [quality-gates.md](quality-gates.md) for details):

1. Tests pass (if infrastructure exists)
2. Lint/format clean (if configured)
3. Self-review finds no critical issues
4. Changes satisfy stated requirements
5. No regressions in existing functionality

### g. Gate Failure Protocol

If the gate fails: fix the issues, re-run the gate. Maximum 2 retries per phase. After the third failure, escalate to the user with:
- What failed
- What was tried
- Suggested next steps

### h. Update Progress

Mark the phase complete in TODO.md. If using git checkpointing, commit after each passed gate.

---

## Step 5: New Feature Detection

During implementation, you will discover potential features or enhancements not in the original plan. Classify each one:

### Improvement vs New Feature Boundary

| Action | Classification | What to Do |
|--------|---------------|------------|
| Performance optimization of existing code | Improvement | Implement directly |
| Refactoring for clarity | Improvement | Implement directly |
| Error handling at existing boundaries | Improvement | Implement directly |
| Tests for existing untested code | Improvement | Implement directly |
| Fixing inconsistencies in existing patterns | Improvement | Implement directly |
| New user-facing behavior | New feature | Save to SUGGESTIONS.md |
| New API endpoints or commands | New feature | Save to SUGGESTIONS.md |
| New integrations | New feature | Save to SUGGESTIONS.md |
| New configuration options | New feature | Save to SUGGESTIONS.md |
| Significant architectural changes | New feature | Save to SUGGESTIONS.md |

**When in doubt, save to SUGGESTIONS.md.** The cost of suggesting something the user implements is far lower than the cost of implementing something the user rejects.

For each suggestion saved to SUGGESTIONS.md:
1. Research the feature briefly
2. Draft an implementation plan
3. Assign a confidence score (1-5)
4. Write it using the format in [suggestions-template.md](suggestions-template.md)

## Step 6: Final Validation

1. Run the full test suite (if infrastructure exists)
2. Verify all TODO.md items are completed or documented as deferred
3. Generate a completion summary:
   - What was built
   - What was improved during self-improvement scans
   - What was deferred to SUGGESTIONS.md
   - Any remaining risks or open questions

---

## SUGGESTIONS.md Format

SUGGESTIONS.md is a **bidirectional async communication channel** — the agent writes suggestions, the human writes feedback. This allows human steering of autonomous development without interrupting the workflow. See [suggestions-template.md](suggestions-template.md) for the full template.

**Status lifecycle**:
1. Agent creates suggestion: `proposed`
2. Agent researches: `researched`
3. Agent drafts plan: `planned`
4. Agent self-reviews plan: `ready-for-review`
5. Human writes decision in `### Human Feedback`:
   - `approved` — agent implements in next build cycle
   - `rejected` — agent skips, leaves for reference
   - `needs-revision` + comments — agent refines, cycles back to `planned`
6. Agent implements approved suggestion: `implemented`

**Write ownership**: Only the main builder thread (or orchestrator) writes agent-authored sections. The `### Human Feedback` section is exclusively human-written — the agent reads it but never modifies it.

### Processing Human Feedback

At every milestone boundary and during the COMPOUND step, re-read SUGGESTIONS.md and check for human feedback:
- **Approved** (`ready-for-review` or `planned` with `approved` decision): promote to a new milestone or add to the next milestone's scope
- **Rejected**: update status to `rejected`, leave in file for reference. Do not re-suggest unless the human explicitly revises their decision
- **Needs-revision**: incorporate human comments into the plan, re-run self-review, update status back to `planned`
- **No feedback yet**: leave as-is. Do NOT block waiting for feedback — continue with other work

---

## Quality Gate Criteria

> "Validation is the only path to finality."

ALL must pass for a phase to be considered complete. See [quality-gates.md](quality-gates.md) for the full reference.

| Gate | Condition | Skip If |
|------|-----------|---------|
| Tests | All pass | No test infrastructure |
| Lint/Format | Clean output | No linter configured |
| Self-Review | No critical issues (broken functionality, security vulnerabilities, data loss risks) | Never skip |
| Requirements | Changes match stated goals | Never skip |
| Regressions | No existing functionality broken | Never skip |

Gate failure: fix, re-gate (max 2 retries), escalate to user.

---

## Long-Running Build Sessions

For builds spanning multiple milestones or exceeding context limits. See [long-running.md](long-running.md) for the full reference.

Key principles:
- **Single-feature focus**: one milestone or feature per build agent
- **Git checkpointing**: commit after each completed milestone
- **Compaction-resilient state**: persist state to FORGE-HANDOFF.md, TODO.md continuously
- **Test-first**: when infrastructure exists, write/update tests before implementation
- **Browser automation**: use browser automation tools (if available) for UI testing — this "dramatically improved performance" (Anthropic)

---

## Conflict Prevention (Build-Specific)

When forge-builder is orchestrated and multiple build agents run in parallel:

1. Each agent gets a structured **FILE SCOPE** declaration (own/read/deny) via context handoff
2. Agents MUST NOT modify files outside their FILE SCOPE own list
3. Out-of-scope changes needed: write to `DEFERRED-CHANGES.md` with the file path, the change needed, and why
4. The orchestrator processes deferred changes after the current phase completes
5. If multiple agents defer changes to the same file, the orchestrator reconciles all deferred changes together

**DEFERRED-CHANGES.md format**:
```markdown
## {file path}
- **Agent**: {agent name}
- **Change needed**: {description}
- **Reason**: {why this is needed for the agent's scope to work}
- **Priority**: {blocking | enhancement}
```

---

## Self-Evolution

Update this skill when:
1. **Quality gate criteria change**: new validation steps, new tools for automated checking
2. **Self-improvement patterns improve**: better heuristics for the improvement vs new feature boundary
3. **Build workflow changes**: new phases, reordered phases, or phases that should be skipped
4. **Platform API changes**: new isolation mechanisms, new checkpointing features

Current version: 1.1.0. See [CHANGELOG.md](CHANGELOG.md) for history.
