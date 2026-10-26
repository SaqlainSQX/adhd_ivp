"""CPU-only public input discovery for Kaggle; no project secrets or oracle labels."""

import hashlib
import json
import urllib.request
from pathlib import Path


def fetch(url, limit=64 * 1024 * 1024):
    request = urllib.request.Request(url, headers={"User-Agent": "social-gaze-course-project/0.1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
        if len(data) > limit:
            raise ValueError("Response exceeds the declared discovery download limit")
        return data


def main():
    output = Path("/kaggle/working")
    if not output.exists():
        output = Path("outputs/discovery")
        output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, url in {
        "mtgs_commit": "https://api.github.com/repos/idiap/MTGS/commits/main",
        "mtgs_tree": "https://api.github.com/repos/idiap/MTGS/git/trees/main?recursive=1",
        "cp_gaze_files": "https://huggingface.co/api/datasets/kunli-cs/CP_gaze/tree/main?recursive=true&limit=1000",
        "childplay_release": "https://zenodo.org/api/records/8252535",
    }.items():
        try:
            data = json.loads(fetch(url))
            (output / f"{name}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
            results[name] = {"ok": True, "url": url}
            print(name, "OK", flush=True)
        except Exception as error:
            results[name] = {"ok": False, "url": url, "error": str(error)}
            print(name, type(error).__name__, flush=True)
    try:
        commit_file = output / "mtgs_commit.json"
        if commit_file.exists():
            revision = json.loads(commit_file.read_text())["sha"]
            data = fetch(f"https://codeload.github.com/idiap/MTGS/zip/{revision}")
            (output / "MTGS-source.zip").write_bytes(data)
            results["mtgs_source"] = {
                "ok": True,
                "revision": revision,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
    except Exception as error:
        results["mtgs_source"] = {"ok": False, "error": str(error)}
    try:
        data = fetch("https://zenodo.org/records/8252535/files/ChildPlay-gaze.tar.gz?download=1")
        if hashlib.md5(data).hexdigest() != "e48a6d0b4bd04f884f86509b022c5f35":
            raise ValueError("Official ChildPlay metadata archive checksum mismatch")
        (output / "ChildPlay-gaze.tar.gz").write_bytes(data)
        results["childplay_metadata"] = {
            "ok": True,
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    except Exception as error:
        results["childplay_metadata"] = {"ok": False, "error": str(error)}
    (output / "discovery-result.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
