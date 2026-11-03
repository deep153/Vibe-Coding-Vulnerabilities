"""Re-run every Claude Sonnet 5.5 trajectory that returned an empty message
with no tool call in the full run, recording the provider finish reason.

The original Stage 2 files are left untouched. Results go to
sard_claude_rerun_raw_logs.json (resumable).
"""

from __future__ import annotations

import json
import os

from sard_config import CODING_MODELS, FULL_DATASET_FILE, FULL_RAW_LOG_FILE
from sard_experiment_runner import openrouter_client, run_trajectory

OUT = "sard_claude_rerun_raw_logs.json"
MODEL = next(m for m in CODING_MODELS if m["display_name"] == "Claude Sonnet 5.5")


def is_non_response(traj: dict) -> bool:
    t0 = traj["turns"][0]
    return not (t0.get("content") or "").strip() and not t0.get("tool_calls")


def main() -> None:
    with open(FULL_DATASET_FILE, encoding="utf-8") as f:
        dataset = {c["test_id"]: c for c in json.load(f)}
    with open(FULL_RAW_LOG_FILE, encoding="utf-8") as f:
        originals = json.load(f)
    targets = [
        t["test_id"]
        for t in originals
        if t["model"] == MODEL["display_name"] and is_non_response(t)
    ]

    done: list[dict] = []
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            done = json.load(f)
    finished = {t["test_id"] for t in done}

    client = openrouter_client()
    for i, test_id in enumerate(targets, 1):
        if test_id in finished:
            continue
        try:
            traj = run_trajectory(
                client,
                MODEL["model_id"],
                MODEL["display_name"],
                dataset[test_id],
                sandbox_mode="real",
            )
        except Exception as exc:  # noqa: BLE001
            traj = {"model": MODEL["display_name"], "test_id": test_id, "error": str(exc)}
        done.append(traj)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(done, f, indent=2)
        t0 = (traj.get("turns") or [{}])[0]
        print(f"[{i}/{len(targets)}] {test_id} finish={t0.get('finish_reason')} "
              f"native={t0.get('native_finish_reason')} tool_calls={len(t0.get('tool_calls') or [])}")


if __name__ == "__main__":
    main()
