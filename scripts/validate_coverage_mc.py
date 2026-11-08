"""T independent checks with standard-library binomial sums, no beta quantiles."""

import hashlib
import json
import math
from functools import reduce
from pathlib import Path

OUT = Path("outputs/coverage-mc-t-v1")


def main():
    cfg = json.loads(Path("configs/coverage-mc-t-v1.json").read_text(encoding="utf-8"))
    result = json.loads((OUT / "result.json").read_text(encoding="utf-8"))
    toy = json.loads((OUT / "toy-validation.json").read_text(encoding="utf-8"))
    if not toy["complete"] or toy["cases"] != 3:
        raise ValueError("T toy gate incomplete")
    if cfg["family_size"] != 74 or cfg["alpha"] != 0.05 or cfg["nominal_target"] != 0.95:
        raise ValueError("T family settings differ")
    if len(result["rows"]) != 74 or len(cfg["cells"]) != 74:
        raise ValueError("T cell count differs")
    sources = {}
    for name, expected in cfg["sources"].items():
        raw = Path(name).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(raw).hexdigest() != expected:
            raise ValueError("T source checksum differs")
        sources[name] = json.loads(raw)
    identifiers = [(r["group"], r["id"]) for r in result["rows"]]
    if len(set(identifiers)) != 74:
        raise ValueError("T duplicate cells")
    if {g: sum(r["group"] == g for r in result["rows"]) for g in ["Main", "UCO", "Q", "R"]} != {
        "Main": 20,
        "UCO": 12,
        "Q": 24,
        "R": 18,
    }:
        raise ValueError("T group cardinalities differ")
    primary = {(r["group"], r["id"]) for r in result["rows"] if r["primary"]}
    if primary != {("Main", "M3-b1032"), ("Main", "M4-b1032")}:
        raise ValueError("T primary endpoints differ")
    n = 1000
    log_choose = [
        math.lgamma(n + 1) - math.lgamma(j + 1) - math.lgamma(n - j + 1) for j in range(n + 1)
    ]
    tail_checks, boundary_checks, max_error = 0, 0, 0.0
    for row, registered in zip(result["rows"], cfg["cells"], strict=True):
        if any(row[k] != v for k, v in registered.items()) or row["n"] != n:
            raise ValueError("T row metadata differs")
        tokens = [s.replace("~1", "/").replace("~0", "~") for s in row["pointer"][1:].split("/")]

        def traverse(value, token):
            return value[int(token)] if isinstance(value, list) else value[token]

        actual = reduce(traverse, tokens, sources[row["source"]])
        if abs(actual - row["k"] / n) > 1e-12 or actual != row["coverage"]:
            raise ValueError("T success count differs")
        k = row["k"]
        for mode, alpha in [("individual", 0.05), ("family", 0.05 / 74)]:
            lo, hi = row[mode + "_interval"]
            if not 0 <= lo <= k / n <= hi <= 1:
                raise ValueError("T interval order invalid")
            for lower, p in [(True, lo), (False, hi)]:
                if (lower and k == 0) or (not lower and k == n):
                    error = abs(p - (0 if lower else 1))
                    boundary_checks += 1
                elif lower and k == n:
                    error = abs(p - math.exp(math.log(alpha / 2) / n))
                    boundary_checks += 1
                elif not lower and k == 0:
                    error = abs(p + math.expm1(math.log(alpha / 2) / n))
                    boundary_checks += 1
                else:
                    js = range(k, n + 1) if lower else range(k + 1)
                    tail = math.fsum(
                        math.exp(log_choose[j] + j * math.log(p) + (n - j) * math.log1p(-p))
                        for j in js
                    )
                    error = abs(tail - alpha / 2)
                    tail_checks += 1
                max_error = max(max_error, error)
                if error > 2e-10:
                    raise ArithmeticError("T independent binomial tail/boundary differs")
            if row[mode + "_undercoverage"] != (hi < 0.95):
                raise ValueError("T undercoverage flag differs")
            if row[mode + "_overcoverage"] != (lo > 0.95):
                raise ValueError("T overcoverage flag differs")
        if (
            row["family_interval"][0] > row["individual_interval"][0]
            or row["family_interval"][1] < row["individual_interval"][1]
        ):
            raise ValueError("T family interval not wider")
    expected_counts = {
        group: {
            flag: sum(r["group"] == group and r[flag] for r in result["rows"])
            for flag in [
                "individual_undercoverage",
                "family_undercoverage",
                "individual_overcoverage",
                "family_overcoverage",
            ]
        }
        for group in ["Main", "UCO", "Q", "R"]
    }
    if expected_counts != result["counts"]:
        raise ValueError("T summary counts differ")
    proof = {
        "complete": True,
        "rows_checked": 74,
        "intervals_checked": 148,
        "binomial_tail_checks": tail_checks,
        "elementary_boundary_checks": boundary_checks,
        "max_tail_or_boundary_absolute_error": max_error,
        "method": "standard-library lgamma log-binomial sums; no beta quantile import",
        "sources_counts_family_flags_and_summaries_verified": True,
        "nominal_containment_not_claimed_as_validation": True,
    }
    (OUT / "independent-validation.json").write_text(
        json.dumps(proof, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(proof, indent=2))


if __name__ == "__main__":
    main()
