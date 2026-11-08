"""Additive research explorer: tracked aggregates and verified, sampled-only D replay."""

import hashlib
import json
import threading
from pathlib import Path

import numpy as np
import pandas as pd

from .exact_intervals import stratified_binary_interval
from .explorer import AuditExplorer
from .followups import load_main
from .frame_study import file_hash, make_design, read_references, reconstruct_plan
from .frames import FrameOracle, estimate_frames, integer_budget


def build_summary(project):
    project = Path(project)
    source = project / "docs/research"
    names = {
        "main": "main-course-results.json",
        "d": "timed-d-result.json",
        "cost": "extra-c-C2-label-cost-result.json",
        "sources": "source-e-result.json",
        "source_assessment": "source-e-assessment.json",
        "intervals": "weighted-f-result.json",
        "blocks": "block-g-result.json",
        "guidance": "g2-result.json",
    }
    docs = {key: json.loads((source / name).read_text()) for key, name in names.items()}
    result = dict(
        version=1,
        population=dict(
            test_frames=10316,
            test_sources=10,
            retained_sources=53,
            attempted_sources=95,
            train_labels=191956,
            validation_labels=25139,
        ),
        draws=1000,
        budgets=[516, 1032, 2063, 4126],
        fractions=[0.05, 0.1, 0.2, 0.4],
        main=dict(
            results=docs["main"]["results"],
            model_mean=docs["main"]["model_only_mean"],
            truth=docs["main"]["reference_prevalence"],
        ),
        frame=dict(
            results={
                key: value
                for key, value in docs["d"]["results"].items()
                if key.startswith(("K4-", "power-score-", "power-uniform-"))
            },
            primary=docs["d"]["comparisons"]["power-score-b1032/K4"],
            selected_weights=docs["d"]["selected_lambdas"],
        ),
        label_cost=dict(
            results=docs["cost"]["results"],
            training_labels=docs["cost"]["training_labels"],
            validation_labels=docs["cost"]["validation_labels_reused"],
        ),
        source_variation=dict(assessment=docs["source_assessment"], rows=[]),
        intervals=docs["intervals"]["results"],
        blocks=docs["blocks"]["results"],
        guidance=docs["guidance"]["results"],
        block_primary=docs["guidance"]["primary"],
        provenance={
            name: hashlib.sha256((source / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            for name in names.values()
        },
    )
    for i in range(1, 11):
        alias = f"S{i:02d}"
        base = docs["sources"]["summaries"][f"K4-b1032-source-{alias}"]
        weighted = docs["sources"]["summaries"][f"power-score-b1032-source-{alias}"]
        comparison = docs["sources"]["comparisons"][f"b1032-source-{alias}"]
        result["source_variation"]["rows"].append(
            dict(
                alias=alias,
                frames=base["size"],
                positives=base["positives"],
                base_rmse=base["rmse_pp"],
                weighted_rmse=weighted["rmse_pp"],
                ratio=comparison["rmse_ratio"],
            )
        )
    return result


class ResearchExplorer(AuditExplorer):
    """The original explorer is unchanged; only its frame renderer is reused."""

    METHODS = ("power-score", "K4", "power-uniform")

    def __init__(self, project, *, aggregate_only=False):
        self.project = Path(project)
        self.main = self.project / "outputs/experiments/course-20261107-v1"
        self.processed = self.project / "data/processed/vsgaze-17357752-v1"
        self.study = self.project / "outputs/experiments/timed-d-20261108-v1"
        self.aggregate_only = aggregate_only
        self.loaded = False
        self.load_lock = threading.Lock()

    def health(self):
        available = not self.aggregate_only and all(
            path.exists()
            for path in [
                self.study / "result.json",
                self.main / "features/manifest.json",
                self.processed / "oracle/oracle_labels.csv",
            ]
        )
        return dict(
            ready=True,
            replay_available=available,
            mode="local frozen-cache research explorer",
            methods=list(self.METHODS) if available else [],
        )

    def _ensure_loaded(self):
        if self.loaded:
            return
        if not self.health()["replay_available"]:
            raise FileNotFoundError(
                "Replay needs the accepted main/D caches and P02 reference tables; "
                "aggregate views remain available."
            )
        with self.load_lock:
            if self.loaded:
                return
            self.lock, self.result, tables, _ = load_main(self.main, self.processed)
            self.tables = {
                k: t[t.split.eq("test")].reset_index(drop=True) for k, t in tables.items()
            }
            self.public = self.tables["static"]
            self.ids = tuple(self.public.record_id)
            self.positions = {key: i for i, key in enumerate(self.ids)}
            index = pd.read_csv(self.study / "population_index.csv")
            if tuple(index.record_id) != self.ids:
                raise ValueError("D population order changed")
            verification = json.loads(
                (self.project / "docs/research/timed-d-independent-validation.json").read_text()
            )
            if file_hash(self.study / "result.json") != verification["result_sha256"]:
                raise ValueError("D accepted result changed")
            self.d_result = json.loads((self.study / "result.json").read_text())
            if file_hash(self.study / "policy-lock.json") != self.d_result["policy_lock_sha256"]:
                raise ValueError("D accepted policy lock changed")
            evidence = json.loads(
                (self.project / "docs/research/timed-d-evidence-manifest.json").read_text()
            )
            for filename in ["query-manifest.json", "draw-results.csv", "K4-training.json"]:
                matches = [sha for name, sha in evidence.items() if name.endswith("/" + filename)]
                if len(matches) != 1 or file_hash(self.study / filename) != matches[0]:
                    raise ValueError(f"D evidence changed: {filename}")
            self.d_manifest = json.loads((self.study / "query-manifest.json").read_text())
            self.d_draws = pd.read_csv(self.study / "draw-results.csv")
            self.training = json.loads((self.study / "K4-training.json").read_text())
            self.frames = pd.read_csv(self.processed / "public/frames.csv").set_index("frame_id")
            acquisition = (
                self.project / "data/raw/childplay/verified-population-v2/acquisition.json"
            )
            self.archives = {}
            if acquisition.exists():
                metadata = json.loads(acquisition.read_text())
                self.archives = {
                    s["source_id"]: Path(s["archive"])
                    for s in metadata["sources"]
                    if s["status"] == "complete"
                }
            self.loaded = True

    def replay(self, method="power-score", fraction=0.1, draw=0, *, reveal=False):
        if (
            method not in self.METHODS
            or fraction not in [0.05, 0.1, 0.2, 0.4]
            or type(draw) is not int
            or not 0 <= draw < 1000
            or type(reveal) is not bool
        ):
            raise ValueError("Choose a recorded method, budget and integer draw0–999")
        self._ensure_loaded()
        budget = integer_budget(fraction, len(self.ids))
        entry = next(e for e in self.d_manifest if e["policy"] == method and e["budget"] == budget)
        path = self.study / entry["file"]
        if file_hash(path) != entry["sha256"]:
            raise ValueError("Saved query file changed")
        native = self.public.f_q.to_numpy(float)
        groups = (
            np.zeros(len(native), int)
            if method == "power-uniform"
            else np.searchsorted(self.training["cuts"], native, side="left")
        )
        sd = np.ones(1) if method == "power-uniform" else np.array(self.training["sd"])
        populations, counts = make_design(groups, sd, budget, entry["alpha"])
        if counts.tolist() != entry["counts"] or list(map(len, populations)) != entry["sizes"]:
            raise ValueError("D design no longer matches the lock")
        saved = np.load(path)
        selection = saved["selected"][draw]
        if not np.array_equal(saved["counts"], counts):
            raise ValueError("Saved counts changed")
        rng = np.random.default_rng(
            np.random.SeedSequence(
                [200000 + draw, [0.05, 0.1, 0.2, 0.4].index(fraction), entry["stream"]]
            )
        )
        expected = np.concatenate(
            [
                rng.choice(p, size=int(n), replace=False)
                for p, n in zip(populations, counts, strict=True)
            ]
        )
        if not np.array_equal(selection, expected):
            raise ValueError("Saved random queries do not replay")
        selected_ids = tuple(self.ids[i] for i in selection)
        refs = read_references(self.processed, selected_ids)
        queried = FrameOracle(refs, selected_ids).query(selected_ids)
        weight = entry["weight"]
        estimate = estimate_frames(
            self.ids, native * weight, reconstruct_plan(populations, counts, selection), queried
        )
        recorded = self.d_draws[
            (self.d_draws.policy == method)
            & (self.d_draws.budget == budget)
            & (self.d_draws.draw == draw)
        ].iloc[0]
        if (
            abs(estimate.prevalence - recorded.prevalence) > 1e-12
            or abs(estimate.variance - recorded.variance) > 1e-12
        ):
            raise ValueError("Point/variance differs from the accepted audit")
        edges = np.r_[0, np.cumsum(counts)]
        successes = [
            sum(queried[self.ids[i]] for i in selection[a:b])
            for a, b in zip(edges[:-1], edges[1:], strict=True)
        ]
        exact = stratified_binary_interval(successes, counts, list(map(len, populations)))
        totals = tuple(round(x * len(self.ids)) for x in exact)
        if totals != (recorded.lower_total, recorded.upper_total):
            raise ValueError("Exact reference differs")
        keys = ["source_id", "clip_id", "person_a", "person_b"]
        example = (
            self.public.iloc[selection]
            .groupby(keys)
            .size()
            .sort_values(ascending=False, kind="stable")
            .index[0]
        )
        public = self.tables["temporal-w11"]
        mask = np.logical_and.reduce([public[k].eq(v) for k, v in zip(keys, example, strict=True)])
        timeline = public[mask].sort_values("clip_frame_index_1based")
        selected_set = set(selected_ids)
        return dict(
            method=method,
            fraction=fraction,
            budget=budget,
            draw=draw,
            verified=True,
            correction_weight=weight,
            native_model_mean=float(native.mean()),
            surrogate_mean=float((native * weight).mean()),
            estimate=estimate.as_dict(),
            exact_binary_reference=dict(
                low=exact[0],
                high=exact[1],
                lower_total=totals[0],
                upper_total=totals[1],
                centers_on_residual_estimate=False,
                point_outside=bool(not exact[0] <= estimate.prevalence <= exact[1]),
            ),
            query_file_sha256=entry["sha256"],
            labels_revealed=reveal,
            timeline=[
                dict(
                    id=r.record_id,
                    position=int(r.clip_frame_index_1based),
                    q=float(r.f_q),
                    context_mean=float(r.f_t_q_mean),
                    queried=r.record_id in selected_set,
                    label=int(queried[r.record_id])
                    if reveal and r.record_id in selected_set
                    else None,
                )
                for r in timeline.itertuples()
            ],
            queries=[
                dict(
                    id=key,
                    q=float(native[self.positions[key]]),
                    label=int(queried[key]) if reveal else None,
                )
                for key in selected_ids
            ],
            strata=[
                dict(population=len(p), queries=int(n))
                for p, n in zip(populations, counts, strict=True)
            ],
        )

    def frame(self, record_id):
        self._ensure_loaded()
        if record_id not in self.positions:
            raise ValueError("Frame must belong to the frozen test population")
        row = self.public.iloc[self.positions[record_id]]
        if row.source_id not in self.archives or not self.archives[row.source_id].exists():
            raise FileNotFoundError(
                "Local media archive unavailable; numerical replay still works."
            )
        return super().frame(record_id)
