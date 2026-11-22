"""Download the BEIR publisher's pinned SciFact sources."""
import argparse
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

PINS = {
    "corpus/corpus-00000-of-00001.parquet": ("scifact", "b3b5335604bf5ee3c4447671af975ea25143d4f5"),
    "queries/queries-00000-of-00001.parquet": ("scifact", "b3b5335604bf5ee3c4447671af975ea25143d4f5"),
    "train.tsv": ("scifact-qrels", "2938d17dc3b09882fdb8c12bbbe2e2dc0e75a029"),
    "test.tsv": ("scifact-qrels", "2938d17dc3b09882fdb8c12bbbe2e2dc0e75a029"),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    def fetch(item):
        name, (repo, rev) = item
        url = f"https://huggingface.co/datasets/BeIR/{repo}/resolve/{rev}/{name}"
        with urlopen(url, timeout=40) as response:
            data = response.read()
        path = args.output / Path(name).name
        path.write_bytes(data)
        return path.name, {"url": url, "sha256": hashlib.sha256(data).hexdigest()}

    with ThreadPoolExecutor(max_workers=4) as pool:
        manifest = dict(pool.map(fetch, PINS.items()))
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


if __name__ == "__main__":
    main()
