"""Build S only from saved aggregate JSON; no scientific computation or fitting."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "docs/templates/course-guide-s.md"


def normalized_hash(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def build(output):
    output.mkdir(parents=True, exist_ok=False)
    claims, cache = [], {}

    def add(name, source, path, units="pp", scale=1, digits=4, scientific=False):
        file = f"docs/research/{source}.json"
        if file not in cache:
            cache[file] = json.loads((ROOT / file).read_text(encoding="utf-8"))
        value = cache[file]
        for step in path:
            value = value[step]
        pointer = "/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in path)
        values = value if isinstance(value, list) else [value]
        formatted = [format(v * scale, f".{digits}{'e' if scientific else 'f'}") for v in values]
        display = "[" + ", ".join(formatted) + "]" if isinstance(value, list) else formatted[0]
        claims.append(
            {
                "id": name,
                "source": file,
                "json_pointer": pointer,
                "expected": value,
                "units": units,
                "scale": scale,
                "digits": digits,
                "scientific": scientific,
                "display": display,
            }
        )

    add("child_n", "main-course-results", ["test_population_size"], "pair-frames", digits=0)
    add("child_sources", "main-course-results", ["test_source_count"], "sources", digits=0)
    add(
        "attempted",
        "verified-population-manifest",
        ["original_sources_attempted"],
        "sources",
        digits=0,
    )
    add("retained", "verified-population-manifest", ["retained_sources"], "sources", digits=0)
    add("draws", "main-course-results", ["draws_per_method_budget"], "draws", digits=0)
    add("main_checks", "main-course-results", ["sampled_method_runs"], "draws", digits=0)
    add("truth", "main-course-results", ["reference_prevalence"], "%", scale=100)
    add("model_mean", "main-course-results", ["model_only_mean"], "%", scale=100)
    add("model_bias", "main-course-results", ["model_only_bias_pp"])
    for method, key in [("static", "M3"), ("temporal", "M4")]:
        add("main_" + method, "main-course-results", ["results", key + "-b1032", "rmse_pp"])
    main = json.loads((ROOT / "docs/research/main-course-results.json").read_text(encoding="utf-8"))
    index = next(
        i
        for i, r in enumerate(main["comparisons"])
        if r["budget"] == 1032 and r["comparison"] == "M4/M3"
    )
    add("main_ratio", "main-course-results", ["comparisons", index, "rmse_ratio"], "ratio")
    add(
        "main_ci",
        "main-course-results",
        ["comparisons", index, "paired_draw_bootstrap_95pct"],
        "ratio",
    )
    add(
        "child_budget", "timed-d-result", ["results", "K4-b1032", "mean_labels"], "labels", digits=0
    )
    for budget in [516, 1032, 2063, 4126]:
        add(
            f"child_budget_{budget}",
            "timed-d-result",
            ["results", f"K4-b{budget}", "mean_labels"],
            "labels",
            digits=0,
        )
        for method in ["K4", "power-score"]:
            add(
                f"child_{method}_{budget}",
                "timed-d-result",
                ["results", f"{method}-b{budget}", "rmse_pp"],
            )
    for name, field in [("child_ratio", "rmse_ratio"), ("child_ci", "draw_bootstrap_95pct")]:
        add(name, "timed-d-primary-decision", [0, field], "ratio")
    for name, path in [
        ("source_positive", ["positive_sources", "total"]),
        ("source_improved", ["positive_sources", "improved"]),
        ("loo_improved", ["leave_out_b1032", "improved"]),
        ("loo_total", ["leave_out_b1032", "total"]),
    ]:
        add(name, "source-e-assessment", path, "sources", digits=0)
    add("loo_worst", "source-e-assessment", ["leave_out_b1032", "worst_ratio"], "ratio")
    add("f_width_ratio", "weighted-f-result", ["primary", "mean_width_ratio"], "ratio")
    add("f_equal_width", "weighted-f-result", ["results", "K4-b1032-equal", "mean_width_pp"])
    add(
        "f_weighted_width",
        "weighted-f-result",
        ["results", "K4-b1032-inverse-fraction", "mean_width_pp"],
    )
    for name, source in [("g1", "block-g-result"), ("g2", "g2-result")]:
        add(name + "_ratio", source, ["primary", "rmse_ratio"], "ratio")
        add(name + "_ci", source, ["primary", "draw_bootstrap_95pct"], "ratio")
    add("uco_n", "l-transfer-result", ["population_size"], "pair-frames", digits=0)
    add("uco_truth", "l-transfer-result", ["reference_prevalence"], "%", scale=100)
    for budget in [260, 521, 1043, 2087]:
        add(
            f"uco_budget_{budget}",
            "l-transfer-result",
            ["results", f"K4-b{budget}", "mean_labels"],
            "labels",
            digits=0,
        )
        for method in ["uniform", "K4", "power-score"]:
            add(
                f"uco_{method}_{budget}",
                "l-transfer-result",
                ["results", f"{method}-b{budget}", "rmse_pp"],
            )
    for name, key in [("uco_half", "power-score/K4-b521"), ("uco_guided", "K4/uniform-b521")]:
        add(name + "_ratio", "l-transfer-result", ["comparisons", key, "rmse_ratio"], "ratio")
        add(
            name + "_ci", "l-transfer-result", ["comparisons", key, "draw_bootstrap_95pct"], "ratio"
        )
    for name, key in [("uco_normal", "normal"), ("uco_binary", "exact_binary_reference")]:
        add(
            name + "_coverage",
            "l-transfer-result",
            ["results", "K4-b521", "intervals", key, "coverage"],
            "%",
            scale=100,
            digits=1,
        )
        add(
            name + "_width",
            "l-transfer-result",
            ["results", "K4-b521", "intervals", key, "mean_width_pp"],
        )
    m = json.loads((ROOT / "docs/research/m-variance-result.json").read_text(encoding="utf-8"))
    for dataset, budget, prefix in [("ChildPlay", 1032, "m_child"), ("UCO", 521, "m_uco")]:
        index = next(
            i for i, r in enumerate(m["rows"]) if r["dataset"] == dataset and r["budget"] == budget
        )
        add(
            prefix + "_delta",
            "m-variance-result",
            ["rows", index, "half_minus_full_variance"],
            "proportion squared",
            digits=6,
            scientific=True,
        )
        add(
            prefix + "_ratio",
            "m-variance-result",
            ["rows", index, "exact_RMSE_ratio_half_over_full"],
            "ratio",
        )
    for prefix, source, match in [
        ("q_child", "q-result", {"dataset": "ChildPlay", "method": "K4", "eta": 0.02}),
        ("q_uco", "q-result", {"dataset": "UCO", "method": "K4", "eta": 0.02}),
        (
            "r_child_fp",
            "r-result",
            {"dataset": "ChildPlay", "method": "K4", "case": "false-positive"},
        ),
        (
            "r_child_fn",
            "r-result",
            {"dataset": "ChildPlay", "method": "K4", "case": "false-negative"},
        ),
        ("r_uco_fp", "r-result", {"dataset": "UCO", "method": "K4", "case": "false-positive"}),
        ("r_uco_fn", "r-result", {"dataset": "UCO", "method": "K4", "case": "false-negative"}),
    ]:
        data = json.loads((ROOT / f"docs/research/{source}.json").read_text(encoding="utf-8"))
        selected = [
            i for i, r in enumerate(data["rows"]) if all(r[k] == v for k, v in match.items())
        ]
        if len(selected) != 1:
            raise ValueError("Ambiguous accepted row")
        if prefix == "q_child":
            add("q_rate", source, ["rows", selected[0], "eta"], "probability")
        if prefix == "r_child_fp":
            add("r_fp_rate", source, ["rows", selected[0], "a"], "probability")
        if prefix == "r_child_fn":
            add("r_fn_rate", source, ["rows", selected[0], "b"], "probability")
        for metric in ["bias_pp", "rmse_pp", "normal_coverage"]:
            coverage = metric == "normal_coverage"
            add(
                prefix + "_" + metric,
                source,
                ["rows", selected[0], metric],
                "%" if coverage else "pp",
                scale=100 if coverage else 1,
                digits=1 if coverage else 4,
            )
    add("q_checks", "q-independent-validation", ["method_rate_draws_checked"], "draws", digits=0)
    add("r_checks", "r-independent-validation", ["method_case_draws_checked"], "draws", digits=0)
    write(
        output / "registration.json",
        {
            "protocol": "docs/SUBMISSION_SYNTHESIS_S.md",
            "protocol_hash": normalized_hash(ROOT / "docs/SUBMISSION_SYNTHESIS_S.md"),
            "template_hash": normalized_hash(TEMPLATE),
            "implementation_hash": normalized_hash(Path(__file__)),
            "sources": {f: normalized_hash(ROOT / f) for f in cache},
            "scientific_outcomes_created": False,
        },
    )
    text = TEMPLATE.read_text(encoding="utf-8")
    for c in claims:
        marker = "{{" + c["id"] + "}}"
        if marker not in text:
            raise ValueError(f"Unused claim: {c['id']}")
        text = text.replace(marker, c["display"] + "<!-- s:" + c["id"] + " -->")
    if "{{" in text:
        raise ValueError("Unresolved guide claim")
    (output / "course-guide.md").write_text(text, encoding="utf-8")
    write(output / "claim-map.json", {"stage": "S reporting only", "claims": claims})
    write(
        output / "guide-summary.json",
        {
            c["id"]: {"value": c["expected"], "display": c["display"], "units": c["units"]}
            for c in claims
        },
    )
    print(f"Built {len(claims)} claims from {len(cache)} aggregate sources")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "outputs/submission-synthesis-s-v1")
    build(parser.parse_args().output)
