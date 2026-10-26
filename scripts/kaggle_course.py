"""Run Kaggle with this project's credentials in an isolated child environment."""

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def isolated_environment(directory: Path, *, direct: bool = False) -> tuple[dict, str]:
    token = (directory / "access_token").read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("Project credential file is empty")
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("KAGGLE_")}
    env["KAGGLE_CONFIG_DIR"] = str(directory.resolve())
    env["KAGGLE_API_TOKEN"] = token
    if direct:
        env = {
            k: v
            for k, v in env.items()
            if k.upper()
            not in {
                "HTTP_PROXY",
                "HTTPS_PROXY",
                "ALL_PROXY",
            }
        }
    return env, token


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=(Path(__file__).resolve().parents[1] / "data/credentials/kaggle-course"),
    )
    parser.add_argument("--direct", action="store_true", help="Bypass proxies in this child only")
    parser.add_argument("args", nargs=argparse.REMAINDER)
    options = parser.parse_args()
    args = options.args[1:] if options.args[:1] == ["--"] else options.args
    if not args:
        parser.error("Supply Kaggle arguments after --")
    if args[:2] in [["auth", "print-access-token"], ["config", "view"]]:
        parser.error("Credential-printing commands are disabled in this project launcher")
    binary = shutil.which("kaggle")
    if binary is None:
        parser.error("Kaggle CLI is not installed")
    try:
        env, token = isolated_environment(options.config_dir, direct=options.direct)
    except (OSError, ValueError):
        parser.exit(2, "Project credential file is missing, unreadable or empty.\n")
    result = subprocess.run([binary, *args], env=env, text=True, capture_output=True)
    for stream, target in [(result.stdout, sys.stdout), (result.stderr, sys.stderr)]:
        sanitized = re.sub(
            r"KGAT_[A-Za-z0-9_-]+", "<redacted>", stream.replace(token, "<redacted>")
        )
        target.write(sanitized)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
