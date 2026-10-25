from itertools import combinations

import numpy as np
import pandas as pd
import pytest

from gaze_audit.data import assert_disjoint_sources, make_blocks, normalize_predictions
from gaze_audit.estimation import estimate
from gaze_audit.experiment import generate_demo, run_audit
from gaze_audit.oracle import LabelOracle
from gaze_audit.policy import StratumPlan, draw_plan


def predictions(indices=(0, 1, 2, 3)):
    return pd.DataFrame(
        {
            "record_id": [str(i) for i in indices],
            "source_id": "source",
            "clip_id": "clip",
            "frame_index": indices,
            "person_a": 2,
            "person_b": 1,
            "probability": np.linspace(0.1, 0.8, len(indices)),
        }
    )


def test_blocks_break_at_gaps_and_keep_short_tail():
    blocks = make_blocks(predictions((0, 1, 3, 4, 5)), length=2)
    assert [b.record_ids for b in blocks] == [("0", "1"), ("3", "4"), ("5",)]
    assert sum(b.cost for b in blocks) == 5


def test_reverse_duplicates_and_hidden_labels_rejected():
    frame = predictions()
    reversed_row = frame.iloc[[0]].assign(record_id="reverse", person_a=1, person_b=2)
    with pytest.raises(ValueError, match="Duplicate"):
        normalize_predictions(pd.concat([frame, reversed_row]))
    with pytest.raises(ValueError, match="no labels"):
        normalize_predictions(frame.assign(label=0))


def test_nonfinite_predictions_rejected():
    frame = predictions()
    frame.loc[0, "probability"] = np.inf
    with pytest.raises(ValueError, match="finite"):
        normalize_predictions(frame)


def test_oracle_reveals_and_logs_only_selected_blocks():
    blocks = make_blocks(predictions(), length=1)
    oracle = LabelOracle(
        pd.DataFrame({"record_id": ["0", "1", "2", "3"], "label": [0, 1, 0, 1]}),
        {"0", "1", "2", "3"},
    )
    queried = oracle.query([blocks[1]], seed=7, purpose="audit")
    assert queried == {blocks[1].block_id: 1}
    assert len(oracle.log) == 1 and oracle.log[0]["record_ids"] == ["1"]


def test_exact_enumeration_unbiasedness_and_variance_estimate():
    blocks = make_blocks(predictions(), length=1)
    labels = [0, 0, 1, 1]
    estimates, estimated_variances = [], []
    for selected in combinations(range(4), 2):
        plan = [StratumPlan(0, tuple(range(4)), selected, 2)]
        queried = {blocks[i].block_id: labels[i] for i in selected}
        result = estimate(blocks, plan, queried)
        estimates.append(result.prevalence)
        estimated_variances.append(result.standard_error**2)
    assert np.mean(estimates) == pytest.approx(0.5)
    assert np.mean(estimated_variances) == pytest.approx(np.var(estimates))


def test_census_exact_with_variable_costs():
    blocks = make_blocks(predictions((0, 1, 2, 4)), length=3)
    plan = [StratumPlan(0, (0, 1), (0, 1), 2)]
    result = estimate(blocks, plan, {blocks[0].block_id: 1, blocks[1].block_id: 1})
    assert result.prevalence == pytest.approx(0.5)
    assert result.standard_error == 0 and result.labels_revealed == 4


def test_allocation_expected_cost_and_sampling_reproducibility():
    blocks = make_blocks(predictions(tuple(range(41))), length=3)
    strata = np.array([i % 2 for i in range(len(blocks))])
    first = draw_plan(blocks, strata, np.array([0.1, 2]), 23, 0.5, 42)
    second = draw_plan(blocks, strata, np.array([0.1, 2]), 23, 0.5, 42)
    assert first == second
    expected = sum(
        h.expected_blocks * np.mean([blocks[i].cost for i in h.population]) for h in first
    )
    assert expected == pytest.approx(23)
    assert all(len(h.selected) >= 2 for h in first)
    with pytest.raises(ValueError, match="two blocks"):
        draw_plan(blocks, strata, np.ones(2), 1, 0.5, 42)


def test_source_overlap_rejected():
    blocks = make_blocks(predictions())
    with pytest.raises(ValueError, match="Source leakage"):
        assert_disjoint_sources({"train": blocks, "test": blocks})


def test_complete_synthetic_audit(tmp_path):
    data = tmp_path / "data"
    generate_demo(data, 42)
    report = run_audit(data, tmp_path / "audit", draws=2, budgets=(0.1,))
    assert report["synthetic"] is True
    assert len(report["summary"]) == 4
    assert all(s["successful_draws"] == 2 for s in report["summary"])
    assert report["development_labels"] == 5760
    assert (tmp_path / "audit" / "queries.jsonl").stat().st_size > 0
