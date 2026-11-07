"""Plot a saved public pair timeline and its selected audit locations."""

import argparse
import json
import os
from pathlib import Path

import pandas as pd


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    args = parser.parse_args()
    os.environ["MPLCONFIGDIR"] = str((args.replay / "matplotlib-cache").resolve())
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    report = json.loads((args.replay / "replay.json").read_text())
    public = pd.read_csv(args.replay / "public-query-timeline.csv")
    frame = public.clip_frame_index_1based
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.2), sharex=True, layout="constrained")
    axes[0].plot(frame, public.f_q, color="#4063A2", label="Frozen native score q", linewidth=1.3)
    axes[0].plot(frame, public.f_t_q_mean, color="#23836A", label="Temporal neighborhood mean")
    queried = public.selected_query.eq(1)
    axes[0].scatter(
        frame[queried],
        public.loc[queried, "f_q"],
        color="#B0413E",
        marker="|",
        s=120,
        label="Queried pair-frame",
    )
    axes[0].set(ylabel="Probability", ylim=(-0.02, 1.02))
    axes[0].legend(frameon=False, fontsize=8, ncols=3)
    axes[1].plot(frame, public.f_t_q_std, color="#8C5AA5", label="Temporal score SD")
    axes[1].set(xlabel="Relative frame within clip", ylabel="Temporal SD")
    axes[1].legend(frameon=False, fontsize=8)
    for axis in axes:
        axis.grid(alpha=0.15)
    example = report["example"]
    fig.suptitle(
        f"{report['method']} draw {report['draw']}: {example['clip_id']} "
        f"(pair {example['person_a']}, {example['person_b']})",
        fontsize=11,
    )
    fig.savefig(args.replay / "public-query-timeline.png", dpi=240, bbox_inches="tight")
    fig.savefig(args.replay / "public-query-timeline.svg", bbox_inches="tight")
    plt.close(fig)
    print(args.replay / "public-query-timeline.png")


if __name__ == "__main__":
    main()
