"""Download archive objects for the frozen HELM MMLU audit."""
import argparse
import gzip
import hashlib
import json
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

ROOT_URL = "https://storage.googleapis.com/crfm-helm-public/mmlu/benchmark_output/"
RELEASE = "v1.0.0"
SUBJECTS = ("abstract_algebra", "college_chemistry", "computer_security", "econometrics", "us_foreign_policy")
FILES = ("scenario_state.json", "per_instance_stats.json")


def fetch(root, remote, local):
    dest = root / local
    if dest.is_file():
        return {"url_path": remote, "file": local, "sha256": hashlib.sha256(dest.read_bytes()).hexdigest()}
    for attempt in range(3):
        try:
            request = Request(ROOT_URL + remote, headers={"Accept-Encoding": "gzip"})
            with urlopen(request, timeout=90) as result:
                data = result.read()
                generation = result.headers.get("x-goog-generation")
            break
        except (TimeoutError, URLError) as error:
            if isinstance(error, HTTPError) and error.code == 404:
                return {"url_path": remote, "file": local, "missing": True}
            if attempt == 2:
                raise
    if data.startswith(b"\x1f\x8b"):
        data = gzip.decompress(data)
    json.loads(data)
    dest.parent.mkdir(exist_ok=True, parents=True)
    pending = dest.with_suffix(".part")
    pending.write_bytes(data)
    pending.replace(dest)
    return {"url_path": remote, "file": local, "sha256": hashlib.sha256(data).hexdigest(),
            "gcs_generation": generation}


def catalogue(directory):
    rows = json.loads((directory / "run_specs.json").read_text())
    runs = {}
    for row in rows:
        model = row["adapter_spec"]["model"]
        subject = row["scenario_spec"]["args"]["subject"]
        assert (model, subject) not in runs
        assert row["adapter_spec"]["method"] == "multiple_choice_joint"
        assert row["adapter_spec"]["eval_splits"] == ["test"]
        runs[model, subject] = row["name"]
    assert set(Counter(m for m, s in runs).values()) == {57} and len({m for m, s in runs}) == 22
    return runs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    base = args.directory
    pref = f"releases/{RELEASE}/"
    jobs = [(pref + "run_specs.json", "run_specs.json"), (pref + "groups/mmlu.json", "published.json")]
    entries = [fetch(base, *job) for job in jobs]
    jobs = [(f"runs/{RELEASE}/{quote(run, safe='')}/{file}", f"{model}/{subject}/{file}")
            for (model, subject), run in catalogue(base).items() if subject in SUBJECTS for file in FILES]
    with ThreadPoolExecutor(max_workers=10) as pool:
        entries.extend(pool.map(lambda job: fetch(base, *job), jobs))
    manifest = base / "fetch-manifest.json"
    manifest.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"HELM archive objects available: {sum('sha256' in x for x in entries)}/{len(entries)}", flush=True)


if __name__ == "__main__":
    main()
