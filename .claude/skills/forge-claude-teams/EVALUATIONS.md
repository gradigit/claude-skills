# Evaluations for forge-claude-teams

## Scenario 1: Happy path — multi-agent build session (should-trigger, functional)

**Given** user is setting up a multi-agent build with Claude Code
**When** user says "set up agent teams for this build"
**Then**
- [ ] Skill activates (or is read by orchestrator)
- [ ] Context handoff template is followed (5 components)
- [ ] File ownership declared per agent
- [ ] Worktree isolation used for build agents
- [ ] Progress narration emitted between actions

## Scenario 2: Edge case — agent failure recovery (should-trigger, functional)

**Given** a sub-agent crashes during a build
**When** the orchestrator detects the failure
**Then**
- [ ] Fresh agent spawned (not retried)
- [ ] Failure context included in new agent prompt
- [ ] No attempt to recover crashed context

## Scenario 3: Should-NOT-trigger — Codex CLI multi-agent work

**Given** user is working in Codex CLI
**When** user says "set up multi-agent for this Codex project"
**Then**
- [ ] forge-claude-teams does NOT activate
- [ ] forge-codex-multiagent activates instead

## Scenario 4: Performance — context budget adherence (performance)

**Given** an orchestrator spawning 5 build workers using forge-claude-teams practices
**When** each worker receives its context handoff
**Then**
- [ ] Each spawn prompt is under 4K tokens
- [ ] No agent starts with >40% context utilization
- [ ] Worktree isolation adds <100ms to agent startup time
- [ ] All 5 agents produce output without context overflow
