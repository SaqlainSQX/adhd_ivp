"""Finish the declared course experiment after its fixed inference shards complete.

This is one sequential local run, without scheduling, test-driven model search,
or changes to the frozen population. Progress and failures are saved to disk.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from gaze_audit.frame_study import file_hash


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--population", type=Path, default=Path("data/raw/childplay/verified-population-v2")
    )
    parser.add_argument(
        "--shards",
        type=Path,
        nargs="+",
        default=[
            Path("outputs/inference/mtgs-strict-shard-v1"),
            Path("outputs/inference/mtgs-remaining-shard-v1"),
        ],
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--plot-python", type=Path, default=Path(".venv-mtgs/Scripts/python.exe"))
    parser.add_argument("--wait-seconds", type=int, default=18000)
    args = parser.parse_args()
    args.run.mkdir(parents=True, exist_ok=True)
    state_path = args.run / "pipeline-status.json"
    if state_path.exists():
        parser.error("Use a new run directory; preserve existing partial/successful pipelines")
    population_path = args.population / "population-manifest.json"
    state = {
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "complete": False,
        "state": "waiting_for_inference",
        "population_sha256": file_hash(population_path),
        "shards": list(map(str, args.shards)),
        "stages": [],
    }

    def save():
        state["updated_utc"] = datetime.now(timezone.utc).isoformat()
        temporary = state_path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(state, indent=2) + "\n")
        temporary.replace(state_path)

    save()
    deadline = time.monotonic() + args.wait_seconds
    try:
        while True:
            waiting = []
            for shard in args.shards:
                path = shard / "inference-provenance.json"
                if not path.exists():
                    waiting.append(str(shard))
                    continue
                try:
                    report = json.loads(path.read_text())
                except json.JSONDecodeError:
                    waiting.append(str(shard))  # Writer may be replacing a small manifest.
                    continue
                if not report["complete"]:
                    waiting.append(str(shard))
            state["waiting_for_shards"] = waiting
            save()
            if not waiting:
                break
            if time.monotonic() > deadline:
                raise TimeoutError(
                    "Inference wait exceeded the declared limit; no partial comparison run"
                )
            time.sleep(15)
        if (args.population / "WITHDRAWN.json").exists() or file_hash(population_path) != state[
            "population_sha256"
        ]:
            raise ValueError("Frozen media population changed or was withdrawn")
        state["state"] = "running"
        save()

        def stage(name, python, script, arguments):
            item = {
                "name": name,
                "state": "running",
                "script": script,
                "script_sha256": file_hash(Path(script)),
                "arguments": arguments,
            }
            state["stages"].append(item)
            state["current_stage"] = name
            save()
            started = time.monotonic()
            log = args.run / f"{name}.log"
            print(f"Starting {name}", flush=True)
            with log.open("w", encoding="utf-8") as handle:
                child = subprocess.run(
                    [str(python), "-X", "utf8", "-u", script, *arguments],
                    stdout=handle,
                    stderr=subprocess.STDOUT,
                )
            item.update(
                {
                    "state": "completed" if child.returncode == 0 else "failed",
                    "exit_code": child.returncode,
                    "elapsed_seconds": time.monotonic() - started,
                    "log": str(log),
                    "log_sha256": file_hash(log),
                }
            )
            save()
            if child.returncode:
                raise RuntimeError(f"{name} failed; inspect {log}")

        cache, features = args.run / "cache", args.run / "features"
        checks, development = args.run / "development-checks", args.run / "development"
        evaluation, replay, report = (
            args.run / "evaluation",
            args.run / "replay",
            args.run / "report",
        )
        stage(
            "P05-merge",
            sys.executable,
            "scripts/merge_prediction_shards.py",
            [
                "--population",
                str(args.population),
                "--shards",
                *map(str, args.shards),
                "--output",
                str(cache),
            ],
        )
        stage(
            "P06-features",
            sys.executable,
            "scripts/build_frame_features.py",
            ["--predictions", str(cache / "predictions.csv"), "--output", str(features)],
        )
        stage(
            "E01-E02-development-checks",
            sys.executable,
            "scripts/run_development_checks.py",
            ["--features", str(features), "--output", str(checks), "--draws", "100"],
        )
        stage(
            "E03-policy-lock",
            sys.executable,
            "scripts/run_frame_study.py",
            [
                "develop",
                "--features",
                str(features),
                "--development",
                str(development),
                "--validation-draws",
                "100",
            ],
        )
        stage(
            "E04-E05-evaluation",
            sys.executable,
            "scripts/run_frame_study.py",
            [
                "evaluate",
                "--features",
                str(features),
                "--development",
                str(development),
                "--evaluation",
                str(evaluation),
                "--test-draws",
                "1000",
            ],
        )
        stage(
            "E06-replay",
            sys.executable,
            "scripts/replay_audit.py",
            [
                "--evaluation",
                str(evaluation),
                "--development",
                str(development),
                "--features",
                str(features),
                "--method",
                "M4",
                "--fraction",
                ".1",
                "--draw",
                "0",
                "--output",
                str(replay),
            ],
        )
        stage(
            "E06-report",
            args.plot_python,
            "scripts/make_course_report.py",
            [
                "--evaluation",
                str(evaluation),
                "--development",
                str(development),
                "--checks",
                str(checks),
                "--population",
                str(args.population),
                "--output",
                str(report),
            ],
        )
        stage(
            "E06-replay-figure",
            args.plot_python,
            "scripts/plot_audit_replay.py",
            ["--replay", str(replay)],
        )
        state.update(
            {
                "complete": True,
                "state": "computed_waiting_for_visual_review",
                "report": str(report / "course-report.md"),
                "result_sha256": file_hash(evaluation / "result.json"),
            }
        )
        save()
        print(f"All computations completed: {report / 'course-report.md'}", flush=True)
    except Exception as error:
        state.update({"state": "failed", "error": str(error)})
        save()
        raise


if __name__ == "__main__":
    main()
