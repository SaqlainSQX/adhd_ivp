"""Pin U inputs, budgets and query streams before fitting coefficients."""

import hashlib
import json
from pathlib import Path


def main():
    prior = json.loads(Path("configs/query-noise-q-v2.json").read_text(encoding="utf-8"))
    paths = set(prior["input_sha256"])
    paths.add("docs/STRATUM_WEIGHTS_U.md")
    designs = []
    for name, code, folder in [
        ("ChildPlay", 1, "timed-d-20261108-v1"),
        ("UCO", 2, "uco-transfer-l-v1"),
    ]:
        base = Path("outputs/experiments") / folder
        manifest = json.loads((base / "query-manifest.json").read_text(encoding="utf-8"))
        for row in manifest:
            if row.get("policy", row.get("design")) != "K4":
                continue
            query = (base / row["file"]).as_posix()
            paths.add(query)
            designs.append(
                {
                    "dataset": name,
                    "dataset_code": code,
                    "base": base.as_posix(),
                    "budget": row["budget"],
                    "budget_index": row["budget_index"],
                    "stream": row["stream"],
                    "counts": row["counts"],
                    "query": query,
                }
            )
    if len(designs) != 8:
        raise ValueError("U expected eight K4 designs")
    cfg = {
        "protocol": "docs/STRATUM_WEIGHTS_U.md",
        "training_rows": 191956,
        "training_sources": 40,
        "draws": 1000,
        "bootstrap_resamples": 2000,
        "methods": ["full", "half", "global", "stratum"],
        "comparisons": [["stratum", "full"], ["stratum", "half"], ["global", "full"]],
        "minimum_count": 2,
        "minimum_q_ss": 1e-12,
        "clip": [0, 1],
        "cuts_side": "left",
        "rng_seed_start": 200000,
        "bootstrap_seed": "SeedSequence([820000+dataset_code*100+budget_index,1,93])",
        "designs": designs,
        "expected_draw_calculations": 32000,
        "input_sha256": {
            p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in sorted(paths)
        },
    }
    with Path("configs/stratum-weights-u-v1.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(cfg, indent=2) + "\n")
    print("Registered U before coefficients/outcomes; eight designs, four fixed reporting arms")


if __name__ == "__main__":
    main()
