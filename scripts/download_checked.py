"""Download a public artifact with resumable transfer and a required SHA-256 check."""

import argparse
import hashlib
import os
import urllib.request
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("url")
parser.add_argument("destination", type=Path)
parser.add_argument("--sha256", required=True)
parser.add_argument("--direct", action="store_true")
args = parser.parse_args()
if args.direct:
    for key in list(os.environ):
        if key.upper() in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}:
            del os.environ[key]
args.destination.parent.mkdir(parents=True, exist_ok=True)
partial = args.destination.with_suffix(args.destination.suffix + ".partial")
if not args.destination.exists():
    offset = partial.stat().st_size if partial.exists() else 0
    request = urllib.request.Request(
        args.url, headers={"Range": f"bytes={offset}-"} if offset else {}
    )
    with urllib.request.urlopen(request, timeout=90) as response:
        append = offset > 0 and response.status == 206
        if append and not response.headers.get("Content-Range", "").startswith(f"bytes {offset}-"):
            raise ValueError("Unexpected resume Content-Range")
        received = offset if append else 0
        next_progress = received + 256 * 1024**2
        with partial.open("ab" if append else "wb") as target:
            while block := response.read(1024 * 1024):
                target.write(block)
                received += len(block)
                if received >= next_progress:
                    print(f"Received {received / 1024**3:.2f} GiB", flush=True)
                    next_progress += 256 * 1024**2
    candidate = partial
else:
    candidate = args.destination
sha = hashlib.sha256()
with candidate.open("rb") as handle:
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        sha.update(block)
if sha.hexdigest() != args.sha256:
    raise ValueError("Artifact SHA-256 mismatch; partial file preserved")
if candidate == partial:
    partial.replace(args.destination)
print(f"Verified {args.destination.name}: {args.destination.stat().st_size} bytes", flush=True)
