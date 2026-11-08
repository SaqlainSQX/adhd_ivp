"""Pin R settings and prerequisites before opening directional outcomes."""

import hashlib
import json
from pathlib import Path


def main():
    previous = Path("configs/query-noise-q-v2.json")
    q = json.loads(previous.read_text(encoding="utf-8"))
    hashes = dict(q["input_sha256"])
    for name in [
        previous.as_posix(),
        "docs/ASYMMETRIC_NOISE_R.md",
        "outputs/query-noise-q-v2/result.json",
        "outputs/query-noise-q-v2/draw-results.csv",
        "outputs/query-noise-q-v2/independent-validation.json",
        "scripts/run_query_noise_v2.py",
        "src/gaze_audit/exact_intervals.py",
        "src/gaze_audit/strengthening.py",
    ]:
        hashes[name] = hashlib.sha256(Path(name).read_bytes()).hexdigest()
    cfg = {
        "protocol": "docs/ASYMMETRIC_NOISE_R.md",
        "datasets": {"ChildPlay": 1, "UCO": 2},
        "draws": 1000,
        "cases": [
            {"name": "clean", "a": 0, "b": 0},
            {"name": "false-positive", "a": 0.02, "b": 0},
            {"name": "false-negative", "a": 0, "b": 0.02},
        ],
        "weights": q["weights"],
        "noise_seed_definition": (
            "default_rng(SeedSequence([810000+draw,1,dataset_code,92])).random(N)"
        ),
        "primary": "full K4 signed bias versus clean reference for both directional cases/corpora",
        "secondary": (
            "all RMSE/normal coverage-width/naive binary clean-target coverage-width/flips"
        ),
        "expected_method_case_draws": 18000,
        "budgets": {"ChildPlay": 1032, "UCO": 521},
        "input_sha256": hashes,
        "toy": q["toy"],
    }
    target = Path("configs/directional-noise-r-v1.json")
    with target.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(cfg, indent=2) + "\n")
    print(f"Registered {len(hashes)} pinned inputs; outcomes not started")


if __name__ == "__main__":
    main()
