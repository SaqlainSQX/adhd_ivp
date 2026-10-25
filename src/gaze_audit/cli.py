import argparse
from pathlib import Path

from .experiment import generate_demo, run_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="Fixed-corpus mutual-looking prevalence audits")
    sub = parser.add_subparsers(dest="command", required=True)
    demo = sub.add_parser("demo", help="Generate synthetic data and run the pipeline")
    demo.add_argument("--output", type=Path, default=Path("outputs/demo"))
    run = sub.add_parser("run", help="Audit normalized cached predictions and separate labels")
    run.add_argument("--data", type=Path, required=True)
    run.add_argument("--output", type=Path, required=True)
    for command in [demo, run]:
        command.add_argument("--draws", type=int, default=100)
        command.add_argument("--seed", type=int, default=42)
        command.add_argument("--block-length", type=int, default=5)
        command.add_argument("--budgets", type=float, nargs="+", default=[0.05, 0.1, 0.2, 0.4])
    args = parser.parse_args()
    try:
        if args.command == "demo":
            if args.output.exists():
                raise ValueError("Output directory already exists; choose a new run directory")
            data = args.output / "synthetic_data"
            generate_demo(data, args.seed)
            output = args.output / "audit"
        else:
            data, output = args.data, args.output
        report = run_audit(
            data,
            output,
            draws=args.draws,
            seed=args.seed,
            block_length=args.block_length,
            budgets=tuple(args.budgets),
        )
    except (ValueError, FileNotFoundError) as exc:
        parser.exit(2, f"Error: {exc}\n")
    print(f"{'SYNTHETIC DEMO' if report['synthetic'] else 'CACHED-DATA AUDIT'} complete")
    print(
        f"Test records: {report['test_records']}; "
        f"development labels: {report['development_labels']}"
    )
    print(f"Report: {(output / 'report.json').resolve()}")
    print(f"Summary: {(output / 'summary.csv').resolve()}")
