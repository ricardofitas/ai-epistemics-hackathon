#!/usr/bin/env python3
"""Download only the 15 checksummed English MC2 files listed in a frozen manifest."""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    parser.add_argument("output_dir", type=Path, help="Data root used by audit_real_traces.py")
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text())
    if manifest["revision"] != "2b09f71e86d98b20fc3ef145b57fd56e9adb963f" or len(manifest["files"]) != 15:
        raise ValueError("Unexpected manifest revision or file count")

    def fetch(entry):
        relative = Path(entry["path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe relative path")
        destination = args.output_dir / "data" / relative
        if destination.exists():
            data = destination.read_bytes()
        else:
            with urllib.request.urlopen(entry["url"], timeout=90) as response:
                data = response.read()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"Checksum or size mismatch: {entry['path']}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(data)
        return len(data)

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        sizes = list(executor.map(fetch, manifest["files"]))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "download_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"verified_files": len(sizes), "total_bytes": sum(sizes)}))


if __name__ == "__main__":
    main()
