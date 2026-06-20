"""
forge_milestone — SkillOpt environment for optimizing forge-orchestrator prose.

Copy this file (and the dataloader below) into a SkillOpt checkout at
`skillopt/envs/forge_milestone/` and register it in scripts/train.py. It subclasses
the same EnvAdapter contract as skillopt/envs/_template/env_template.py.

A rollout = replay ONE forge milestone under the candidate skill (the
forge-orchestrator gate/COMPOUND section), then score the resulting artifact tree
with forge_reward.score_run → {id, hard, soft}. The reward leans on `hard`
(all-or-nothing, hard to game); `soft` is the gradient shaper.

SECURITY (hard precondition): the environment MUST be installed with the `skillopt`
subtree ONLY. Run forge-skillopt/check_no_skillopt_sleep.py in CI — it asserts
`import skillopt_sleep` raises ImportError. Never `pip install -e .` the whole
SkillOpt repo (its pyproject packages the leaky skillopt_sleep module).

COST (M6): each rollout is a full multi-agent orchestration (minutes–hours, many
model calls). Run with batch 4-8, workers 1-2, 1 milestone/rollout, use_gate=true,
on a no-Azure backend (codex_exec / claude_code_exec). Gate M6 behind a passing
forge-skillopt/measure_noise.py and explicit budget approval; accept best_skill.md
ONLY on held-out val improvement AND human diff-review of the gate-ladder change.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# forge_reward lives in forge-skillopt/ (one dir up from this env package when
# vendored). Resolve it via FORGE_SKILLOPT_DIR or a sensible default.
_FR_DIR = os.environ.get("FORGE_SKILLOPT_DIR", str(Path(__file__).resolve().parents[1]))
if _FR_DIR not in sys.path:
    sys.path.insert(0, _FR_DIR)
import forge_reward  # noqa: E402

try:
    from skillopt.envs.base import EnvAdapter
    from skillopt.datasets.base import BatchSpec
except Exception:  # allow standalone import for syntax/contract checks
    EnvAdapter = object  # type: ignore
    BatchSpec = object  # type: ignore


class ForgeMilestoneLoader:
    """Loads milestone replay items. Each item needs at least `id`; forge items add
    `repo_url`, `base_sha` (pinned), `milestone`, `acceptance_criteria`, `task_type`."""

    def __init__(self, split_dir: str = "", data_path: str = "", **kw) -> None:
        self.split_dir = split_dir
        self.data_path = data_path
        self.train_items: list[dict] = []
        self.val_items: list[dict] = []
        self.test_items: list[dict] = []

    def setup(self, cfg: dict) -> None:
        for split in ("train", "val", "test"):
            p = Path(self.split_dir) / f"{split}.jsonl"
            items = self.load_split_items(str(p)) if p.exists() else []
            setattr(self, f"{split}_items", items)

    @staticmethod
    def load_split_items(split_path: str) -> list[dict]:
        p = Path(split_path)
        if not p.exists():
            return []
        out = []
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                out.append(json.loads(line))
        return out

    def build_train_batch(self, batch_size: int, seed: int, **kw):
        return BatchSpec(payload=self.train_items[:batch_size]) if BatchSpec is not object else self.train_items[:batch_size]

    def build_eval_batch(self, env_num: int, split: str, seed: int, **kw):
        items = getattr(self, f"{split}_items", [])
        payload = items[:env_num] if env_num else items
        return BatchSpec(payload=payload) if BatchSpec is not object else payload


class ForgeMilestoneEnv(EnvAdapter):
    """Optimize the forge-orchestrator gate/COMPOUND section against a deterministic
    artifact-derived reward."""

    def __init__(self, split_dir: str = "", workers: int = 1, minibatch_size: int = 8,
                 edit_budget: int = 4, backend_cmd: str = "", run_root: str = "/tmp/forge_rollouts",
                 **kw) -> None:
        self.workers = workers
        self.minibatch_size = minibatch_size
        self.edit_budget = edit_budget
        # Backend command template that runs ONE forge milestone and writes its
        # artifacts into {run_dir}. Provided via config (codex_exec/claude_code_exec).
        # MUST be a no-Azure backend. Left empty here → rollout raises until wired.
        self.backend_cmd = backend_cmd
        self.run_root = run_root
        self.dataloader = ForgeMilestoneLoader(split_dir=split_dir, **kw)

    def setup(self, cfg: dict) -> None:
        if hasattr(EnvAdapter, "setup"):
            try:
                super().setup(cfg)  # type: ignore
            except Exception:
                pass
        self.dataloader.setup(cfg)

    def get_dataloader(self):
        return self.dataloader

    def build_env_from_batch(self, batch, **kw):
        return list(getattr(batch, "payload", batch) or [])

    def build_train_env(self, batch_size: int, seed: int, **kw):
        return self.build_env_from_batch(self.dataloader.build_train_batch(batch_size=batch_size, seed=seed, **kw))

    def build_eval_env(self, env_num: int, split: str, seed: int, **kw):
        return self.build_env_from_batch(self.dataloader.build_eval_batch(env_num=env_num, split=split, seed=seed, **kw))

    def _replay(self, item: dict, skill_content: str, run_dir: Path) -> None:
        """Run ONE forge milestone under skill_content, writing artifacts to run_dir.
        This is the expensive M6 step — a full orchestration via the configured
        no-Azure backend. Raises if no backend is wired (so M5 can't accidentally
        spend)."""
        if not self.backend_cmd:
            raise RuntimeError(
                "backend_cmd not configured — wire a no-Azure codex_exec/claude_code_exec "
                "command before running rollouts (M6). See README."
            )
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "candidate_skill.md").write_text(skill_content, encoding="utf-8")
        cmd = self.backend_cmd.format(
            run_dir=str(run_dir),
            repo_url=item.get("repo_url", ""),
            base_sha=item.get("base_sha", ""),
            milestone=item.get("milestone", item.get("id", "")),
            skill_path=str(run_dir / "candidate_skill.md"),
        )
        subprocess.run(cmd, shell=True, check=False, timeout=int(item.get("timeout_s", 3600)))

    def rollout(self, env_manager, skill_content: str, out_dir: str, **kw) -> list[dict]:
        results: list[dict] = []
        for item in env_manager:
            mid = str(item.get("id", item.get("milestone", "")))
            run_dir = Path(self.run_root) / f"{mid}__{abs(hash(skill_content)) % 10_000_000}"
            try:
                self._replay(item, skill_content, run_dir)
                r = forge_reward.score_run(str(run_dir), item.get("milestone", mid), repo_root=str(run_dir))
            except Exception as e:
                r = {"id": mid, "hard": 0, "soft": 0.0, "fail_reason": str(e)}
            r.setdefault("id", mid)
            r["task_type"] = item.get("task_type", "milestone")
            results.append(r)
        return results

    def get_task_types(self) -> list[str]:
        seen: list[str] = []
        for it in (self.dataloader.train_items + self.dataloader.val_items + self.dataloader.test_items):
            tt = str(it.get("task_type") or "milestone")
            if tt not in seen:
                seen.append(tt)
        return seen or ["milestone"]
