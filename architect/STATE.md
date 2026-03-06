# Forge State
## Current Stage: handoff (Step 11 — artifacts saved, presenting handoff)
## Mode: 1
## Depth: full
## Categories Asked: [architecture, scope, constraints, agent-patterns, platform-specifics, model-selection, context-engineering, conflict-prevention]
## Categories Skipped: []
## Categories Remaining: []
## Steps Completed: [1-capture, 2-depth, 3-questionnaire, 4-research, 5-gap-analysis, 6-draft-v1, 7-self-critique, 8-sub-agent-challenge, 9-iterate, 10-save-artifacts]
## Steps Remaining: [11-handoff]
## Key Decisions:
- 5 skills + 4 custom agents: forge-orchestrator, forge-research, forge-builder, forge-claude-teams, forge-codex-multiagent + forge-adversarial-reviewer, forge-build-worker, forge-research-worker, forge-performance-auditor
- Layered + hybrid architecture: Layer 0 (practices) → Layer 1 (capabilities) → Layer 2 (orchestrator) + custom agents for isolated workers
- Option C invocability: user-invocable: true + explicit refs from Layer 1 for cross-platform reliability
- Hybrid pattern source: Droid structure + user's proven patterns
- Hybrid exit condition: milestone gates + diminishing returns + Questions to Resolve
- Batch approval: SUGGESTIONS.md, never pause
- Cross-CLI: graceful degradation
- Study: spawn as sub-agent, not wrap
- Builder: auto-detect input with freshness check (standalone) / direct plan (orchestrated) + Directive vs Inquiry classification
- Queue integration: shared patterns in practices guide, not coupled
- Sub-agent context: 5-concern/7-XML-tag handoff template with role-specific prompt contracts and structured output schemas
- Context persistence: disk for workers/validators, ephemeral for short-lived
- Model selection: fidelity over cost, workers inherit main model, zero exceptions
- Conflict prevention: pyramid (read-only safe → worktrees+ownership → never same file)
- Parallelism: default sequential, 2-3 parallel build threads, 3-5 for read-only review within threads
- Pipeline pattern: parallelized serial threads (parallel pipelines, each internally sequential)
- Platform detection: check for platform-specific tools, conditional behavior paths
- Global circuit breaker: max 10 milestones, max 50 agent spawns per run
- Write ownership: only orchestrator writes to shared files (SUGGESTIONS.md, FORGE-STATUS.md, FORGE-HANDOFF.md)
- Compound learning: after each milestone, codify learnings with minimum-signal gate
- Cross-session memory: FORGE-MEMORY.md with incremental delta updates (ACE pattern)
- Review mandate: fresh context windows for all reviews, spec+diff only, no builder history
- Error recovery: restart fresh > continue iterating (for sub-agents); compaction survival for orchestrator
- Quality gates: "Validation is the only path to finality" (Gemini mandate)
- Per-step success criteria: every milestone step has concrete verification conditions
- Complexity-adaptive planning: simple milestones skip detailed planning
- Progress narration: human-readable notes before each action batch
- Every.to compound plugin: evaluated and excluded (moderate quality, patterns absorbed, plugin not integrated)
- Research recency: 8/10 findings still valid, 2 partially outdated in numbers (not direction), specific corrections applied
- Context recovery: compaction-resilient state persistence — CLAUDE.md anchor (survives verbatim) + continuous state files on disk
- Agent CANNOT kill-and-restart itself: confirmed across all CLIs (#19877, #12665, #16440, Ralph Wiggum #125)
- CLAUDE.md survives compaction verbatim: re-read from disk, contains ## Forge Pipeline State with re-read instructions
- Degradation-recovery cycle: each compaction degrades, each re-read from disk recovers meaningful state
- Handoff workflow: extraction not adaptation — reuse information schema and design principles, build new lightweight mechanism
- FORGE-HANDOFF.md: compaction survival file + external restart enabler, ~600 tokens per checkpoint
- SessionStart hook with compact matcher: secondary signal for post-compaction recovery (not primary — reliability issue #15174)
- Known reliability risk: agent may ignore post-compaction re-read instructions (Issue #13919, training bias)
- Prompt engineering standards: XML structure, information ordering (objective first/task last), explicit constraints, positive framing, context budget rules, selective CoT, neutral tool guidance
- Sub-agent prompt template: 7-tag XML (objective, context, output-format, tools, boundaries, quality-bar, task) instantiating 5 conceptual concerns
- Role-specific prompt contracts: confidence-gated reviewers (>80%), spec-driven builders (temp 0.0), hypothesis-driven researchers, scoped brainstorm agents
- Overcorrection bias mitigation: confidence gating + evidence requirements (file:line) for all review agents
- Orchestrator quality bar: 5-dimension scoring (schema/evidence/scope/completeness/actionability), minimum 8/10
- Guardrail simplicity: max 5 items per boundary tier, no conditional boundaries
- Human steering formatting: YAML frontmatter + critical info at start + progressive disclosure
## Challenge Results:
- 34 issues found (4 CRITICAL, 10 HIGH, 16 MEDIUM, 4 LOW)
- All CRITICAL and HIGH issues resolved in prompt v2
- Key fixes: worktree fallback, Codex API verification, context overflow protocol, global circuit breaker, concurrent write prevention, platform detection, implementation order
## Research Completed: all (10 original + 14 new + 5 prompt engineering = 29 total)
## Research Streams (Step 9 iterations):
- System prompts analysis (Claude Code, Codex CLI, Gemini CLI): 8 patterns extracted
- Latest agentic best practices (30+ sources): 9 patterns extracted
- Compound agentic engineering (30+ papers/systems): 6 findings, confirms architecture
- Custom sub-agents vs skills: hybrid architecture adopted
- Every.to compound engineering plugin (critical evaluation): moderate quality, patterns absorbed
- 2025 research recency evaluation (10 findings checked against Opus 4.6/Codex 5.3/Gemini 3.1): 3 corrections applied
- Claude Code compaction internals (Piebald-AI, Hrishi decompilation, API docs, GitHub issues): compaction degrades after 2+ cycles
- Codex CLI compaction (open source, codex-rs/core/src/compact*.rs): 90% trigger, loses all tool output, compaction loop issues
- Gemini CLI compaction (open source, chatCompressionService.ts): three-phase truncate→summarize→verify, most sophisticated but still degrades
- Handoff workflow evaluation (read all handoff/wrap/syncing-docs skills): extraction not adaptation, Option C hybrid recommended
- Comparative compaction analysis (all 3 CLIs): compaction survival validated across all platforms
- Kill-and-restart feasibility: DEFINITIVELY NOT POSSIBLE from within agent CLI. Ralph Wiggum #125, PR #126 failed, #12665/#16440 unimplemented
- Post-compaction behavior: CLAUDE.md survives verbatim, ## Compact Instructions recognized, SessionStart hook exists but unreliable (#15174), agent may ignore re-read instructions (#13919)
- Compaction-resilient architecture synthesis: CLAUDE.md anchor + continuous state files + degradation-recovery cycle
- TurboDraft prompt engineering research (21 files): fidelity ledger, silent quality bar, guardrail complexity trap, preset-specific contracts
- Agentic prompt engineering (web research): CoT hurts 36.3% on pattern tasks, context rot 20-50%, role prompting no effect on accuracy, XML preferred
- Multi-agent coordination prompts (web research): orchestrator-worker delegation, BugBot confidence gating, Block dialectical autocoding, SWE-bench strategies, Agent Teams patterns
- Prompt format & structure (web research): lost-in-the-middle 30%+, XML cross-vendor, explicit constraints 9x less variance, structured output >99%
- Adversarial cross-validation: ~60% validated across sources, ~25% single-source plausible, ~15% suspicious numbers, zero irreconcilable contradictions
## Research Pending: none
