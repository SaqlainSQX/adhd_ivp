"""Run the registered K1 supplied-frame download with durable status and resume."""

import hashlib
import json
import msvcrt
import os
import shutil
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/uco-acquisition-k-v1"
DEST = ROOT / "data/raw/uco/acquisition-k-v1"
URL = "http://rabinf24.uco.es/ucolaeo/ucolaeodb_v1.1.tgz"
EXPECTED = 4066161261
MODIFIED = "Tue, 06 Apr 2021 14:59:08 GMT"


def now():
    return datetime.now(timezone.utc).isoformat()


def save(state):
    temporary = OUT / f"status-{os.getpid()}.tmp"
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(OUT / "status.json")


def download():
    DEST.mkdir(parents=True, exist_ok=True)
    partial = DEST / "ucolaeodb_v1.1.tgz.part"
    complete = DEST / "ucolaeodb_v1.1.tgz"
    if complete.exists():
        raise FileExistsError("Completed archive exists; verify it instead of redownloading")
    if shutil.disk_usage(ROOT).free < 24 * 1024**3:
        raise RuntimeError("Registered free-space gate failed")
    request = urllib.request.Request(URL, method="HEAD")
    with urllib.request.urlopen(request, timeout=12) as response:
        if int(response.headers.get("Content-Length", -1)) != EXPECTED:
            raise ValueError("Remote release byte count changed")
        if response.headers.get("Last-Modified") != MODIFIED:
            raise ValueError("Remote release modification date changed")
    starting_bytes = partial.stat().st_size if partial.exists() else 0
    if starting_bytes > EXPECTED:
        raise ValueError("Partial archive larger than registered release")
    attempt = 1 + len(list(OUT.glob("command-*.json")))
    args = ["curl.exe", "--location", "--fail", "--continue-at", "-",
            "--retry", "3", "--retry-delay", "5", "--connect-timeout", "20",
            "--max-time", "3600", "--max-filesize", str(EXPECTED),
            "--speed-limit", "1024", "--speed-time", "120", "--silent", "--show-error",
            "--dump-header", str(OUT / f"headers-{attempt}.txt"),
            "--output", str(partial), URL]
    (OUT / f"command-{attempt}.json").write_text(json.dumps(args, indent=2) + "\n")
    state = {"stage": "K1-download", "status": "running", "attempt": attempt,
             "wrapper_pid": os.getpid(), "started_utc": now(), "url": URL,
             "expected_bytes": EXPECTED, "starting_bytes": starting_bytes,
             "protocol": "docs/UCO_ACQUISITION_K.md", "media_extracted": False,
             "inference_started": False, "label_values_read": False}
    with (OUT / f"curl-{attempt}.log").open("wb") as log:
        process = subprocess.Popen(args, cwd=ROOT, stdout=log, stderr=log)
        state["curl_pid"] = process.pid
        started = time.monotonic()
        try:
            while process.poll() is None:
                state.update(updated_utc=now(), bytes=partial.stat().st_size
                             if partial.exists() else 0)
                save(state)
                if time.monotonic() - started >= 3600:
                    process.terminate()
                    process.wait()
                    break
                time.sleep(10)
        except BaseException:
            process.terminate()
            process.wait()
            raise
    state.update(exit_code=process.returncode, updated_utc=now(),
                 bytes=partial.stat().st_size if partial.exists() else 0)
    if process.returncode or state["bytes"] != EXPECTED:
        state["status"] = "failed_resume_available"
        save(state)
        raise RuntimeError("Download did not complete; preserve partial file and attempt logs")
    state["status"] = "hashing"
    save(state)
    with partial.open("rb") as handle:
        state["sha256"] = hashlib.file_digest(handle, "sha256").hexdigest()
    partial.rename(complete)
    state.update(status="download_complete_alignment_pending", completed_utc=now(),
                 file=str(complete.relative_to(ROOT)))
    save(state)
    print(json.dumps(state, indent=2), flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    # OS releases this advisory lock even if a prior helper crashes.
    with (OUT / "download.lock").open("a+b") as lock:
        lock.seek(0, 2)
        if not lock.tell():
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        try:
            download()
        except Exception as error:
            failure = {"utc": now(), "error_type": type(error).__name__,
                       "message": str(error), "pid": os.getpid()}
            (OUT / f"failure-{time.time_ns()}.json").write_text(
                json.dumps(failure, indent=2) + "\n")
            raise
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == "__main__":
    main()
