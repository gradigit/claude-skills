# Research: Alternatives to MCP Agent Mail & Build-vs-Buy Analysis

## Summary
For 2-5 agent forge pipelines, task decomposition (clear file ownership per agent) is strongly preferred over dynamic file locking. Industry evidence from Cursor (20 agents → 2-3 effective throughput under locking), CooperBench (2-agent cooperation ~50% worse than single agent), and Claude Code official guidance all converge on the same answer: decompose tasks to avoid overlap, don't coordinate during overlap. MCP Agent Mail is the most feature-complete existing solution but is massively oversized (31K lines, 31 dependencies) for our narrow needs (~2 features). If locking becomes necessary, a custom build (~250-300 lines, zero dependencies, Claude Code hooks-native) is preferable. The recommended path is: improve decomposition first (free), add warn-only scope guard if violations are observed (~50 lines), build advisory locks only if unavoidable overlap is proven (~200 lines).

## Key Findings

1. **No alternative MCP server matches Agent Mail's file reservation depth** — Multi-Agent Coordination MCP (AndrewDavidRivers, ~2K stars) is the closest lightweight alternative with task+dependency+auto-file-locking, but lacks glob patterns, TTL, staleness detection, and pre-commit guard. Other MCP coordination servers (Agent-MCP, Beads Village) are immature (<500 stars). confidence: high — sources: competitive analysis across 30+ tools

2. **MCP Agent Mail is ~31,000 lines Python with 31 dependencies** — massive surface area for ~2 features we need (file reservation enforcement + glob-pattern tracking). Bus factor = 1 (sole developer). confidence: high — source: codebase analysis

3. **Our actual needs reduce to 3 narrow tiers** — (1) PreToolUse scope guard ~50 lines, (2) JSON lock file + pre-commit guard ~200 lines, (3) git merge-tree check ~100 lines = ~300-400 lines total with zero new dependencies. confidence: high — source: requirements analysis against forge pipeline

4. **For 2-5 agents, task decomposition is strongly preferred over locking** — CooperBench (2026) shows 2-agent cooperation performs ~50% worse than single agent. Cursor abandoned locking for hierarchical decomposition. Claude Code docs: "Break the work so each teammate owns a different set of files." confidence: very high — sources: [CooperBench](https://cooperbench.com/), [Cursor blog](https://cursor.com/blog/scaling-agents), [Claude Code agent teams docs](https://code.claude.com/docs/en/agent-teams)

5. **PreToolUse hooks are the enforcement primitive** — can intercept Edit/Write calls and block by exit code 2 or JSON `permissionDecision: "deny"`. Hooks fire independently per agent process but can race on shared lock files — need OS-level mutex (mkdir on macOS, flock on Linux). confidence: very high — sources: [Claude Code hooks docs](https://code.claude.com/docs/en/hooks), [hooks guide](https://code.claude.com/docs/en/hooks-guide)

6. **Agent identity is NOT exposed to PreToolUse hooks** — no `CLAUDE_AGENT_NAME` or `CLAUDE_TEAMMATE_NAME` environment variable. Must be injected via SessionStart hook writing to `CLAUDE_ENV_FILE` or via SubagentStart `additionalContext`. Critical gap for any scope enforcement implementation. confidence: very high — sources: [hooks reference](https://code.claude.com/docs/en/hooks), [GitHub issue #17188](https://github.com/anthropics/claude-code/issues/17188)

7. **Industry convergence: worktree/branch isolation + task decomposition + PR-level merge** — every commercial tool (Codex, Copilot, Devin, Windsurf, Amp) uses branch-per-agent. Nobody does runtime file locking successfully at scale. confidence: very high — sources: product docs and blog posts

8. **Git-native coordination tools are emerging but immature** — TICK.md (Markdown-based coordination), Beads (JSONL in `.beads/`), Beads Village (`.reservations/`) store coordination state in the repo itself. All <500 stars, unproven at scale. confidence: medium — sources: GitHub repos

9. **We already have the hard parts** — worktree isolation (forge-claude-teams), static file ownership (context handoffs), agent spawning protocol (forge-orchestrator). Missing only: runtime enforcement of declared scope + dynamic negotiation for overlap cases. confidence: high — source: forge skill analysis

10. **Cursor's key lesson applies at our scale** — "Many improvements came from removing complexity rather than adding it." The integrator role for conflict resolution was removed because "it created more bottlenecks than it solved." Lock infrastructure adds complexity that may degrade rather than improve throughput for small teams. confidence: high — source: [Cursor blog](https://cursor.com/blog/scaling-agents)

11. **Lock file design is straightforward if needed** — JSON in `.claude/locks/`, `mkdir` as POSIX-portable mutex, TTL-based auto-expiry for crash recovery, SessionEnd hook for cleanup. ~200-300 lines including the pre-commit guard. confidence: high — sources: POSIX file locking patterns, [BashFAQ/045](https://mywiki.wooledge.org/BashFAQ/045)

12. **Warn-only scope guard is the minimum viable intervention** — PreToolUse hook that logs when an agent touches files outside its declared scope, without blocking. Provides data on whether overlap is actually happening before investing in locks. ~50 lines. confidence: high — source: hook pattern analysis

## Competitive Landscape

### MCP Coordination Servers
| Tool | Focus | Maturity | File Coordination |
|------|-------|----------|-------------------|
| MCP Agent Mail | File reservations + messaging | 1,760 stars, 8 releases | Glob patterns, TTL, staleness, pre-commit guard |
| Multi-Agent Coordination MCP | Task + dependency + auto-locking | ~2K stars | Auto file locking, simpler model |
| Agent-MCP (rinadelph) | Inter-agent communication | <100 stars | No file coordination |
| Beads Village | Git-native task tracking | <500 stars | `.reservations/` files |

### Commercial AI Coding Tools
| Tool | Coordination Approach | File Conflict Strategy |
|------|----------------------|----------------------|
| Cursor | Hierarchical Planner/Worker/Judge | Worktrees, decomposition, NO locking |
| Codex App | Branch-per-agent | PR-level merge |
| GitHub Copilot | Mission Control hierarchy | Workspace isolation |
| Devin | Single-branch sequential | N/A (single agent) |
| Sourcegraph Amp | Agent per codebase area | Decomposition |

### Git-Native Coordination
| Tool | Mechanism | Maturity |
|------|-----------|----------|
| TICK.md | Markdown task file in repo | Concept stage |
| Beads | JSONL in `.beads/` directory | Early (<500 stars) |
| git merge-tree | In-memory three-way merge prediction | Stable (git built-in) |

## Hypotheses

| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| H1: MCP Agent Mail is the best existing solution for forge file coordination | refuted | Massively oversized (31K lines vs ~300 needed). Multi-Agent Coordination MCP is simpler but still more than needed. Task decomposition may eliminate the need entirely. |
| H2: Custom build is viable and preferable to adopting MCP Agent Mail | confirmed with caveats | Viable (~300-400 lines) but depth research shows decomposition alone may suffice for 2-5 agents. Build only if decomposition proves insufficient in practice. |
| H3: Industry has converged on a standard approach | confirmed | Worktree isolation + task decomposition + PR-level merge. Runtime file locking is abandoned at scale. |

## Questions Resolved

- [x] Q1: What alternatives to MCP Agent Mail exist? — Multi-Agent Coordination MCP (closest), 30+ tools surveyed across 8 categories. None are better suited for our specific use case.
- [x] Q2: Which alternative best fits our forge pipeline? — None outperform improved decomposition for 2-5 agents. If locking needed, custom build > any existing tool.
- [x] Q3: What coordination patterns do commercial tools use? — Worktree isolation + hierarchical decomposition. Cursor explicitly abandoned locking.
- [x] Q4: Build vs buy? — Build, but only if decomposition proves insufficient. ~300-400 lines, zero dependencies, 3-5 days.
- [x] Q5: What enforcement primitive should we use? — PreToolUse hooks (Claude Code native). Can block Edit/Write calls. Race conditions solved with mkdir mutex.

## Recommended Path

### Tier 0: Better Decomposition (Do Now — Free)
- Make file ownership explicit in every forge-orchestrator context handoff
- Add file scope declarations to forge-build-worker agent definition
- Improve milestone decomposition to minimize file overlap between parallel agents
- **Cost**: 0 new lines of code, just better prompts
- **Expected impact**: Eliminates most accidental overlap

### Tier 1: Warn-Only Scope Guard (When Violations Observed — ~50 Lines)
- PreToolUse hook on Edit/Write that checks file path against agent's declared scope
- Logs violations but does NOT block — provides data on overlap frequency
- Requires solving agent identity gap (inject via SessionStart → CLAUDE_ENV_FILE)
- **Cost**: ~50 lines bash, 1-2 hours
- **Trigger**: Deploy Tier 0, observe if agents still violate scope in practice

### Tier 2: Advisory Locks + Enforcement (If Overlap Unavoidable — ~200-300 Lines)
- JSON lock file in `.claude/locks/` with mkdir mutex for atomic access
- Pre-commit guard that blocks commits conflicting with active reservations
- TTL-based auto-expiry (300s default) for crash recovery
- SessionEnd hook for cleanup
- **Cost**: ~200-300 lines bash/jq, 2-3 days
- **Trigger**: Tier 1 data shows frequent unavoidable file overlap

### Tier 3: Merge Prediction (If Merge Conflicts Frequent — ~100 Lines)
- `git merge-tree --quiet` check before merging worktree branches
- Surface predicted conflicts to orchestrator before they become actual conflicts
- **Cost**: ~100 lines bash, 4-8 hours
- **Trigger**: Merge conflicts halt the pipeline frequently enough to justify

### What NOT to Build
- MCP server (unnecessary complexity for hooks-native enforcement)
- Glob-pattern matching for reservations (simple path prefix is sufficient at our scale)
- Multi-signal staleness detection (TTL + SessionEnd cleanup is sufficient for 2-5 agents)
- AST-level region concurrency (no production system does this; wait for Kiro/Tree-sitter ecosystem to mature)

## Trade-Off Summary

| Approach | Complexity | Dependencies | Maintenance | Effectiveness (2-5 agents) |
|----------|-----------|-------------|-------------|---------------------------|
| Better decomposition (Tier 0) | None | None | None | High |
| Warn-only guard (Tier 1) | ~50 lines | None | Minimal | Medium (diagnostic) |
| Custom locks (Tier 1+2) | ~250-350 lines | None | Low | High (if overlap exists) |
| MCP Agent Mail | 31K lines | 31 Python deps | High (external) | High (overkill) |
| Multi-Agent Coordination MCP | ~5K lines | Node.js deps | Medium (external) | Medium |

## Gaps and Limitations

- No empirical data on forge-specific scope violation frequency — Tier 0 must be tested before deciding if Tier 1+ is needed
- Agent identity workaround (SessionStart → CLAUDE_ENV_FILE) is untested — may have edge cases with concurrent agent spawning
- mkdir mutex is POSIX-portable but less elegant than flock; performance under high contention unknown (unlikely concern at 2-5 agents)
- CooperBench results are for general coding tasks — forge-specific structured workflows with explicit handoffs may perform better than the general case
- Build estimates (3-5 days for Tier 1+2+3) may be optimistic if testing edge cases doubles the effort

## Sources

- [MCP Agent Mail (GitHub)](https://github.com/Dicklesworthstone/mcp_agent_mail) — production file reservation implementation
- [Multi-Agent Coordination MCP (GitHub)](https://github.com/AndrewDavidRivers/multi-agent-coordination-mcp) — lightweight alternative
- [Cursor: Scaling Long-Running Autonomous Coding](https://cursor.com/blog/scaling-agents) — locking failure evidence, hierarchical decomposition
- [CooperBench: Why Coding Agents Cannot be Your Teammates Yet](https://cooperbench.com/) — 2-agent cooperation ~50% worse than single agent
- [Claude Code: Agent Teams](https://code.claude.com/docs/en/agent-teams) — "Break the work so each teammate owns a different set of files"
- [Claude Code: Hooks Reference](https://code.claude.com/docs/en/hooks) — PreToolUse schema, blocking responses, environment variables
- [Claude Code: Hooks Guide](https://code.claude.com/docs/en/hooks-guide) — file protection hook example
- [GitHub Issue #17188](https://github.com/anthropics/claude-code/issues/17188) — request for session metadata env vars in hooks
- [BashFAQ/045](https://mywiki.wooledge.org/BashFAQ/045) — POSIX atomic operations (mkdir, symlink)
- [disler/claude-code-hooks-multi-agent-observability](https://github.com/disler/claude-code-hooks-multi-agent-observability) — multi-agent hook monitoring
- [Agentic Drift: It's Hard to Be Multiple Developers at Once](https://dev.to/helgesverre/agentic-drift-its-hard-to-be-multiple-developers-at-once-4872) — coordination overhead analysis
- [Google A2A Protocol](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — inter-agent communication standard

## Generated
- Date: 2026-03-04
- Workflow: forge-research v1.1.0 (continuation — alternatives + build-vs-buy analysis)
- Parent research: [agent-mail-coordination.md](agent-mail-coordination.md)
