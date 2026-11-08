"""Record bounded official dataset HEAD checks; no data, labels or accounts."""

import json
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URLS = {
    "ava_annotations": "https://www.robots.ox.ac.uk/~vgg/research/laeonet/downloads/ava_laeo.tar.gz",
    "uco_frames_v1_1": "http://rabinf24.uco.es/ucolaeo/ucolaeodb_v1.1.tgz",
    "uco_frames_v1_0": "https://www.robots.ox.ac.uk/~vgg/research/laeonet/downloads/UCOLAEO_v1.0_frames.tar.gz",
}


def main():
    output = ROOT / "outputs/external-metadata-j-v1"
    output.mkdir(parents=True, exist_ok=False)
    rows = []
    for candidate, url in URLS.items():
        row = {"candidate": candidate, "requested_url": url, "method": "HEAD",
               "utc": datetime.now(timezone.utc).isoformat()}
        request = urllib.request.Request(
            url, method="HEAD", headers={"User-Agent": "course-gaze-feasibility/1.0"})
        try:
            with urllib.request.urlopen(request, timeout=12) as response:
                row.update(status=response.status,
                           final_host=urllib.parse.urlparse(response.url).hostname,
                           content_type=response.headers.get("Content-Type"),
                           content_length=response.headers.get("Content-Length"),
                           last_modified=response.headers.get("Last-Modified"))
        except urllib.error.HTTPError as error:
            row.update(error_type=type(error).__name__, status=error.code)
        except (urllib.error.URLError, TimeoutError, OSError) as error:
            row.update(error_type=type(error).__name__)
        rows.append(row)
    payload = {"stage": "J-HEAD-only", "complete": True,
               "label_values_read": False, "media_downloaded": False, "requests": rows}
    (output / "access-probes.json").write_text(json.dumps(payload, indent=2) + "\n")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
