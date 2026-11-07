"""Local offline audit replay service; no inference or arbitrary filesystem routes."""

import io
import json
import tarfile
from pathlib import Path

import numpy as np
import pandas as pd

from .followups import load_frozen_policy, load_main
from .frame_study import file_hash, make_design, read_references, reconstruct_plan
from .frames import FrameOracle, estimate_frames, integer_budget
from .strengthening import FeaturePolicy


class AuditExplorer:
    def __init__(self, main, processed, acquisition, extension):
        self.main, self.processed, self.extension = Path(main), Path(processed), Path(extension)
        self.lock, self.result, tables, _ = load_main(self.main, self.processed)
        self.tables = {k: v[v.split.eq("test")].reset_index(drop=True) for k, v in tables.items()}
        self.public = self.tables["static"]
        self.ids = tuple(self.public.record_id)
        self.positions = {key: i for i, key in enumerate(self.ids)}
        population = pd.read_csv(self.main / "evaluation/population_index.csv")
        if tuple(population.record_id) != self.ids:
            raise ValueError("Saved population order changed")
        self.policies = {
            m: load_frozen_policy(self.main, self.lock[f]["feature_set"], self.lock)
            for m, f in [("M3", "selected_static"), ("M4", "selected_temporal")]
        }
        self.draws = pd.read_csv(self.main / "evaluation/draw-results.csv")
        self.manifest = json.loads((self.main / "evaluation/query-manifest.json").read_text())
        frames = pd.read_csv(self.processed / "public/frames.csv")
        self.frames = frames[frames.frame_id.isin(self.public.frame_id)].set_index("frame_id")
        media = json.loads((Path(acquisition) / "acquisition.json").read_text())
        self.archives = {
            s["source_id"]: Path(s["archive"])
            for s in media["sources"]
            if s["status"] == "complete"
        }
        self.simple = None
        simple_root = self.extension / "B1-simple-controls"
        if (simple_root / "result.json").exists():
            result = json.loads((simple_root / "result.json").read_text())
            if (
                result["complete"]
                and file_hash(simple_root / "policy-lock.json") == result["policy_lock_sha256"]
            ):
                self.simple = {
                    "root": simple_root,
                    "result": result,
                    "lock": json.loads((simple_root / "policy-lock.json").read_text()),
                    "draws": pd.read_csv(simple_root / "draw-results.csv"),
                    "manifest": json.loads((simple_root / "query-manifest.json").read_text()),
                }

    def summary(self):
        coverage_path = self.extension / "B2-coverage/result.json"
        return {
            "main": self.result,
            "simple_controls": self.simple["result"] if self.simple else None,
            "coverage_extension": json.loads(coverage_path.read_text())
            if coverage_path.exists()
            else None,
            "population": {
                "sources": 53,
                "train_sources": 40,
                "validation_sources": 3,
                "test_sources": 10,
                "test_pairs": len(self.ids),
                "train_labels_reused": 191956,
                "validation_labels_reused": 25139,
            },
            "methods": ["M1", "M2", "M3", "M4", "M5"]
            + (list(self.simple["lock"]["policies"]) if self.simple else []),
            "draws": self.result["draws_per_method_budget"],
            "cache_mode": "Frozen MTGS predictions; supplied benchmark head tracks; "
            "offline saved-query replay",
        }

    def replay(self, method="M3", fraction=0.1, draw=0):
        if (
            fraction not in [0.05, 0.1, 0.2, 0.4]
            or not 0 <= draw < self.result["draws_per_method_budget"]
        ):
            raise ValueError("Choose a recorded budget and draw 0 through 999")
        budget = integer_budget(fraction, len(self.ids))
        q = self.public.f_q.to_numpy(float)
        if method in ["M1", "M2", "M3", "M4", "M5"]:
            design = "uniform" if method in ["M1", "M2", "M5"] else method
            entry = next(
                e for e in self.manifest if e["design"] == design and e["budget"] == budget
            )
            path = self.main / "evaluation" / entry["file"]
            expected_hash = entry["sha256"]
            if design == "uniform":
                populations, counts, stream = (tuple(range(len(q))),), np.array([budget]), 1
            else:
                chosen = self.lock["selected_static" if method == "M3" else "selected_temporal"]
                policy = self.policies[method]
                populations, counts = make_design(
                    policy.strata(self.tables[chosen["feature_set"]]),
                    policy.residual_sd,
                    budget,
                    chosen["alpha"],
                )
                stream = 3 if method == "M3" else 4
            if method == "M1":
                q = np.zeros(len(q))
            elif method == "M5":
                q = self.policies["M4"].contextual_surrogate(
                    self.tables[self.lock["selected_temporal"]["feature_set"]]
                )
            recorded = self.draws[
                (self.draws.method == method)
                & (self.draws.budget == budget)
                & (self.draws.draw == draw)
            ].iloc[0]
        elif self.simple and method in self.simple["lock"]["policies"]:
            spec = self.simple["lock"]["policies"][method]
            policy = FeaturePolicy(
                spec["feature"], np.array(spec["cut_points"]), np.array(spec["residual_sd"])
            )
            populations, counts = make_design(
                policy.strata(self.public),
                policy.residual_sd,
                budget,
                self.simple["lock"]["selected"][method]["alpha"],
            )
            entry = next(
                e
                for e in self.simple["manifest"]
                if e["policy"] == method and e["budget"] == budget
            )
            path, expected_hash = self.simple["root"] / entry["file"], entry["sha256"]
            stream = 7 if method == "q-quartiles" else 8
            data = self.simple["draws"]
            recorded = data[
                (data.policy == method) & (data.budget == budget) & (data.draw == draw)
            ].iloc[0]
        else:
            raise ValueError("Unknown or unavailable method")
        if file_hash(path) != expected_hash:
            raise ValueError("Saved query file hash changed")
        selection = np.load(path)["selected"][draw]
        rng = np.random.default_rng(
            np.random.SeedSequence([200000 + draw, [0.05, 0.1, 0.2, 0.4].index(fraction), stream])
        )
        regenerated = np.concatenate(
            [
                rng.choice(p, size=int(n), replace=False)
                for p, n in zip(populations, counts, strict=True)
            ]
        )
        if not np.array_equal(selection, regenerated):
            raise ValueError("Query replay differs from the saved random plan")
        selected_ids = tuple(self.ids[i] for i in selection)
        # Only the saved query IDs reach the reference accessor after plan verification.
        refs = read_references(self.processed, selected_ids)
        queried = FrameOracle(refs, selected_ids).query(selected_ids)
        estimate = estimate_frames(
            self.ids, q, reconstruct_plan(populations, counts, selection), queried
        )
        if (
            abs(estimate.prevalence - recorded.prevalence) > 1e-12
            or abs(estimate.variance - recorded.variance) > 1e-12
        ):
            raise ValueError("Replayed estimate differs from the recorded point/variance")
        chosen_rows = self.public.iloc[selection]
        keys = ["clip_id", "person_a", "person_b"]
        example = (
            chosen_rows.groupby(keys).size().sort_values(ascending=False, kind="stable").index[0]
        )
        public = self.tables[self.lock["selected_temporal"]["feature_set"]]
        mask = np.logical_and.reduce([public[k].eq(v) for k, v in zip(keys, example, strict=True)])
        timeline = public[mask].sort_values("clip_frame_index_1based")
        selected_set = set(selected_ids)
        return {
            "method": method,
            "fraction": fraction,
            "draw": draw,
            "budget": budget,
            "verified": True,
            "query_file_sha256": expected_hash,
            "estimate": estimate.as_dict(),
            "surrogate_mean": float(q.mean()),
            "native_model_mean": self.result["model_only_mean"],
            "example": {k: str(v) for k, v in zip(keys, example, strict=True)},
            "timeline": [
                {
                    "id": r.record_id,
                    "position": int(r.clip_frame_index_1based),
                    "q": float(r.f_q),
                    "context_mean": float(r.f_t_q_mean),
                    "queried": r.record_id in selected_set,
                }
                for r in timeline.itertuples()
            ],
            "queries": [
                {
                    "id": key,
                    "q": float(self.public.iloc[self.positions[key]].f_q),
                    "label": int(queried[key]),
                }
                for key in selected_ids
            ],
            "strata": [
                {"population": len(p), "queries": int(n)}
                for p, n in zip(populations, counts, strict=True)
            ],
            "normal_interval_note": "Approximate; observed undercoverage in repeated audits. "
            "See interval evaluation.",
        }

    def frame(self, record_id):
        from PIL import Image, ImageDraw

        if record_id not in self.positions:
            raise ValueError("Frame must belong to the frozen test population")
        row = self.public.iloc[self.positions[record_id]]
        frame = self.frames.loc[row.frame_id]
        with tarfile.open(self.archives[row.source_id]) as archive:
            member = archive.extractfile(frame.annotation_path)
            if member is None:
                raise ValueError("Registered JPEG is absent from the local archive")
            picture = Image.open(io.BytesIO(member.read())).convert("RGB")
        picture.thumbnail((1100, 700))
        width, height = picture.size
        drawing = ImageDraw.Draw(picture)
        for person, color in [("a", "#57c9ff"), ("b", "#ffbf69")]:
            x, y = row[f"f_head_{person}_center_x"], row[f"f_head_{person}_center_y"]
            w, h = row[f"f_head_{person}_width"], row[f"f_head_{person}_height"]
            box = [
                (x - w / 2) * width,
                (y - h / 2) * height,
                (x + w / 2) * width,
                (y + h / 2) * height,
            ]
            drawing.rectangle(box, outline=color, width=3)
            drawing.text(
                (max(0, box[0]), max(0, box[1] - 16)),
                f"Track {row[f'person_{person}']}",
                fill=color,
            )
        buffer = io.BytesIO()
        picture.save(buffer, format="JPEG", quality=90)
        return buffer.getvalue()
