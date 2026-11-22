"""Fetch and verify the publisher snapshots without downloading model code."""
import argparse
import json
import shutil
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

from worker import ROOT, sha256

RANGE_SIZE = 16 * 1024**2


def download(job):
    url, destination, length, start, total = job
    if length is not None and destination.is_file() and destination.stat().st_size == length:
        return
    headers = {}
    if length is not None:
        end = start + length - 1
        headers["Range"] = f"bytes={start}-{end}"
    for attempt in range(4):
        pending = destination.with_suffix(".pending")
        try:
            with urlopen(Request(url, headers=headers), timeout=60) as source:
                if length is not None:
                    assert source.status == 206 and source.headers["Content-Range"] == f"bytes {start}-{end}/{total}"
                with pending.open("wb") as output:
                    shutil.copyfileobj(source, output)
            if length is not None and pending.stat().st_size != length:
                raise OSError("Incomplete HTTP range response")
            pending.replace(destination)
            return
        except (OSError, URLError):
            if attempt == 3:
                raise RuntimeError(f"Publisher download failed for {destination.name}") from None
            time.sleep(2 ** attempt)


def queue_assets(root, protocol, pins):
    jobs, assemble = [], []
    for repo, revision in protocol["models"].items():
        directory = root / "weights" / revision
        directory.mkdir(exist_ok=True, parents=True)
        url = f"https://huggingface.co/{repo}/resolve/{revision}/"
        for name in protocol["snapshot_files"]:
            destination = directory / name
            if name != "model.safetensors":
                if not destination.is_file():
                    jobs.append((url + name, destination, None, None, None))
                continue
            pin = pins[repo]
            if destination.is_file() and sha256(destination) == pin["sha256"]:
                continue
            chunks = directory / "chunks"
            chunks.mkdir(exist_ok=True)
            total = pin["bytes"]
            output_parts = []
            # A previously started direct transfer supplies any complete prefix chunks.
            prefix = directory / "model.part"
            prefix_size = prefix.stat().st_size if prefix.is_file() else 0
            for start in range(0, total, RANGE_SIZE):
                length = min(RANGE_SIZE, total - start)
                part = chunks / f"{start:010}.chunk"
                output_parts.append(part)
                if start + length <= prefix_size and not part.is_file():
                    with prefix.open("rb") as existing:
                        existing.seek(start)
                        data = existing.read(length)
                    assert len(data) == length
                    part.write_bytes(data)
                jobs.append((url + name, part, length, start, total))
            assemble.append((repo, destination, output_parts))
    return jobs, assemble


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("runtime", type=Path)
    args = parser.parse_args()
    protocol = json.loads((ROOT / "pilot.json").read_text())
    pins = json.loads((ROOT / "model-weights.json").read_text())
    jobs, assemble = queue_assets(args.runtime, protocol, pins)
    with ThreadPoolExecutor(max_workers=12) as pool:
        for index, _ in enumerate(pool.map(download, jobs), 1):
            if index % 8 == 0:
                print(f"Resolved {index}/{len(jobs)} asset files or ranges", flush=True)
    for repo, destination, parts in assemble:
        pending = destination.with_suffix(".verified")
        with pending.open("wb") as output:
            for part in parts:
                with part.open("rb") as source:
                    shutil.copyfileobj(source, output)
        if sha256(pending) != pins[repo]["sha256"]:
            raise RuntimeError(f"Publisher weight SHA-256 mismatch for {repo}")
        pending.replace(destination)
        for part in parts:
            part.unlink()
        parts[0].parent.rmdir()
        print(f"{repo}: verified publisher SHA-256", flush=True)


if __name__ == "__main__":
    main()
