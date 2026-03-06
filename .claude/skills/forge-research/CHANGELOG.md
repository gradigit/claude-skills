# Changelog

All notable changes to the forge-research skill.

## [1.1.0] - 2026-03-03

### Changed
- Added 4 hard GATE checkpoints (A-D) between workflow steps to enforce sequential completion
- Added Step Completion Protocol section explaining why gates exist and what each enforces
- Step 1: directive table must now be output visibly before proceeding
- Step 2: strengthened to MANDATORY with explicit "read the file, don't just acknowledge it" language
- Step 3: added MANDATORY label, minimum 2 hypotheses + 3 questions requirement, gate checkpoint
- Step 4: context handoff now requires XML format explicitly — plain-text prompts are prohibited
- Step 5: added GATE C checkpoint preventing skip to output writing
- Step 6: marked as NEVER optional with "skipping is #1 failure mode" callout; self-critique must be output visibly with all 5 points addressed
- Step 7: added explicit skip condition (only if adversarial review found no critical gaps)

### Context
Driven by evaluation of first production run (claude-queuer session). Agent skipped steps 2, 3, 6, 7 entirely and used plain-text handoffs instead of XML. Output quality was good but process compliance was poor (C+ grade). Gates are the primary enforcement mechanism since skills have no runtime validation.

## [1.0.0] - 2026-03-03

### Added
- Initial release — autonomous multi-agent research campaign skill
- 9-step procedural workflow: parse directive, platform detection, hypotheses, breadth phase, synthesis, adversarial challenge, depth phase, final synthesis, output
- Platform detection: Claude Code (TeamCreate/Agent) and Codex CLI (spawn_agent) with fallback
- Hypotheses and Questions to Resolve tracking as termination criteria
- Phase 1 (breadth): study sub-agents, codebase exploration agents, session log analysis agents
- Phase 2 (depth): targeted gap resolution with cross-referencing and deep crawl
- Adversarial challenge: self-critique checklist + forge-adversarial-reviewer agent integration
- Confidence scoring: high/medium/low with criteria per level
- Study skill integration with fallback to direct WebSearch/WebFetch
- Research quality standards: source priority, recency, cross-reference, SEO spam rejection
- Termination conditions: questions resolved, hypotheses judged, adversarial review clean, diminishing returns, max 3 depth cycles
- Output templates: standard (single-phase) and extended (multi-phase with verified/unverified/conflicts)
- Context handoff templates for sub-agents (5-component XML format)

### Context
Layer 1 capability skill — procedural workflow for autonomous research. Spawns study agents, codebase explorers, and adversarial reviewers. Can be invoked standalone or orchestrated by forge-orchestrator.
