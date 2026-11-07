"""Plot saved exploratory ablations beside the unchanged primary comparison."""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main", type=Path, default=Path("docs/research/main-course-results.json"))
    parser.add_argument("--a1", type=Path, default=Path("docs/research/followup-A1-results.json"))
    parser.add_argument("--a2", type=Path, default=Path("docs/research/followup-A2-results.json"))
    parser.add_argument("--output", type=Path, default=Path("reports/course-project"))
    args = parser.parse_args()
    locked, windows, summaries = [json.loads(p.read_text()) for p in [args.main, args.a1, args.a2]]
    if not all(r["complete"] for r in [locked, windows, summaries]):
        raise ValueError("Plot only completed experiments")
    if windows["budget"] != summaries["budget"] or windows["budget"] != 1032:
        raise ValueError("The registered common budget must be 1,032 labels")
    if not all(r["main_result_unchanged"] for r in [windows, summaries]):
        raise ValueError("Follow-ups must preserve the main comparison")
    for experiment in [windows, summaries]:
        if not all(
            check["status"] == "passed" for check in experiment["independent_checks"].values()
        ):
            raise ValueError("Independent follow-up validation must pass before plotting")
    rows = []
    for label, designation, data in [
        ("Static\n(main M3)", "locked main", locked["results"]["M3-b1032"]),
        ("Window 11\n(main M4)", "locked main", locked["results"]["M4-b1032"]),
        ("Window 5\n(A1)", "exploratory ablation", windows["results"]["temporal-w5"]),
        (
            "Window 11\nsummary-only (A2)",
            "exploratory ablation",
            summaries["results"]["summary-only"],
        ),
    ]:
        rows.append(
            {
                "method": label.replace("\n", " "),
                "designation": designation,
                "budget": 1032,
                "draws": 1000,
                "rmse_pp": data["rmse_pp"],
                "bias_pp": data["bias_pp"],
                "normal_coverage": data["intervals"]["normal"]["coverage"],
                "normal_mean_width_pp": data["intervals"]["normal"]["mean_width_pp"],
            }
        )
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / "followup-summary.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    colors = ["#32689c", "#e08b38", "#70a3ce", "#73a380"]
    labels = [r["method"].replace(" (", "\n(") for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), layout="constrained")
    for axis, field, ylabel in [
        (axes[0], "rmse_pp", "RMSE (percentage points; lower is better)"),
        (axes[1], "normal_coverage", "Approximate normal 95% interval coverage"),
    ]:
        values = [r[field] for r in rows]
        bars = axis.bar(range(len(rows)), values, color=colors)
        axis.set_xticks(range(len(rows)), labels, fontsize=8)
        axis.set_ylabel(ylabel)
        axis.bar_label(bars, fmt="%.4f" if field == "rmse_pp" else "%.3f", padding=4)
        axis.grid(axis="y", alpha=0.2)
        axis.set_axisbelow(True)
        axis.set_ylim(0, max(values) * 1.18 if field == "rmse_pp" else 1.05)
    axes[1].axhline(0.95, color="#7d334c", linestyle="--", linewidth=1, label="Nominal 95%")
    axes[1].legend(loc="lower right")
    fig.suptitle(
        "Locked main comparison and exploratory ablations\n"
        "1,032 labels; 1,000 draws; fixed available corpus"
    )
    for extension in ["png", "svg"]:
        fig.savefig(args.output / f"followup-comparison.{extension}", dpi=220)
    plt.close(fig)
    print(args.output / "followup-comparison.png")


if __name__ == "__main__":
    main()
