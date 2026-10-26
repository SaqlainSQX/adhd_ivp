import hashlib
import json

import numpy as np
import pandas as pd

from gaze_audit.frame_study import develop, evaluate


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
                    "eligible_anchor": 1,
                    "f_q": q,
                    "f_geometry": float(rng.random()),
                }
            )
            labels.append({"record_id": record, "label": int(rng.random() < q)})
    static = pd.DataFrame(rows)
    tables = {
        "static": static,
        "temporal-w5": static.assign(f_context=0.1),
        "temporal-w11": static.assign(f_context=0.2),
    }
    processed = tmp_path / "processed"
    (processed / "oracle").mkdir(parents=True)
    references = pd.DataFrame(labels)
    references.to_csv(processed / "oracle/oracle_labels.csv", index=False)
    pd.DataFrame({"source_id": [f"train-{i}" for i in range(5)], "fold": range(5)}).to_csv(
        processed / "development_folds.csv", index=False
    )
    development = tmp_path / "development"
    lock = develop(tables, {"fixture": "synthetic-software-check"}, processed, development, draws=3)
    assert lock["test_references_used_for_selection"] is False
    assert len(lock["candidates"]) == 9
    before = hashlib.sha256((development / "policy-lock.json").read_bytes()).hexdigest()
    first = tmp_path / "evaluation-first"
    report = evaluate(
        tables, {"fixture": "synthetic-software-check"}, processed, development, first, draws=3
    )
    assert report["sampled_method_runs"] == 60
    manifest = json.loads((first / "query-manifest.json").read_text())
    assert len(manifest) == 12  # Four budgets, only three query streams; M1/M2/M5 share one.
    assert report["uniform_queries_reused_by"] == ["M1", "M2", "M5"]
    references.loc[references.record_id.str.startswith("test-"), "label"] = 1
    references.to_csv(processed / "oracle/oracle_labels.csv", index=False)
    second = tmp_path / "evaluation-changed-test-references"
    altered = evaluate(
        tables, {"fixture": "synthetic-software-check"}, processed, development, second, draws=3
    )
    assert hashlib.sha256((development / "policy-lock.json").read_bytes()).hexdigest() == before
    assert (first / "query-manifest.json").read_bytes() == (
        second / "query-manifest.json"
    ).read_bytes()
    assert report["reference_prevalence"] != altered["reference_prevalence"]
    for entry in manifest:
        queries = np.load(first / entry["file"])["selected"]
        assert queries.shape == (3, entry["budget"])
        assert all(len(set(row)) == entry["budget"] for row in queries)
