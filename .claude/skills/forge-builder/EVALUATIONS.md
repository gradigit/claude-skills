# Evaluations for forge-builder

## Scenario 1: Happy path — standalone build with directive (should-trigger, functional)

**Given** user invokes forge-builder with a clear build directive
**When** user says "forge build the authentication middleware for Express with JWT validation"
**Then**
- [ ] Skill activates and classifies input as directive (not inquiry)
- [ ] Platform detection runs and reads the correct practices guide
- [ ] Build phases execute in order: implement, self-review, test, improve, quality gate
- [ ] Quality gate criteria are checked (tests, lint, self-review, requirements, regressions)
- [ ] TODO.md is updated with phase completion status
- [ ] Completion summary generated listing what was built, improved, and deferred

## Scenario 2: Edge case — inquiry classification (should-trigger, analysis only)

**Given** user invokes forge-builder with an analysis question
**When** user says "how should we handle authentication in this project?"
**Then**
- [ ] Skill activates and classifies input as inquiry (not directive)
- [ ] Agent responds with analysis and recommendations only
- [ ] No files are created or modified
- [ ] No build phases are executed
- [ ] Agent waits for a follow-up directive before making changes

## Scenario 3: Should-NOT-trigger — research request

**Given** user needs to research a topic before building
**When** user says "research the best caching strategies for our API"
**Then**
- [ ] forge-builder does NOT activate
- [ ] forge-research activates instead (research is its domain)
- [ ] No build phases are executed

## Scenario 4: Performance — quality gate throughput (performance)

**Given** a build with 3 phases, each with test infrastructure
**When** all phases pass on first attempt
**Then**
- [ ] Each quality gate check completes in <30 seconds
- [ ] Self-improvement scan adds <2 minutes per phase
- [ ] Total build completes without hitting the 2-retry limit
- [ ] Git checkpoints are created after each passed gate
