# Changelog

All notable changes to the researching skill.

## [1.2.0] - 2026-02-10

### Added
- **Parallel subagent execution**: 4+ topics automatically spawn one subagent per topic, then run a synthesis pass to find cross-topic connections
- **Auto-selection by topic count**: 2-3 topics run sequentially (cross-topic context is valuable), 4-6 run in parallel subagents, 7+ suggest splitting into multiple `/study` calls
- **Execution strategy table**: Clear mapping from topic count to strategy with rationale
- **Per-topic subagent prompt template**: Inlines methodology, quality filters, cross-verification, and hypothesis tracking so each subagent is self-contained
- **Synthesis pass instructions**: Read all per-topic outputs, produce cross-cutting findings, unified hypothesis table, and synthesized executive summary
- **User override**: "sequential" forces single-session, "parallel" forces subagents even for 2-3 topics

### Context
Sequential research degrades on topic 4+ as context fills. Parallel subagents get fresh context per topic at roughly the same token cost, with a synthesis pass that explicitly looks for cross-topic connections (more reliable than hoping the sequential agent notices them mid-search).

## [1.1.0] - 2026-02-10

### Added
- **Multi-topic research mode**: Handles `/study A, B, C, D` with per-topic decomposition, cross-topic finding detection, and a Cross-Cutting Findings output section
- **Delegation mode**: When `/study` is used alongside agent teams, the skill loads into the lead's context as methodology, then gets embedded into a researcher agent's prompt with the full quality filter criteria, Self-Ask steps, and self-critique inlined
- **Multi-topic output template** in output-templates.md: per-topic sections (hypothesis, findings, recommendation, sources) plus cross-cutting findings and unified hypothesis assessment table
- **Execution mode detection** in Step 1: detects direct vs delegated, single vs multi-topic
- **Delegation prompt structure**: template showing how to construct a researcher agent prompt that preserves the full study methodology
- **Sizing guidance for multi-topic**: 2-3 topics as one session, 4-6 with parallel sub-questions, 7+ suggest splitting

### Context
The v1.0.0 skill was skipped entirely when `/study` was invoked alongside "use agent teams" in a compound instruction. The agent wrote an ad-hoc research prompt that lacked Self-Ask decomposition, breadth-first search, quality filters, and self-critique. These additions ensure the methodology survives delegation to teammate agents.

## [1.0.0] - 2026-02-05

### Added
- Initial release
- Two depth modes: quick (3-5 sources) and full (10+ sources with verification)
- Self-Ask question decomposition pattern
- Breadth-first search strategy (broad → narrow)
- Three-tier source quality filtering system
- Cross-verification requirement (2+ sources for claims)
- Hypothesis tracking with confidence levels
- Self-critique phase before finalizing
- Four output templates: quick, full, comparative, prior-art
- Progressive disclosure with quality-filters.md and output-templates.md

### Research Foundation
Based on:
- Anthropic's multi-agent research system (90.2% improvement over single-agent)
- Self-Ask prompting pattern (LearnPrompting)
- Triangulation methodology (Scribbr)
- Chain-of-Verification concept
- Claude 4.5 research prompting best practices
