"""Public media availability probe; no cookies, login bypass or GPU use."""

import csv
import io
import json
import subprocess
import sys
import tarfile
import urllib.request
from pathlib import Path


def fetch_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    root = Path("/kaggle/working")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], check=True)
    import yt_dlp

    with urllib.request.urlopen(
        "https://zenodo.org/records/8252535/files/ChildPlay-gaze.tar.gz?download=1", timeout=60
    ) as response:
        metadata = response.read()
    with tarfile.open(fileobj=io.BytesIO(metadata), mode="r:gz") as archive:
        with io.TextIOWrapper(
            archive.extractfile("ChildPlay-gaze/clips.csv"), encoding="utf-8"
        ) as handle:
            clips = list(csv.DictReader(handle))
    sources = {
        split: sorted({r["video_id"] for r in clips if r["split"] == split})
        for split in ["train", "val", "test"]
    }
    selected = sources["train"][:2] + sources["val"][:1] + sources["test"][:2]
    results = {"probe_sources": [], "youtube_requires_no_cookie_workflow": True, "mirrors": {}}
    options = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "socket_timeout": 15,
        "retries": 0,
        "extractor_retries": 0,
    }
    for video_id in selected:
        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(
                    f"https://www.youtube.com/watch?v={video_id}", download=False
                )
            results["probe_sources"].append(
                {
                    "source_id": video_id,
                    "available": True,
                    "duration": info.get("duration"),
                    "format_count": len(info.get("formats", [])),
                }
            )
        except Exception as error:
            results["probe_sources"].append(
                {"source_id": video_id, "available": False, "error": str(error)[:1200]}
            )
        (root / "media-probe.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(video_id, results["probe_sources"][-1]["available"], flush=True)
    for query in ["childplay", "childgaze"]:
        try:
            results["mirrors"][query] = fetch_json(
                f"https://huggingface.co/api/datasets?search={query}&limit=30"
            )
        except Exception as error:
            results["mirrors"][query] = {"error": str(error)}
    (root / "media-probe.json").write_text(json.dumps(results, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
