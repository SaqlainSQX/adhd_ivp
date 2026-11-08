"""Register the complete T family before binomial endpoint calculations."""

import hashlib
import json
from pathlib import Path


def main():
    sources, cells = {}, []

    def load(name):
        path = Path("docs/research") / (name + ".json")
        sources[path.as_posix()] = hashlib.sha256(
            path.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest()
        return path.as_posix(), json.loads(path.read_text(encoding="utf-8"))

    def add(group, name, source, path, coverage, primary=False):
        k = round(1000 * coverage)
        if abs(coverage - k / 1000) > 1e-12 or not 0 <= k <= 1000:
            raise ValueError("Coverage is not a valid 1000-draw fraction")
        pointer = "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in path)
        cells.append(
            {
                "group": group,
                "id": name,
                "source": source,
                "pointer": pointer,
                "n": 1000,
                "k": k,
                "coverage": coverage,
                "primary": primary,
            }
        )

    source, data = load("main-course-results")
    for method in ["M1", "M2", "M3", "M4", "M5"]:
        for budget in [516, 1032, 2063, 4126]:
            key = f"{method}-b{budget}"
            add(
                "Main",
                key,
                source,
                ["results", key, "intervals", "normal", "coverage"],
                data["results"][key]["intervals"]["normal"]["coverage"],
                method in ["M3", "M4"] and budget == 1032,
            )
    source, data = load("l-transfer-result")
    for method in ["uniform", "K4", "power-score"]:
        for budget in [260, 521, 1043, 2087]:
            key = f"{method}-b{budget}"
            add(
                "UCO",
                key,
                source,
                ["results", key, "intervals", "normal", "coverage"],
                data["results"][key]["intervals"]["normal"]["coverage"],
            )
    for group, file, param, allowed in [
        ("Q", "q-result", "eta", [0, 0.01, 0.02, 0.05]),
        ("R", "r-result", "case", ["clean", "false-positive", "false-negative"]),
    ]:
        source, data = load(file)
        expected = {
            (dataset, method, value)
            for dataset in ["ChildPlay", "UCO"]
            for method in ["K4", "power-score", "uniform"]
            for value in allowed
        }
        actual = [(r["dataset"], r["method"], r[param]) for r in data["rows"]]
        if set(actual) != expected or len(actual) != len(expected):
            raise ValueError("T source family differs from protocol")
        for i, row in enumerate(data["rows"]):
            name = f"{row['dataset']}/{row['method']}/{param}={row[param]}"
            add(group, name, source, ["rows", i, "normal_coverage"], row["normal_coverage"])
    if len(cells) != 74 or sum(c["primary"] for c in cells) != 2:
        raise ValueError("T family size differs")
    protocol = Path("docs/COVERAGE_MC_T.md")
    config = {
        "protocol": protocol.as_posix(),
        "protocol_sha256": hashlib.sha256(
            protocol.read_bytes().replace(b"\r\n", b"\n")
        ).hexdigest(),
        "sources": sources,
        "hash_convention": "text CRLF to LF",
        "alpha": 0.05,
        "family_size": 74,
        "nominal_target": 0.95,
        "cells": cells,
        "new_queries_models_labels": False,
        "seeds": "none; deterministic analysis of existing counts",
    }
    with Path("configs/coverage-mc-t-v1.json").open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(config, indent=2) + "\n")
    print("Registered all74 counts/selectors before T endpoints")


if __name__ == "__main__":
    main()
