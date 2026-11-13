#!/usr/bin/env python3
"""Reconstruct and verify original SSE journal bytes from a text archive."""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile


READ_BYTES = 4 * 1024 * 1024


def safe_path(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or "\\" in relative:
        raise ValueError("Invalid manifest path")
    path = PurePosixPath(relative)
    if path.is_absolute() or not path.parts or any(piece in {".", ".."} for piece in path.parts):
        raise ValueError("Unsafe manifest path")
    candidate = root.joinpath(*path.parts)
    if not candidate.resolve().is_relative_to(root.resolve()):
        raise ValueError("Manifest path leaves the archive directory")
    return candidate


def check_record(record: dict, digest: object, size: int, stage: str) -> None:
    if size != record["size_bytes"] or digest.hexdigest() != record["sha256"]:
        raise ValueError(f"{stage} hash or size mismatch")


def restore_one(archive: Path, output: Path, entry: dict) -> None:
    original_path = safe_path(output, entry["path"])
    original_path.parent.mkdir(parents=True, exist_ok=True)
    encoded_digest = hashlib.sha256()
    encoded_size = 0
    compressed_digest = hashlib.sha256()
    compressed_size = 0
    with tempfile.TemporaryFile(mode="w+b") as compressed:
        for part in entry["parts"]:
            path = safe_path(archive, part["path"])
            if path.is_symlink() or not path.is_file():
                raise ValueError("Archive part must be a regular file")
            part_digest = hashlib.sha256()
            part_size = 0
            with path.open("rb") as source:
                while encoded := source.read(READ_BYTES):
                    part_digest.update(encoded)
                    part_size += len(encoded)
                    encoded_digest.update(encoded)
                    encoded_size += len(encoded)
                    raw = base64.b64decode(encoded, validate=True)
                    compressed_digest.update(raw)
                    compressed_size += len(raw)
                    compressed.write(raw)
            check_record(part, part_digest, part_size, "Encoded part")
        check_record(entry["encoded"], encoded_digest, encoded_size, "Encoded journal")
        check_record(entry["compressed"], compressed_digest, compressed_size, "Compressed journal")
        compressed.seek(0)
        original_digest = hashlib.sha256()
        original_size = 0
        with gzip.GzipFile(fileobj=compressed, mode="rb") as source, original_path.open("xb") as target:
            while raw := source.read(READ_BYTES):
                original_digest.update(raw)
                original_size += len(raw)
                target.write(raw)
        check_record(entry["original"], original_digest, original_size, "Original journal")


def reconstruct(archive: Path, output: Path) -> int:
    archive = archive.absolute()
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Restore output already exists: {output}")
    if output == archive or output in archive.parents or archive in output.parents:
        raise ValueError("Restore output and archive directories must not overlap")
    manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("format") != "sse-journal-gzip-base64" or manifest.get("format_version") != 1:
        raise ValueError("Unsupported archive format")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        for entry in manifest["journals"]:
            restore_one(archive, staging, entry)
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Restore output appeared during verification: {output}")
        staging.rename(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return len(manifest["journals"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path, required=True, help="New directory for original journal bytes")
    args = parser.parse_args()
    try:
        count = reconstruct(args.archive, args.output)
    except (OSError, ValueError, RuntimeError, KeyError, TypeError, EOFError) as error:
        parser.exit(1, f"Reconstruction failed: {error}\n")
    print(f"Verified and restored {count} journals to {args.output}")


if __name__ == "__main__":
    main()
