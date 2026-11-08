"""Exact-binomial Monte Carlo coverage intervals for the registered T family."""

import hashlib
import json
from pathlib import Path

from scipy.stats import beta

OUT = Path("outputs/coverage-mc-t-v1")


def write(path, data):
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def interval(k, n, alpha):
    return [
        0.0 if k == 0 else float(beta.ppf(alpha / 2, k, n - k + 1)),
        1.0 if k == n else float(beta.ppf(1 - alpha / 2, k + 1, n - k)),
    ]


def run():
    cfg_path = Path("configs/coverage-mc-t-v1.json")
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=False)
    for name, expected in cfg["sources"].items():
        raw = Path(name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("T registered source changed")
    write(
        OUT / "registration.json",
        {
            "config": cfg,
            "config_sha256": hashlib.sha256(cfg_path.read_bytes()).hexdigest(),
            "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
    )
    # Exact elementary reference cases, before corpus endpoint readout.
    toys = [(0, 1, [0, 0.975]), (1, 1, [0.025, 1]), (1, 2, [1 - 0.975**0.5, 0.975**0.5])]
    maximum = 0.0
    for k, n, expected in toys:
        error = max(abs(a - b) for a, b in zip(interval(k, n, 0.05), expected, strict=True))
        maximum = max(maximum, error)
        if error > 1e-12:
            raise ArithmeticError("T toy interval failed")
    write(
        OUT / "toy-validation.json",
        {"complete": True, "cases": len(toys), "max_endpoint_error": maximum},
    )
    rows = []
    for cell in cfg["cells"]:
        row = dict(cell)
        for name, alpha in [
            ("individual", cfg["alpha"]),
            ("family", cfg["alpha"] / cfg["family_size"]),
        ]:
            bounds = interval(cell["k"], cell["n"], alpha)
            row[name + "_interval"] = bounds
            row[name + "_undercoverage"] = bounds[1] < cfg["nominal_target"]
            row[name + "_overcoverage"] = bounds[0] > cfg["nominal_target"]
        rows.append(row)
    write(
        OUT / "result.json",
        {
            "complete": True,
            "rows": rows,
            "family_size": len(rows),
            "new_queries_models_labels": False,
            "scope": "coverage probability over audit draws on already studied populations",
            "counts": {
                group: {
                    flag: sum(r["group"] == group and r[flag] for r in rows)
                    for flag in [
                        "individual_undercoverage",
                        "family_undercoverage",
                        "individual_overcoverage",
                        "family_overcoverage",
                    ]
                }
                for group in ["Main", "UCO", "Q", "R"]
            },
        },
    )
    write(OUT / "status.json", {"state": "computed_independent_check_pending", "cells": len(rows)})
    print("Computed all74 registered cells; independent validation pending")


if __name__ == "__main__":
    try:
        run()
    except Exception as error:
        if OUT.exists():
            write(OUT / "failure.json", {"type": type(error).__name__, "message": str(error)})
        raise
