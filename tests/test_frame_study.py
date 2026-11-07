import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from gaze_audit.frame_study import develop, evaluate, load_feature_population


def test_lock_then_evaluate_keeps_uniform_ids_and_test_labels_out_of_selection(tmp_path):
    rng = np.random.default_rng(17)
    rows, labels = [], []
    for split, size in [("train", 1000), ("validation", 1600), ("test", 1600)]:
        for i in range(size):
            q = float(rng.uniform(0.05, 0.3))
            record = f"{split}-{i}"
            rows.append(
                {
                    "record_id": record,
                    "split": split,
                    "source_id": f"{split}-{i % 5}",
                    "frame_id": f"frame-{split}-{i}",
                    "clip_id": f"clip-{split}-{i % 5}",
                    "person_a": 1,
                    "person_b": 2,
                    "clip_frame_index_1based": i // 5 + 1,
                    "eligible_anchor": 1,
                    "f_q": q,
                    "f_geometry": float(rng.random()),
                }
            )
            labels.append({"record_id": record, "label": int(rng.random() < q)})
    static = pd.DataFrame(rows)
    tables = {
        "static": static,
        "temporal-w5": static.assign(f_context=0.1, f_t_q_mean=static.f_q, f_t_q_std=0.01),
        "temporal-w11": static.assign(f_context=0.2, f_t_q_mean=static.f_q, f_t_q_std=0.02),
    }
    feature_root = tmp_path / "features"
    feature_root.mkdir()
    manifest = {"complete": True, "feature_files": {}}
    for name, table in tables.items():
        path = feature_root / f"features-{name}.csv"
        table.to_csv(path, index=False)
        manifest["feature_files"][name] = {
            "filename": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "feature_columns": [c for c in table if c.startswith("f_")],
        }
    (feature_root / "manifest.json").write_text(json.dumps(manifest))
    tables, hashes = load_feature_population(feature_root)
    processed = tmp_path / "processed"
    (processed / "oracle").mkdir(parents=True)
    references = pd.DataFrame(labels)
    references.to_csv(processed / "oracle/oracle_labels.csv", index=False)
    pd.DataFrame({"source_id": [f"train-{i}" for i in range(5)], "fold": range(5)}).to_csv(
        processed / "development_folds.csv", index=False
    )
    development = tmp_path / "development"
    lock = develop(tables, hashes, processed, development, draws=3)
    assert lock["test_references_used_for_selection"] is False
    assert len(lock["candidates"]) == 9
    before = hashlib.sha256((development / "policy-lock.json").read_bytes()).hexdigest()
    first = tmp_path / "evaluation-first"
    report = evaluate(tables, hashes, processed, development, first, draws=3)
    assert report["sampled_method_runs"] == 60
    manifest = json.loads((first / "query-manifest.json").read_text())
    assert len(manifest) == 12  # Four budgets, only three query streams; M1/M2/M5 share one.
    assert report["uniform_queries_reused_by"] == ["M1", "M2", "M5"]
    references.loc[references.record_id.str.startswith("test-"), "label"] = 1
    references.to_csv(processed / "oracle/oracle_labels.csv", index=False)
    second = tmp_path / "evaluation-changed-test-references"
    altered = evaluate(tables, hashes, processed, development, second, draws=3)
    assert hashlib.sha256((development / "policy-lock.json").read_bytes()).hexdigest() == before
    assert (first / "query-manifest.json").read_bytes() == (
        second / "query-manifest.json"
    ).read_bytes()
    assert report["reference_prevalence"] != altered["reference_prevalence"]
    replay = tmp_path / "replay"
    command = [
        sys.executable,
        "scripts/replay_audit.py",
        "--evaluation",
        str(second),
        "--development",
        str(development),
        "--features",
        str(feature_root),
        "--processed",
        str(processed),
        "--output",
        str(replay),
    ]
    result = subprocess.run(
        command, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True
    )
    assert result.returncode == 0, result.stderr
    replay_report = json.loads((replay / "replay.json").read_text())
    assert replay_report["rng_plan_reproduced"] and replay_report["estimate_reproduced"]
    assert replay_report["exact_labels"] == 160
    timeline = pd.read_csv(replay / "public-query-timeline.csv")
    assert "label" not in timeline and timeline.selected_query.sum() > 0
    # Even one changed reference must be rejected when replaying a saved evaluation.
    references.loc[references.record_id.eq("test-0"), "label"] = 0
    references.to_csv(processed / "oracle/oracle_labels.csv", index=False)
    command[-1] = str(tmp_path / "replay-changed-oracle")
    rejected = subprocess.run(
        command, cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True
    )
    assert rejected.returncode != 0 and "Oracle references changed" in rejected.stderr
    for entry in manifest:
        queries = np.load(first / entry["file"])["selected"]
        assert queries.shape == (3, entry["budget"])
        assert all(len(set(row)) == entry["budget"] for row in queries)
