"""Verify the private, frozen GAMMAF repair execution package without inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess


def load(root: Path):
    config = json.loads((root / "executor-config.json").read_text())
    assert config["study"] == "gammaf-v2-full-options-20261115"
    plan_path = Path(config["plan_path"])
    assert not plan_path.is_absolute() and ".." not in plan_path.parts
    raw = (root / plan_path).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == config["plan_sha256"]
    plan = json.loads(raw)
    assert 0 < int(plan["max_api_calls"]) <= 5000
    assert 0 < float(plan["max_credits"]) <= 100
    freeze = json.loads((root / "FREEZE.json").read_text())
    for name, expected in freeze["files"].items():
        path = Path(name)
        assert not path.is_absolute() and ".." not in path.parts
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == expected, name
    for key in ("preflight_command", "inference_command"):
        assert isinstance(config[key], list) and config[key]
        assert all(isinstance(arg, str) and "\0" not in arg for arg in config[key])
    launch = json.loads((root / "LAUNCH.json").read_text())
    assert launch["study"] == config["study"]
    assert launch["plan_sha256"] == config["plan_sha256"]
    return config


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    config = load(root)
    if args.preflight:
        env = {k: v for k, v in os.environ.items() if k not in {"ADAPTION_API_KEY", "OPENAI_API_KEY", "GITHUB_TOKEN", "GH_TOKEN"}}
        subprocess.run(config["preflight_command"], cwd=root, env=env, check=True)
    print(json.dumps({"freeze_verified": True, "provider_calls": 0, "plan_sha256": config["plan_sha256"]}))


if __name__ == "__main__":
    main()
