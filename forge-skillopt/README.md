# forge-skillopt — SkillOpt pilot for optimizing the forge workflow

Evidence-gated integration of [Microsoft SkillOpt](https://github.com/microsoft/SkillOpt)
to optimize the forge-orchestrator's prose against a **deterministic reward derived
from real forge runs**. Built per the forge eval decision (Phase 1) and its
adversarial review (GO-WITH-CHANGES).

This package is the **gradable substrate (M5)**. The actual optimization run (M6)
is gated behind a passing noise gate, explicit budget approval, and human review.

## Why this can work for forge (when it couldn't for handoff)

handoff's EVALUATIONS were qualitative checklists — not a gradable reward, so
SkillOpt was deferred. Forge is different: it emits machine-checkable signals the
M2/M4 work made deterministic (GATE A–E markers, the goal-reconciliation table,
`state: FINALIZED`, scope-guard logs). `forge_reward.py` turns those into a
{hard, soft} score, so the optimizer has a real gradient.

## Components (all tested standalone)

| File | Role | Status |
|------|------|--------|
| `forge_reward.py` | deterministic reward over a completed run's artifacts → `{hard, soft, components}`. Imports the M2 completion guard for the criteria signal (single source, anti-Goodhart). | ✅ tested |
| `check_no_skillopt_sleep.py` | **hard security precondition**: asserts `import skillopt_sleep` fails + greps for leaked secrets. | ✅ tested |
| `measure_noise.py` | **M5 gate**: replay each milestone N×, require per-milestone soft std-dev ≤ threshold + consistent `hard`. Run BEFORE M6. | ✅ tested |
| `skillopt_env/forge_milestone.py` | SkillOpt `EnvAdapter`: `rollout()` replays a milestone under the candidate skill, scores via `forge_reward`. | ✅ imports; runs in a SkillOpt checkout (M6) |
| `configs/forge_milestone.yaml` | conservative config (1 milestone/rollout, batch 4–8, workers 1–2, held-out gate on). | ✅ |
| `data/forge_milestones/*.jsonl` | dataset format (replayable milestones, pinned `base_sha`, acceptance criteria) + train/val/test split. | ✅ sample |

## Reward (forge_reward.py)

```
soft = 0.40·criteria_coverage + 0.25·gate_adherence
     + 0.20·(1−false_completion) + 0.15·(1−scope_violation_rate)
hard = 1  iff  every criterion verified (Code file:line resolves AND named Test exists)
              AND no gate skipped  AND  scope_violations == 0
```
Acceptance leans on `hard`; `soft` is a gradient shaper only (so writing a gate
marker without satisfying the expensive hard signal can't move acceptance —
anti-reward-hacking, per the adversarial review).

## Security precondition (HARD — do this first)

SkillOpt's `pyproject.toml` packages `skillopt_sleep`, whose `backend.py` hardcodes
internal Azure endpoints + a managed-identity client-id GUID. **A plain
`pip install -e .` of the SkillOpt repo pulls the leaky module in.** Therefore:

1. Vendor/install ONLY the `skillopt` subtree (not the whole repo).
2. `python forge-skillopt/check_no_skillopt_sleep.py` must PASS (it asserts
   `import skillopt_sleep` raises ImportError). Wire it into CI / pre-commit.
3. Use a **no-Azure backend** for rollouts (`codex_exec` / `claude_code_exec`).

## M5 — build & validate the gradable substrate (no optimization)

1. Run the security check (above) → PASS.
2. Curate `data/forge_milestones/{train,val,test}.jsonl` from the in-repo milestones
   + the 233-run forensic corpus (each item: pinned `base_sha`, acceptance criteria).
   A **real val split is required** for the held-out gate.
3. Replay 10–20 milestones N× under the *unoptimized* skill, then:
   `python forge-skillopt/measure_noise.py <replay_root> --max-std 0.10`
   It must PASS (low variance + consistent `hard`). If it FAILs, the reward is too
   noisy — fix the parseable-state emission (M2 reconciliation / M4 validate) and
   re-measure. **Do not optimize against a noisy reward.**

## M6 — scoped optimization run (budget-gated)

Only after M5 PASSES and a budget is approved:

1. Copy `skillopt_env/forge_milestone.py` → `<skillopt>/skillopt/envs/forge_milestone/`,
   wire the dataloader, register in `scripts/train.py`, and copy
   `configs/forge_milestone.yaml` → `<skillopt>/configs/forge_milestone/default.yaml`
   (inheriting `_base_/default.yaml`). Set `backend_cmd` to a no-Azure command.
2. Optimize the **gate/COMPOUND section only** (not the whole 423-line doc).
3. Accept `best_skill.md` **only on held-out val improvement** AND a **human
   diff-review** of the gate-ladder change — never auto-accept on metric delta.
4. The accepted section must pass the forge EVALUATIONS regression (M2/M3 scenarios).
5. Record provenance (seed, dataset, gate metric, delta) in the forge CHANGELOG.

**Cost**: each rollout is a full multi-agent orchestration (minutes–hours, many
model calls); M6 is rate-limit-prone. Run deliberately against a budget with
workers 1–2 and batch 4–8.
