"""Retrieve only the frozen HELM Arabic MadinahQA General run archives."""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

from fetch_helm import FILES, fetch

ROOT_URL = "https://storage.googleapis.com/crfm-helm-public/arabic/benchmark_output/"
RELEASES = ("v1.0.0", "v2.0.0")
SUBSET = "Arabic_Language_(General)"


def run_catalogue(root, release):
    data = json.loads((root / release / "run_specs.json").read_text())
    result = {}
    for row in data:
        scenario = row["scenario_spec"]
        if (scenario["class_name"].endswith(".MadinahQAScenario")
                and scenario["args"]["subset"] == SUBSET):
            adapter = row["adapter_spec"]
            model = adapter["model"]
            assert model not in result
            result[model] = (row["name"], adapter)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    entries = [fetch(args.directory, f"releases/{release}/run_specs.json",
                     f"{release}/run_specs.json", ROOT_URL) for release in RELEASES]
    jobs = []
    for release in RELEASES:
        for model, (run, _) in run_catalogue(args.directory, release).items():
            jobs.extend((f"runs/{release}/{quote(run, safe='')}/{name}",
                         f"{release}/{model}/{name}") for name in (*FILES, "stats.json"))
    with ThreadPoolExecutor(max_workers=10) as pool:
        entries.extend(pool.map(lambda job: fetch(args.directory, *job, ROOT_URL), jobs))
    (args.directory / "fetch-manifest.json").write_text(json.dumps(entries, indent=2) + "\n")
    print(f"MadinahQA archive objects available: {sum('sha256' in e for e in entries)}/{len(entries)}",
          flush=True)


if __name__ == "__main__":
    main()
