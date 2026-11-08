"""Inspect pinned author code and HDF column metadata, without loading labels."""

import ast
import hashlib
import io
import json
import shutil
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import h5py

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-contract-j-v1"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "course-gaze-metadata/1.0"})
    with urllib.request.urlopen(request, timeout=15) as response:
        content = response.read(65537)
    if len(content) > 65536:
        raise ValueError("Metadata response exceeds bounded request")
    return content


def main():
    OUT.mkdir(parents=True, exist_ok=False)
    api = "https://api.github.com/repos/AVAuco/ucolaeodb/commits/master"
    commit = json.loads(fetch(api))["sha"]
    fetched = {}
    names = ["README.md", "code/uco_dbconfig.py", "code/ucolaeo_demo.py", "code/uco_dbutils.py"]
    for name in names:
        content = fetch(f"https://raw.githubusercontent.com/AVAuco/ucolaeodb/{commit}/{name}")
        target = OUT / Path(name).name
        target.write_bytes(content)
        fetched[name] = digest(target)
    # Literal AST extraction: never import or execute the downloaded author code.
    tree = ast.parse((OUT / "uco_dbconfig.py").read_text())
    splits = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ("validationVids", "testVids"):
                    splits[target.id] = ast.literal_eval(node.value)
    assert len(splits["validationVids"]) == 8 and len(splits["testVids"]) == 15
    assert not set(splits["validationVids"]) & set(splits["testVids"])
    schemas = {}
    with tarfile.open(ROOT / "data/research/VSGaze.tar.gz") as archive:
        for split in ("train", "val", "test"):
            member = archive.getmember(f"VSGaze/uco_laeo_{split}.h5")
            content = archive.extractfile(member).read()
            with h5py.File(io.BytesIO(content), "r") as h5:
                group = h5["data"]
                columns = [x.decode() if isinstance(x, bytes) else str(x)
                           for x in group["axis0"][()]]
                schemas[split] = {"h5_sha256": hashlib.sha256(content).hexdigest(),
                                  "bytes": len(content), "row_count": group["axis1"].shape[0],
                                  "columns": columns, "object_values_read": False}
    provenance = []
    for name in ["mtgs-strict-shard-v1", "mtgs-remaining-shard-v1"]:
        path = ROOT / f"outputs/inference/{name}/inference-provenance.json"
        data = json.loads(path.read_text())
        provenance.append({"file": str(path.relative_to(ROOT)), "sha256": digest(path),
                           "historical_anchors_per_second": data["frames_per_second"]})
    anchors = schemas["test"]["row_count"]
    rates = [x["historical_anchors_per_second"] for x in provenance]
    result = {"stage": "J-UCO-schema-and-contract", "created_utc":
              datetime.now(timezone.utc).isoformat(), "author_commit": commit,
              "author_code_sha256": fetched, "official_splits": splits,
              "vsgaze_schemas": schemas,
              "pinned_mtgs_loader_sha256": digest(
                  ROOT / "external/MTGS-pinned/mtgs/datasets/uco_laeo_temporal.py"),
              "free_disk_bytes_observed": shutil.disk_usage(ROOT).free,
              "current_frame_archive_bytes_from_J_HEAD": 4066161261,
              "historical_inference": provenance,
              "test_anchor_minutes_at_historical_rates": [anchors / max(rates) / 60,
                                                           anchors / min(rates) / 60],
              "timing_is_forecast_not_measurement": True,
              "reference_values_loaded": False, "pickle_objects_loaded": False,
              "media_downloaded": False, "inference_started": False,
              "performance_evaluated": False}
    (OUT / "result.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
