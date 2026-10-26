"""Prepare an ignored private Kaggle script job from tracked, reviewable source."""

import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("slug")
    parser.add_argument("--owner", default="watasimycola")
    parser.add_argument("--gpu", action="store_true")
    parser.add_argument("--config", type=Path)
    parser.add_argument("--kernel-source", action="append", default=[])
    args = parser.parse_args()
    root = Path("data/kaggle-jobs") / args.slug
    root.mkdir(parents=True, exist_ok=True)
    code = args.source.read_text(encoding="utf-8")
    if args.config:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        code = f"JOB_CONFIG = {config!r}\n\n" + code
    (root / args.source.name).write_text(code, encoding="utf-8")
    metadata = {
        "id": f"{args.owner}/{args.slug}",
        "title": args.slug.replace("-", " ").title(),
        "code_file": args.source.name,
        "language": "python",
        "kernel_type": "script",
        "is_private": "true",
        "enable_gpu": str(args.gpu).lower(),
        "enable_tpu": "false",
        "enable_internet": "true",
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": args.kernel_source,
        "model_sources": [],
    }
    (root / "kernel-metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(root)


if __name__ == "__main__":
    main()
