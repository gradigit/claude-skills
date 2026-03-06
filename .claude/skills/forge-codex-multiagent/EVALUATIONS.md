# Evaluations for forge-codex-multiagent

## Scenario 1: Happy path — multi-agent Codex session (should-trigger, functional)

**Given** user is setting up multi-agent work in Codex CLI
**When** user says "set up codex agents for parallel processing"
**Then**
- [ ] Skill activates (or is read by orchestrator)
- [ ] Context handoff follows 5-component template
- [ ] File ownership declared per agent via scope field
- [ ] spawn_agent used with clear instructions

## Scenario 2: Edge case — batch CSV processing (should-trigger, functional)

**Given** user wants to process multiple files with same operation
**When** user uses spawn_agents_on_csv pattern
**Then**
- [ ] CSV template correctly maps rows to agent instructions
- [ ] max_threads respects limit (default 3, max 7)
- [ ] Each agent has independent scope

## Scenario 3: Should-NOT-trigger — Claude Code multi-agent work

**Given** user is working in Claude Code
**When** user says "set up multi-agent for this Claude Code project"
**Then**
- [ ] forge-codex-multiagent does NOT activate
- [ ] forge-claude-teams activates instead

## Scenario 4: Edge case — agent failure and recovery (should-trigger, functional)

**Given** a spawned agent crashes or times out during work
**When** the orchestrator detects the failure via wait() timeout or error return
**Then**
- [ ] Failed agent is closed with close_agent to collect partial output
- [ ] Fresh agent is spawned with same context handoff + failure note
- [ ] No send_input is attempted to the failed agent
- [ ] Recovery follows the 2-retry escalation protocol

## Scenario 5: Performance — batch processing throughput (performance)

**Given** a CSV with 10 analysis tasks for spawn_agents_on_csv
**When** batch processing runs with max_threads=3
**Then**
- [ ] No more than 3 agents run concurrently
- [ ] All 10 tasks complete without resource exhaustion
- [ ] Each agent's context handoff is under 4K tokens
- [ ] Total orchestration overhead is <20% of agent computation time
