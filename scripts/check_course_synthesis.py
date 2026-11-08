"""Independently resolve S claims, rendered markers, paths and accepted evidence."""

import argparse
import hashlib
import json
import math
import re
from functools import reduce
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def normalized_sha(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def validate(bundle):
    registration = read_json(bundle / "registration.json")
    claims = read_json(bundle / "claim-map.json")["claims"]
    summary = read_json(bundle / "guide-summary.json")
    guide = (bundle / "course-guide.md").read_text(encoding="utf-8")
    for name, expected in registration["sources"].items():
        if normalized_sha(ROOT / name) != expected:
            raise ValueError(f"S source checksum differs: {name}")
    identifiers = [c["id"] for c in claims]
    if len(set(identifiers)) != len(claims) or set(summary) != set(identifiers):
        raise ValueError("S duplicate or missing claims")
    for claim in claims:
        if claim["source"] not in registration["sources"]:
            raise ValueError("S unregistered source")
        # Independent RFC6901 traversal; primary uses typed key/index lists.
        steps = [
            s.replace("~1", "/").replace("~0", "~") for s in claim["json_pointer"][1:].split("/")
        ]

        def step(value, token):
            return value[int(token)] if isinstance(value, list) else value[token]

        actual = reduce(step, steps, read_json(ROOT / claim["source"]))
        if actual != claim["expected"] or summary[claim["id"]]["value"] != actual:
            raise ValueError(f"S source/summary mismatch: {claim['id']}")
        vals = actual if isinstance(actual, list) else [actual]
        if any(
            isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v)
            for v in vals
        ):
            raise ValueError("S nonnumeric metric")
        fmt = "." + str(claim["digits"]) + ("e" if claim["scientific"] else "f")
        labels = [format(v * claim["scale"], fmt) for v in vals]
        display = "[" + ", ".join(labels) + "]" if isinstance(actual, list) else labels[0]
        if claim["display"] != display or summary[claim["id"]] != {
            "value": actual,
            "display": display,
            "units": claim["units"],
        }:
            raise ValueError(f"S display/units mismatch: {claim['id']}")
        if display + "<!-- s:" + claim["id"] + " -->" not in guide:
            raise ValueError(f"S rendered claim missing or changed: {claim['id']}")
    if set(re.findall(r"<!-- s:([^ ]+) -->", guide)) != set(identifiers) or "{{" in guide:
        raise ValueError("S unresolved or unknown guide markers")
    links = re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", guide)
    for link in links:
        if "://" in link or link.startswith("#"):
            continue
        # Guide's intended destination is docs/COURSE_PROJECT_GUIDE_S.md.
        target = (ROOT / "docs" / link).resolve()
        # S aggregate exports are installed only after this successful check.
        if link == "research/s-claim-map.json":
            target = bundle / "claim-map.json"
        if not target.is_file():
            raise ValueError(f"S broken local link: {link}")
    prior = 0
    for path in (ROOT / "docs/research").glob("*evidence-manifest.json"):
        if path.name == "s-evidence-manifest.json":
            continue
        for name, expected in read_json(path).get("files", {}).items():
            raw = (ROOT / name).read_bytes()
            if expected not in (
                hashlib.sha256(raw).hexdigest(),
                hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest(),
            ):
                raise ValueError(f"S prior evidence changed: {name}")
            prior += 1
    frozen = read_json(ROOT / "docs/research/timed-d-registration.json")["config"]["frozen_hashes"]
    for name, key in [
        ("evaluation/result.json", "main_result"),
        ("development/policy-lock.json", "main_policy_lock"),
    ]:
        raw = (ROOT / "outputs/experiments/course-20261107-v1" / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != frozen[key]:
            raise ValueError("S frozen main file differs")
    return {
        "complete": True,
        "claims_independently_resolved": len(claims),
        "aggregate_sources": len(registration["sources"]),
        "local_links_checked": len(links),
        "prior_manifest_entries_checked": prior,
        "main_result_and_lock_unchanged": True,
        "scientific_outcomes_created": False,
        "guide_sha256": normalized_sha(bundle / "course-guide.md"),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle", type=Path, default=ROOT / "outputs/submission-synthesis-s-v1")
    parser.add_argument("--proof", type=Path)
    args = parser.parse_args()
    result = validate(args.bundle)
    text = json.dumps(result, indent=2) + "\n"
    if args.proof:
        with args.proof.open("x", encoding="utf-8") as handle:
            handle.write(text)
    print(text)
