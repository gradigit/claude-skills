# Research: Agent Mail-Based Inter-Agent Coordination for Conflict-Free Parallel File Editing

## Summary
Message-passing coordination for multi-agent file access is technically sound and already implemented (MCP Agent Mail). The critical insight is that advisory protocols alone fail because LLM agents degrade at multi-step coordination after ~12 turns — external enforcement (pre-commit guards, TTL-based lease expiry) is mandatory. The optimal architecture combines git worktree isolation (baseline), advisory file leases via MCP tools (intent signaling), `git merge-tree` for continuous merge prediction, and AST-level region boundaries for same-file concurrency. Current Claude Code SendMessage is too unreliable for coordination; MCP tools are the correct transport layer.

## Key Findings

1. **MCP Agent Mail already exists** — production implementation of advisory file leases with glob patterns, TTLs, multi-signal staleness detection, and git pre-commit guards. 1,760 GitHub stars, 8 releases, actively maintained. Operates as an MCP server compatible with both Claude Code and Codex CLI. confidence: very high — sources: [mcp_agent_mail](https://github.com/Dicklesworthstone/mcp_agent_mail), [mcpagentmail.com](https://mcpagentmail.com/)

2. **LLM agents fail at lock/release protocols** — Cursor ran hundreds of concurrent coding agents and documented catastrophic failure: agents forgot to release locks, acquired duplicates, and ignored lock requirements entirely. 20 agents degraded to 2-3 effective throughput. They abandoned locking for hierarchical coordination. confidence: very high — source: [Cursor: Scaling Long-Running Autonomous Coding](https://cursor.com/blog/scaling-agents)

3. **Multi-turn instruction degradation is the root cause** — 30-40% performance drop in multi-turn settings. Critical threshold at ~12 turns where agents show "accelerating degradation" including redundant operations and protocol violations. Advisory coordination requires exactly the kind of sustained multi-turn discipline that degrades. confidence: high — sources: [LLMs Get Lost In Multi-Turn Conversation](https://arxiv.org/pdf/2505.06120), [LoCoBench-Agent](https://arxiv.org/pdf/2511.13998)

4. **External enforcement is the solution** — Research consensus (AgentSpec ICSE 2026, Agent Behavioral Contracts) shifts from "train agents to follow protocols" to "enforce externally." MCP Agent Mail's pre-commit guard is exactly this pattern — blocks commits that violate others' reservations regardless of agent compliance. confidence: high — sources: [AgentSpec](https://arxiv.org/abs/2503.18666), [Agent Behavioral Contracts](https://arxiv.org/abs/2602.22302)

5. **No major multi-agent framework has built-in file coordination** — CrewAI, AutoGen, LangGraph, MetaGPT, OpenAI Swarm, ChatDev all lack file-level locking. Industry converged on git worktree isolation as the standard. confidence: very high — sources: framework docs and repos

6. **`git merge-tree` enables zero-side-effect merge prediction** — Three-way merge in memory, exit code signals clean/conflict. Supports batch mode via `--stdin`. Uber's SubmitQueue proved speculative merge validation at scale: 5% conflict rate at 2 concurrent changes escalates to 40% at 16. confidence: very high — sources: [git-merge-tree docs](https://git-scm.com/docs/git-merge-tree), [Uber SubmitQueue](https://www.uber.com/blog/bypassing-large-diffs-in-submitqueue/)

7. **AST-level region boundaries enable same-file concurrency** — Microsoft Research proved edits to different AST subtrees are associative (order-independent merge). Tree-sitter provides incremental parsing for region detection. Kiro ships AST-based editing with 34% fewer LLM calls and zero tool errors. confidence: high — sources: [MS Research 2015](https://www.microsoft.com/en-us/research/wp-content/uploads/2015/02/paper.pdf), [Kiro](https://kiro.dev/blog/surgical-precision-with-ast/), [tree-sitter](https://github.com/tree-sitter/tree-sitter)

8. **Claude Code SendMessage is unreliable for coordination** — File-based inbox with ~1s polling, at-most-once delivery, known message-loss bugs (marked read before delivery), no recipient validation, 10-30s typical round-trip. Sufficient for human-readable status updates but insufficient for lock coordination protocols. confidence: high — sources: GitHub issues [#25383](https://github.com/anthropics/claude-code/issues/25383), [#25135](https://github.com/anthropics/claude-code/issues/25135), [#23415](https://github.com/anthropics/claude-code/issues/23415)

9. **MCP tools are the correct transport** — MCP Agent Mail bypasses SendMessage entirely and exposes coordination as MCP tool calls. This works on both Claude Code and Codex CLI. The pre-commit guard is Git-native (platform-agnostic). confidence: high — source: MCP Agent Mail architecture

10. **CRDTs/OT are overkill for agent coding** — Agents produce batch edits at function/block granularity (seconds-to-minutes), not character streams (milliseconds). Advisory leases + merge prediction is the right complexity level. confidence: medium — sources: CRDTs vs OT analysis, [Weidner 2025](https://mattweidner.com/2025/05/21/text-without-crdts.html)

11. **Current forge pipeline has 4 coordination bottlenecks** — (1) Shared state file contention (orchestrator-only writes), (2) Deferred changes queuing up in DEFERRED-CHANGES.md, (3) Merge conflicts halting pipeline (manual user intervention), (4) Phase-sequential milestones blocked by learning propagation (CLAUDE.md patterns only available after COMPOUND step). confidence: high — source: forge skill file analysis

12. **Multi-agent failure rate is 41-86.7%** with ~79% from specification + coordination. Coordination failures specifically: 36.9%. Speed improvement from parallel agents is only ~1.3x. confidence: high — sources: [Augment Code](https://www.augmentcode.com/guides/why-multi-agent-llm-systems-fail-and-how-to-fix-them), [arxiv 2503.13657](https://arxiv.org/abs/2503.13657)

13. **Agents follow observable-state protocols better than ToM protocols** — LLM-Coordination benchmark (NAACL 2025) shows agents excel when coordination state is directly observable (file exists / doesn't exist) but struggle with Theory of Mind reasoning. File-based artifacts (JSON reservation files) are more reliable than purely message-based coordination. confidence: high — source: [LLM-Coordination (NAACL 2025)](https://aclanthology.org/2025.findings-naacl.448/)

14. **MCP Agent Mail's crash recovery is robust** — Three layers: TTL-based auto-expiry, multi-signal staleness detection (agent inactivity + mail silence + filesystem silence + git silence), and manual force-release. Does NOT rely on agents to release their own locks. confidence: very high — source: MCP Agent Mail source code analysis

## Hypotheses
| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| H1: Message-passing can replace static file ownership with dynamic, negotiated file locks | confirmed with caveats | MCP Agent Mail implements this. Advisory locks alone fail (Cursor evidence) — external enforcement (pre-commit guard) is mandatory. |
| H2: Agents can evaluate merge compatibility at region level for same-file concurrency | confirmed | `git merge-tree` for file-level, AST subtree boundaries for region-level (MS Research proof, Tree-sitter, Kiro). No production system combines all three yet. |
| H3: Existing Claude Code SendMessage is sufficient for agent mail coordination | refuted | At-most-once delivery, message-loss bugs, 10-30s latency. MCP tools are the correct transport. |
| H4: Mail-based coordination is slower than static ownership for most cases | confirmed | 3-5s minimum, 10-30s typical round-trip. Cursor: 20 agents → 2-3 effective throughput under locking. Only worthwhile for patterns impossible with static ownership. |
| H5: Distributed systems locking patterns have direct analogs for multi-agent coding | confirmed | Advisory leases, fencing tokens, TTL crash recovery, multi-signal staleness detection all map directly. |

## Questions Resolved
- [x] Q1: Frameworks use hub-and-spoke (CrewAI), conversation (AutoGen), shared state (LangGraph), pub-sub (MetaGPT), handoffs (Swarm). None have file coordination built in.
- [x] Q2: Claude Code SendMessage is file-based inbox (JSON array per agent), ~1s polling, filelock concurrency, messages injected as synthetic user turns.
- [x] Q3: Advisory leases preferred over mandatory locks. Fencing tokens critical for correctness. Three distributed failure modes (process pause, clock drift, network delay) all have agent analogs.
- [x] Q4: `git merge-tree --quiet` predicts conflicts without side effects. Uber proved speculative merge validation at scale. 5% conflict at 2 agents → 40% at 16.
- [x] Q5: AST subtree boundaries (MS Research associativity proof), Tree-sitter incremental parsing, LSP TextEdit non-overlapping constraint. Semistructured merge reduces conflicts ~34%.
- [x] Q6: 4 bottlenecks in current forge pipeline: shared state contention, deferred changes, merge conflicts halting pipeline, phase-sequential milestones.
- [x] Q7: CRDTs/OT overkill for agent coding. Advisory leases + merge prediction + AST regions = optimal hybrid.
- [x] Q8: At-most-once delivery, message-loss bugs, 10-30s typical latency. MCP tools bypass these issues.
- [x] Q9: 5 message types: state_update, deferred_change, acquire_lock/release_lock, discovery broadcast, merge_conflict proposal. MCP Agent Mail implements these as MCP tool calls.
- [x] Q10: MCP Agent Mail is the direct implementation. No framework has it built in. 1,760 stars, actively maintained.

## Recommended Architecture

### Layered Coordination Stack

```
Layer 4: AST-level region declarations (future)
         Tree-sitter parses function/class boundaries
         Agents declare "editing function X in file Y"
         → enables same-file concurrency

Layer 3: Continuous merge prediction
         Coordinator runs `git merge-tree` periodically
         against all agent branches
         → early conflict detection before commit

Layer 2: Advisory file leases (MCP Agent Mail)
         Agents call file_reservation_paths() via MCP
         TTL-based, auto-releasing, with staleness detection
         Pre-commit guard blocks conflicting commits
         → intent signaling + enforcement backstop

Layer 1: Git worktree isolation (current)
         Each build agent gets its own worktree/branch
         → baseline isolation, unchanged

Layer 0: Static file ownership (current)
         Context handoff declares file scope per agent
         → still the first line of defense
```

### Integration Path for Forge Skills

**Phase 1 — MCP Agent Mail integration (low risk, high value)**
- Install MCP Agent Mail as an MCP server for the forge pipeline
- Add `file_reservation_paths` calls to forge-build-worker before editing files
- Enable pre-commit guard on all agent worktrees
- No changes to forge-claude-teams or forge-codex-multiagent needed — MCP tools work on both platforms

**Phase 2 — Merge prediction (medium risk, medium value)**
- Add `git merge-tree --quiet` check to forge-orchestrator before merging worktree branches
- Surface predicted conflicts to the orchestrator before they become actual conflicts
- Reduces manual merge conflict resolution (currently halts pipeline)

**Phase 3 — AST-level region concurrency (high risk, high value, future)**
- Integrate Tree-sitter for function/class boundary detection
- Agents declare AST-level scopes instead of file-level scopes
- Enable 2+ agents on the same file targeting different functions
- Requires significant testing — no production system does this yet

### Design Principles (from research)

1. **Never trust agents to self-regulate** — use external enforcement (pre-commit guards, TTL expiry, staleness detection)
2. **Make coordination state observable** — file-based artifacts (JSON reservation files) over purely message-based protocols. Agents follow observable-state protocols better (NAACL 2025)
3. **Advisory first, enforce at commit** — don't block agents from working; block them from committing conflicting changes
4. **TTL everything** — every lease must have a bounded lifetime. Crash recovery through passive observation, not active heartbeats
5. **Git is the safety net** — merge conflicts are the ultimate correctness guarantee. Coordination reduces their frequency, not replaces them

## Gaps and Limitations
- No public case studies of MCP Agent Mail in production multi-agent fleets at scale
- MCP Agent Mail has bus factor = 1 (sole developer)
- AST-level same-file concurrency is theoretically proven but no production implementation for multi-agent coding exists
- Performance benchmarks comparing coordination overhead vs merge overhead vs sequential overhead don't exist
- Agent compliance research is for general LLMs — forge-specific agent compliance (with custom agent definitions + structured handoffs) may be better than the general case
- Codex CLI's `send_input` interaction model wasn't deeply analyzed for coordination protocol compatibility beyond MCP tool calls

## Sources
- [MCP Agent Mail (GitHub)](https://github.com/Dicklesworthstone/mcp_agent_mail) — production implementation of agent mail file coordination
- [MCP Agent Mail (website)](https://mcpagentmail.com/) — commercial companion and documentation
- [Cursor: Scaling Long-Running Autonomous Coding](https://cursor.com/blog/scaling-agents) — file locking failure evidence at scale
- [LLMs Get Lost In Multi-Turn Conversation (arxiv 2505.06120)](https://arxiv.org/pdf/2505.06120) — multi-turn degradation
- [LoCoBench-Agent (arxiv 2511.13998)](https://arxiv.org/pdf/2511.13998) — long-context agent benchmark
- [Context Rot (Chroma Research)](https://research.trychroma.com/context-rot) — context degradation research
- [AgentSpec (arxiv 2503.18666)](https://arxiv.org/abs/2503.18666) — runtime constraint enforcement
- [Agent Behavioral Contracts (arxiv 2602.22302)](https://arxiv.org/abs/2602.22302) — behavioral drift detection
- [Why Do Multi-Agent LLM Systems Fail? (arxiv 2503.13657)](https://arxiv.org/abs/2503.13657) — failure taxonomy
- [Augment Code: Why Multi-Agent Systems Fail](https://www.augmentcode.com/guides/why-multi-agent-llm-systems-fail-and-how-to-fix-them) — failure rates
- [LLM-Coordination (NAACL 2025)](https://aclanthology.org/2025.findings-naacl.448/) — coordination benchmark
- [git-merge-tree docs](https://git-scm.com/docs/git-merge-tree) — merge prediction primitive
- [Uber SubmitQueue](https://www.uber.com/blog/bypassing-large-diffs-in-submitqueue/) — speculative merge at scale
- [MS Research: AST-based Collaborative Editing (2015)](https://www.microsoft.com/en-us/research/wp-content/uploads/2015/02/paper.pdf) — region-level merge associativity
- [Kiro: Surgical AST-based Code Editing](https://kiro.dev/blog/surgical-precision-with-ast/) — production AST editing
- [Roo Code DAST (Issue #4730)](https://github.com/RooCodeInc/Roo-Code/issues/4730) — semantic anchoring proposal
- [tree-sitter](https://github.com/tree-sitter/tree-sitter) — incremental parsing infrastructure
- [Martin Kleppmann: How to do distributed locking (2016)](https://martin.kleppmann.com/2016/02/08/how-to-do-distributed-locking.html) — locking primitives taxonomy
- [Claude Code Agent Teams docs](https://code.claude.com/docs/en/agent-teams) — SendMessage architecture
- [OpenCode porting deep dive](https://dev.to/uenyioha/porting-claude-codes-agent-teams-to-opencode-4hol) — SendMessage internals
- [claude-code-teams-mcp](https://github.com/cs50victor/claude-code-teams-mcp) — SendMessage reimplementation
- GitHub issues: [#25383](https://github.com/anthropics/claude-code/issues/25383), [#25135](https://github.com/anthropics/claude-code/issues/25135), [#23415](https://github.com/anthropics/claude-code/issues/23415), [#29271](https://github.com/anthropics/claude-code/issues/29271) — SendMessage bugs
- [Merge evaluation (ASE 2024)](https://homes.cs.washington.edu/~mernst/pubs/merge-evaluation-ase2024.pdf) — semistructured merge ~34% reduction
- [LLM-Based Multi-Agent Systems for SE (ACM TOSEM)](https://dl.acm.org/doi/10.1145/3712003) — literature review
- [Google A2A Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — inter-agent protocol
- [CRDTs vs OT (HackerNoon)](https://hackernoon.com/crdts-vs-operational-transformation-a-practical-guide-to-real-time-collaboration) — collaborative editing comparison
- [LSP Specification 3.17](https://microsoft.github.io/language-server-protocol/specifications/lsp/3.17/specification/) — TextEdit constraint

## Generated
- Date: 2026-03-04
- Workflow: forge-research v1.1.0 (5 research agents: frameworks, distributed-locking, sendmessage-internals, forge-pipeline-analysis, agent-mail-deep-dive)
