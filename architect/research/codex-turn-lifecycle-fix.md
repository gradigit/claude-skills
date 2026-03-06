# Research: Codex CLI Turn-Ending Mechanism and Forge Skills Impact

## Summary
Codex CLI ends a turn when the model produces a text-only response (no tool calls). This is a deterministic mechanism in `codex-rs/core/src/codex.rs` — `needs_follow_up` is only set to `true` when tool calls are present. This causes forge-orchestrator to stop after each milestone's COMPOUND step, which writes 6+ state files then naturally produces a text summary. The fix belongs in both forge-codex-multiagent (general Turn Lifecycle guidance) and forge-orchestrator (specific COMPOUND step continuation directive). forge-builder has medium risk; forge-research is unaffected.

## Key Findings

1. **Turn lifecycle is deterministic** — `needs_follow_up = false` when no tool calls in response → loop breaks → turn ends. No configuration can override this. confidence: high — source: `codex-rs/core/src/codex.rs` lines 5097-5159, `stream_events_utils.rs` lines 111-235

2. **No auto_continue or max_turns config exists** — full codebase search confirms no knobs to force continuation after text-only responses. confidence: high — source: full search of codex-rs/

3. **The Codex system prompt actively causes the problem** — prompt.md encourages "preamble messages" and "sharing progress updates" as standalone text, which ends turns. confidence: high — source: `codex-rs/core/prompt.md`, GitHub #7900

4. **GitHub #7900 is the primary report** — affects all models, not just GPT-5.x. PR #7923 (community fix) was not merged. PR #12831 (Feb 25, 2026) restricts preambles to realtime mode only (partial fix). Issue still OPEN. confidence: high — source: github.com/openai/codex/issues/7900

5. **10+ related GitHub issues confirm the pattern** — #10828, #11527, #5264, #6277, #7247, #2751, #3790, #6384 all report premature stopping. Some closed as "model-behavior", none have harness-level fixes. confidence: high — source: github.com/openai/codex/issues/

6. **Claude Code doesn't have this problem** — Anthropic Messages API supports text + tool_use blocks in the same content array. `stop_reason: "tool_use"` if ANY tool_use block exists, regardless of text blocks. confidence: high — source: Anthropic tool use docs, stop reasons docs

7. **OpenAI introduced **`phase`** field for gpt-5.3-codex** — `"commentary"` vs `"final_answer"` distinguishes progress updates from turn-ending responses. Must be persisted in conversation history. confidence: high — source: Codex Prompting Guide (OpenAI cookbook)

8. **Official guidance: remove preamble instructions** — "Remove all prompting for the model to communicate an upfront plan, preambles, or other status updates during the rollout, as this can cause the model to stop abruptly." confidence: high — source: Codex Prompting Guide

9. **Successful long-horizon Codex workflows keep tool calls at every step** — read file → edit → run tests → observe → repair → update docs → repeat. Never text-only progress messages. confidence: high — source: OpenAI long horizon tasks cookbook

10. **forge-codex-multiagent Section 7 "Progress Narration" conflicts** — lines 393-399 encourage standalone text progress notes, which is exactly the pattern that ends Codex turns. confidence: high — source: direct analysis of SKILL.md

## Hypotheses
| Hypothesis | Status | Evidence |
| --- | --- | --- |
| H1: Codex ends turns on text-only responses | confirmed | Source code: `needs_follow_up` only true on tool calls |
| H2: System prompt encourages text-only updates | confirmed | prompt.md "Preamble messages" + "Sharing progress updates" sections |
| H3: Prompt-level instructions can prevent it | uncertain | Partially effective. Official guidance prefers removing preamble instructions over adding "don't stop" directives. AGENTS.md patterns degrade on long contexts |
| H4: Fix in both codex-multiagent AND orchestrator | confirmed | Defense in depth: general principle + specific failure point |
| H5: forge-builder has same risk as orchestrator | refuted | MEDIUM risk only — most phase transitions chain tool calls naturally |
| H6: Progress Narration guidance causes the problem | confirmed | Lines 393-399 encourage standalone text notes |

## Questions Resolved
- [x] Q1: Turn ends when `needs_follow_up = false`, set true ONLY on tool calls — source: codex.rs, stream_events_utils.rs
- [x] Q2: #7900 is the primary issue, 10+ related issues, PR #12831 merged as partial fix — source: GitHub
- [x] Q3: Yes, system prompt encourages "preamble messages" and "progress updates" — source: prompt.md
- [x] Q4: Claude Code supports text + tool_use in same response, `stop_reason: "tool_use"` continues — source: Anthropic docs
- [x] Q5: No auto_continue/max_turns config. `phase` field is API-level for gpt-5.3-codex — source: Codex Prompting Guide, codebase search
- [x] Q6: Official: remove preamble instructions. Ensure every step has a tool call — source: Codex Prompting Guide, long horizon cookbook
- [x] Q7: forge-orchestrator HIGH risk (COMPOUND step), forge-research NONE (chains tool calls naturally) — source: SKILL.md analysis
- [x] Q8: forge-builder MEDIUM risk — phase transitions mostly safe, Step 4b/4d/4f could stop mid-phase — source: SKILL.md analysis
- [x] Q9: Yes, Section 7 "Progress Narration" conflicts directly — source: SKILL.md lines 393-399
- [x] Q10: Fix should follow official guidance pattern: remove preamble encouragement + add tool-call continuation at known failure points — source: Codex Prompting Guide

## Recommended Fix: Exact Changes

### 1. forge-codex-multiagent → v1.1.0

**Add Section 9: Turn Lifecycle** (before Anti-Patterns). General guidance read by all skills during platform detection.

```markdown
## 9. Turn Lifecycle

**Critical for long-running workflows.**

Codex CLI ends a turn when the model produces a text-only response — any response
with no tool calls. This is a deterministic mechanism: `needs_follow_up` is set to
`true` only when tool calls are present. No configuration can override this.

This differs from Claude Code, where text and tool_use blocks coexist in the same
response and text alone does not end the turn.

### Rules for Continuous Execution

| Rule | Why |
|------|-----|
| Never produce a text-only message mid-workflow | Ends the turn immediately |
| Always pair state-file updates with a follow-up tool call | The tool call keeps the turn alive |
| After writing state files, immediately read the next phase's inputs | Transitions directly to the next step |
| Save summaries for the final step only | The last step is where the turn should end |

### Pattern

After completing a milestone or phase, do not summarize — immediately read the
next milestone's scope or the next phase's inputs. The act of reading transitions
you into the next step and keeps the turn alive.

```
# BAD — standalone text ends the turn
"Milestone 1 complete. Moving to milestone 2..."

# GOOD — tool call keeps the turn alive
[write FORGE-STATUS.md] → [read TODO.md for next milestone scope] → continue
```

### Where This Matters Most

- **forge-orchestrator COMPOUND step**: writes 6+ state files, then the model
  naturally summarizes. That summary ends the turn. Fix: read next milestone scope
  immediately after the commit.
- **forge-builder phase transitions**: after marking a phase complete in TODO.md,
  move directly to the next phase's implementation step.
- **forge-research synthesis steps**: after writing the research output file, if
  more depth cycles remain, read the output back to start the next cycle.
```

**Revise Section 7 "Progress Narration"** (lines 391-408). Change the progress narration guidance to be Codex-safe:

Current (lines 393-399):
```
Before each significant action batch, emit a brief progress note:
[auth-analyzer] Starting token refresh analysis in src/auth/refresh.ts
```

Revised:
```
Before each significant action batch, emit a brief progress note **as part of
a response that also includes tool calls**. On Codex CLI, a text-only progress
note ends the turn — always pair narration with the tool calls it describes.

Do NOT emit standalone text-only progress messages between action batches.
```

### 2. forge-orchestrator → v1.2.0

**Add COMPOUND step 9** (after line 178): explicit continuation directive.

```markdown
9. **Transition to next milestone immediately**: Read the next milestone's scope
   from TODO.md right now. Do NOT produce a standalone summary between milestones
   — on Codex CLI, a text-only response (no tool calls) ends the turn and halts
   the orchestration. The summary is implicit in the state files you just updated.
   If this is the last milestone, proceed to Step 3.
```

### 3. forge-builder — No changes

MEDIUM risk, but the fix in forge-codex-multiagent's Turn Lifecycle section covers it. forge-builder reads the practices guide during Step 2 (Platform Detection), so it will receive the general guidance. Adding redundant Codex-specific instructions to every skill creates maintenance burden without proportional benefit.

### 4. forge-research — No changes

Already works on Codex (A- grade). Every step naturally chains tool calls.

## Gaps and Limitations
- AGENTS.md "don't stop" instructions have limited effectiveness on long contexts — our fix should not rely solely on this pattern
- The `phase` field (gpt-5.3-codex) is an API-level mechanism that the Codex CLI harness handles — prompt instructions cannot control it
- PR #12831 (Feb 25, 2026) may have partially mitigated the problem for recent Codex versions, but our fix should work regardless of version
- We haven't tested the exact fix wording on Codex — it should be validated in the next orchestrator run

## Sources
- `codex-rs/core/src/codex.rs` lines 5097-5159 — turn execution loop and `needs_follow_up` check
- `codex-rs/core/src/stream_events_utils.rs` lines 111-235 — `handle_output_item_done` where `needs_follow_up` is set
- `codex-rs/core/prompt.md` line 125 — system prompt "keep going" instruction
- github.com/openai/codex/issues/7900 — primary bug report for premature turn-ending
- github.com/openai/codex/issues/10828, #11527, #5264, #6277, #7247, #2751, #3790, #6384 — related issues
- github.com/openai/codex/pull/7923 — community fix (not merged)
- github.com/openai/codex/pull/12831 — official partial fix (preambles for realtime only)
- Anthropic tool use docs — text + tool_use coexistence in Messages API
- Anthropic stop reasons docs — `stop_reason: "tool_use"` continues turn
- Codex Prompting Guide (OpenAI cookbook) — official guidance on removing preamble instructions
- OpenAI long horizon tasks cookbook — successful multi-hour Codex workflow patterns

## Generated
- Date: 2026-03-04
- Workflow: forge-research v1.1.0 (manual execution, 4 research agents)
