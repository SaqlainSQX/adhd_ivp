"""Download public ChildPlay sources and reproduce official JPEG extraction.

CPU-only Kaggle script. Only public metadata enters this job; no oracle values.
The small default pilot must pass alignment review before a full acquisition.
"""

import csv
import hashlib
import importlib.util
import io
import json
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
from pathlib import Path

CONFIG = globals().get(
    "JOB_CONFIG",
    {
        "mode": "pilot",
        "sources": ["1Aea8BH-PCs", "31lG75MDwSA", "smwfiZd8HLc"],
        "clips_per_source": 1,
        "shard_index": 0,
        "shard_count": 1,
    },
)
SPECIAL_CLIPS = {
    "smwfiZd8HLc_7508-8408-downsampled",
    "smwfiZd8HLc_10346-12974-downsampled",
    "smwfiZd8HLc_16176-16586-downsampled",
    "smwfiZd8HLc_20322-20668-downsampled",
    "31lG75MDwSA_2857-2928",
    "31lG75MDwSA_3180-3306",
    "31lG75MDwSA_4686-4764",
    "EuYseDl2jm8_1869-2033",
    "EuYseDl2jm8_3680-3791",
}


def digest(path):
    result = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as response:
        return response.read()


def main():
    started = time.monotonic()
    root = Path(globals().get("OUTPUT_ROOT", "/kaggle/working"))
    root.mkdir(parents=True, exist_ok=True)
    scratch = Path(globals().get("SCRATCH_ROOT", "/tmp/social-gaze-download"))
    scratch.mkdir(parents=True, exist_ok=True)
    if importlib.util.find_spec("yt_dlp") is None:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "yt-dlp"], check=True)
    import cv2
    import yt_dlp

    report = {
        "config": CONFIG,
        "sources": [],
        "oracle_access": False,
        "opencv_version": cv2.__version__,
        "yt_dlp_version": yt_dlp.version.__version__,
    }
    if CONFIG["mode"] == "pilot" and not CONFIG.get("metadata_archive"):
        for name, url in {
            "mtgs-checkpoint": "https://huggingface.co/api/models/Idiap/mtgs-vsgaze",
            "mtgs-commits": "https://api.github.com/repos/idiap/MTGS/commits?per_page=100",
            "childplay-mirror": "https://huggingface.co/api/datasets/goldpotatoes/ChildPlay/tree/main?recursive=true&limit=1000",
        }.items():
            try:
                (root / f"{name}.json").write_bytes(fetch(url))
            except Exception as error:
                report[name] = {"error": str(error)}
    metadata = (
        Path(CONFIG["metadata_archive"]).read_bytes()
        if CONFIG.get("metadata_archive")
        else fetch("https://zenodo.org/records/8252535/files/ChildPlay-gaze.tar.gz?download=1")
    )
    if hashlib.sha256(metadata).hexdigest() != (
        "4d18bf1abc6ffbf9746a181e2a40588805e7ad1ab85b79024d05f59c0096f773"
    ):
        raise ValueError("Original metadata checksum mismatch")
    with tarfile.open(fileobj=io.BytesIO(metadata), mode="r:gz") as archive:
        with io.TextIOWrapper(
            archive.extractfile("ChildPlay-gaze/clips.csv"), encoding="utf-8"
        ) as handle:
            clips = list(csv.DictReader(handle))
        with io.TextIOWrapper(
            archive.extractfile("ChildPlay-gaze/videos.csv"), encoding="utf-8"
        ) as handle:
            videos = {row["video_id"]: row for row in csv.DictReader(handle)}
    selected = sorted({r["video_id"] for r in clips})
    if CONFIG.get("sources"):
        selected = [s for s in selected if s in CONFIG["sources"]]
    selected = selected[CONFIG["shard_index"] :: CONFIG["shard_count"]]
    report["expected_sources"] = selected
    report_path = root / "acquisition.json"
    if report_path.exists():
        previous = json.loads(report_path.read_text(encoding="utf-8"))
        if previous["config"] != CONFIG:
            raise ValueError("Cannot resume acquisition with a different configuration")
        for item in previous["sources"]:
            if item["status"] == "complete":
                path = root / item["archive"]
                if not path.exists() or digest(path) != item["archive_sha256"]:
                    raise ValueError(
                        "Completed archive changed; choose a new acquisition directory"
                    )
                report["sources"].append(item)
        report["previous_unfinished_sources"] = [
            r["source_id"] for r in previous["sources"] if r["status"] != "complete"
        ]
    completed = {r["source_id"] for r in report["sources"]}

    def save():
        report["elapsed_seconds"] = time.monotonic() - started
        (root / "acquisition.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    for source in selected:
        if source in completed:
            continue
        if shutil.disk_usage(root).free < 5 * 1024**3:
            report["stopped_reason"] = "Less than 5 GiB free; preserve completed archives"
            break
        item = {"source_id": source, "status": "started", "clips": []}
        report["sources"].append(item)
        save()
        video = scratch / f"{source}.mp4"
        capture = None
        try:
            fps = float(videos[source]["fps"])
            # Preserve the original temporal cadence. Never choose 30fps for a 60fps source.
            options = {
                "format": (
                    f"bestvideo[ext=mp4][vcodec^=avc1][fps>={fps - 1}]"
                    f"[fps<={fps + 1}][height<=1080]"
                ),
                "outtmpl": str(video),
                "quiet": True,
                "no_warnings": True,
                "socket_timeout": 30,
                "retries": 2,
                "extractor_retries": 1,
                "noplaylist": True,
                "noprogress": True,
            }
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(
                    f"https://www.youtube.com/watch?v={source}", download=True
                )
            item.update(
                {
                    "format_id": info.get("format_id"),
                    "format_fps": info.get("fps"),
                    "download_width": info.get("width"),
                    "download_height": info.get("height"),
                    "source_video_sha256": digest(video),
                    "video_bytes": video.stat().st_size,
                    "metadata_fps": fps,
                    "metadata_frame_count": int(videos[source]["frame_count"]),
                }
            )
            capture = cv2.VideoCapture(str(video))
            if not capture.isOpened():
                raise ValueError("Downloaded video cannot be decoded")
            item.update(
                {
                    "decoded_fps": capture.get(cv2.CAP_PROP_FPS),
                    "decoded_frame_count": int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
                    "decoded_width": int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "decoded_height": int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                }
            )
            if abs(item["decoded_fps"] - fps) > 0.1:
                raise ValueError("Downloaded video cadence differs from release metadata")
            if item["metadata_frame_count"] > 0:
                delta = item["decoded_frame_count"] - item["metadata_frame_count"]
                item["frame_count_delta"] = delta
                if abs(delta) > CONFIG.get("allow_frame_count_delta", 0):
                    raise ValueError("Source frame count changed; manual alignment required")
                item["alignment_review_required"] = delta != 0
            rows = sorted((r for r in clips if r["video_id"] == source), key=lambda r: r["clip"])
            if CONFIG.get("clips_per_source"):
                # For the downsampled pilot, deliberately include a documented lagged clip.
                rows.sort(key=lambda r: (r["clip"] not in SPECIAL_CLIPS, r["clip"]))
                rows = rows[: CONFIG["clips_per_source"]]
            archive_path = root / f"frames-{source}.tar"
            with tarfile.open(archive_path, "w") as images:
                for row in rows:
                    clip = row["clip"]
                    interval = clip.rsplit("_", 1)[1].replace("-downsampled", "")
                    start = int(interval.split("-")[0])
                    downsampled = clip.endswith("-downsampled")
                    special = clip in SPECIAL_CLIPS
                    capture.set(cv2.CAP_PROP_POS_FRAMES, start - 1 - int(special))
                    count = int(row["frame_count"])
                    ret, frame = capture.read()
                    for relative in range(count):
                        if downsampled:
                            ret, frame = capture.read()
                        if not ret:
                            raise ValueError(f"Decode stopped at {clip}, frame {relative + 1}")
                        expected = start - 1 - int(special) + int(downsampled)
                        expected += (2 if downsampled else 1) * relative
                        observed = round(capture.get(cv2.CAP_PROP_POS_FRAMES)) - 1
                        if observed != expected:
                            raise ValueError("Decoder position does not match mapping")
                        success, encoded = cv2.imencode(".jpg", frame)
                        if not success:
                            raise ValueError("JPEG encoding failed")
                        content = encoded.tobytes()
                        member = tarfile.TarInfo(f"images/{clip}/{source}_{start + relative}.jpg")
                        member.size = len(content)
                        images.addfile(member, io.BytesIO(content))
                        ret, frame = capture.read()
                    item["clips"].append(
                        {
                            "clip_id": clip,
                            "frames": count,
                            "special_lag": special,
                            "downsampled": downsampled,
                        }
                    )
            capture.release()
            item.update(
                {
                    "status": "complete",
                    "archive": archive_path.name,
                    "archive_sha256": digest(archive_path),
                    "archive_bytes": archive_path.stat().st_size,
                }
            )
        except Exception as error:
            item.update({"status": "failed", "error": str(error)[:2000]})
            partial = root / f"frames-{source}.tar"
            if partial.exists():
                partial.unlink()
        finally:
            if capture is not None:
                capture.release()
            # Temporary full source videos are deleted after their verified JPEG archive is saved.
            for temporary in scratch.glob(f"{source}.*"):
                try:
                    temporary.unlink()
                except OSError as error:
                    item.setdefault("cleanup_errors", []).append(str(error))
            save()
            print(source, item["status"], flush=True)
    report["complete"] = len(report["sources"]) == len(selected) and all(
        r["status"] == "complete" for r in report["sources"]
    )
    save()


if __name__ == "__main__":
    main()
