# Evaluations for forge-research

## Scenario 1: Happy path — autonomous research on a technical topic (should-trigger, functional)

**Given** user wants deep research on a technical topic
**When** user says "forge research the best approaches for implementing event sourcing in Python"
**Then**
- [ ] Skill activates
- [ ] Platform detected (Claude Code or Codex CLI) and practices guide read
- [ ] Hypotheses and Questions to Resolve list created before any agent spawns
- [ ] Phase 1 breadth agents spawned with proper context handoffs (5-component XML)
- [ ] Study skill used for web research agents (or fallback logged if not installed)
- [ ] Phase 1 findings synthesized into findings table with confidence scores
- [ ] Adversarial challenge performed (self-critique at minimum)
- [ ] Phase 2 depth agents target gaps from adversarial review
- [ ] Final output written to `architect/research/{topic}.md` using output template
- [ ] All Questions to Resolve checked off or marked unresolvable
- [ ] All hypotheses have final status (confirmed/refuted/uncertain)

## Scenario 2: Edge case — orchestrated research with structured directive (should-trigger, functional)

**Given** forge-orchestrator invokes forge-research with a structured XML directive
**When** the directive arrives with `<task>`, `<context>`, `<scope>`, `<boundaries>`, `<output-contract>` tags
**Then**
- [ ] Skill activates from orchestrator invocation
- [ ] Directive parsed correctly — topic, questions, scope, constraints, output path extracted from XML
- [ ] Output written to path specified in `<output-contract>`, not the default path
- [ ] Research scope respects `<boundaries>` — out-of-scope topics not investigated
- [ ] Results returned in format suitable for orchestrator consumption

## Scenario 3: Should-NOT-trigger — user asks to build or code something

**Given** user wants to implement, build, or write code
**When** user says "build me an authentication system" or "code a REST API"
**Then**
- [ ] forge-research does NOT activate
- [ ] forge-builder activates instead (or base Claude for simple coding tasks)

## Scenario 4: Should-NOT-trigger — simple factual question

**Given** user asks a simple factual question that doesn't need a research campaign
**When** user says "what is event sourcing?" or "explain the difference between REST and GraphQL"
**Then**
- [ ] forge-research does NOT activate
- [ ] Base Claude answers the factual question directly
- [ ] No research agents are spawned
- [ ] No hypothesis tracking or adversarial review is invoked

## Scenario 5: Performance — research termination efficiency (performance)

**Given** a research campaign with 5 initial questions
**When** all questions are resolved after 2 depth cycles
**Then**
- [ ] Research terminates without reaching the 3-cycle hard ceiling
- [ ] Diminishing returns detection triggers (<10% new info in last cycle)
- [ ] Total agent spawns stay under 15 for a 5-question campaign
- [ ] Final output is written within 3 minutes of last agent completing
