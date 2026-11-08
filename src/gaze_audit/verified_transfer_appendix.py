"""Explicit aggregate checksum checks that remain active under Python -O."""

import hashlib
import json
from pathlib import Path

from .transfer_appendix import SOURCES, build_summary


def build_verified_summary(root):
    root = Path(root)
    for source, manifest in SOURCES.items():
        expected = json.loads((root / manifest).read_text())["files"][source]
        actual = hashlib.sha256((root / source).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
        if not isinstance(expected, str) or actual != expected:
            raise ValueError(f"Frozen aggregate differs from its manifest: {source}")
    return build_summary(root)
