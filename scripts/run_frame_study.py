"""Run course-v1 development selection and/or the locked M0–M5 frame benchmark."""

import argparse
import json
import time
from pathlib import Path

from gaze_audit.frame_study import develop, evaluate, load_feature_population

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("stage", choices=["develop", "evaluate", "all"])
parser.add_argument("--features", type=Path, required=True)
parser.add_argument("--processed", type=Path, default=Path("data/processed/vsgaze-17357752-v1"))
parser.add_argument("--development", type=Path, required=True)
parser.add_argument("--evaluation", type=Path)
parser.add_argument("--validation-draws", type=int, default=100)
parser.add_argument("--test-draws", type=int, default=1000)
args = parser.parse_args()
if min(args.validation_draws, args.test_draws) < 1:
    parser.error("Draw counts must be positive")
if args.stage != "develop" and args.evaluation is None:
    parser.error("Evaluation requires --evaluation")
started = time.monotonic()
tables, hashes = load_feature_population(args.features)
if args.stage in ["develop", "all"]:
    develop(tables, hashes, args.processed, args.development, args.validation_draws)
if args.stage in ["evaluate", "all"]:
    report = evaluate(
        tables, hashes, args.processed, args.development, args.evaluation, args.test_draws
    )
    print(
        json.dumps(
            {
                "test_population_size": report["test_population_size"],
                "sampled_method_runs": report["sampled_method_runs"],
            },
            indent=2,
        )
    )
print(f"Completed stage {args.stage} in {time.monotonic() - started:.1f} seconds")
