#!/usr/bin/env python3
"""Preserve completed SSE journals as deterministic, Git-sized text archives.

This program never changes the source journals and never prints their contents.
Only run it once all journal writers have exited. The explicit --runs-complete
flag acknowledges that requirement; metadata checks also reject observed writes.
"""

from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import BinaryIO


DEFAULT_CHUNK_BYTES = 64 * 1024 * 1024
MAX_CHUNK_BYTES = 64 * 1024 * 1024
READ_BYTES = 3 * 1024 * 1024
SCRIPT_DIR = Path(__file__).resolve().parent


def file_identity(path: Path) -> tuple[int, int, int, int, int]:
    info = path.stat(follow_symlinks=False)
    if path.is_symlink() or not path.is_file():
        raise ValueError(f"Expected a regular, non-symlink journal: {path}")
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def snapshot(directory: Path) -> dict[str, tuple[int, int, int, int, int]]:
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError(f"Expected a regular journal directory: {directory}")
    return {path.name: file_identity(path) for path in sorted(directory.glob("*.jsonl"))}


def encode_parts(compressed: BinaryIO, destination: Path, prefix: str,
                 chunk_bytes: int) -> tuple[list[dict], str, int]:
    """Base64 a binary stream, retaining no large binary artifact in the archive."""
    parts: list[dict] = []
    encoded_digest = hashlib.sha256()
    encoded_size = 0
    part_handle = None
    part_digest = hashlib.sha256()
    part_size = 0
    part_path = None

    def finish_part() -> None:
        nonlocal part_handle
        if part_handle is not None:
            part_handle.close()
            parts.append({"path": part_path.as_posix(), "size_bytes": part_size,
                          "sha256": part_digest.hexdigest()})
            part_handle = None

    try:
        while raw := compressed.read(READ_BYTES):
            encoded = base64.b64encode(raw)
            encoded_digest.update(encoded)
            encoded_size += len(encoded)
            offset = 0
            while offset < len(encoded):
                if part_handle is None:
                    part_path = Path(prefix + f".part{len(parts) + 1:05d}")
                    part_handle = (destination / part_path).open("xb")
                    part_digest = hashlib.sha256()
                    part_size = 0
                piece = encoded[offset:offset + chunk_bytes - part_size]
                part_handle.write(piece)
                part_digest.update(piece)
                part_size += len(piece)
                offset += len(piece)
                if part_size == chunk_bytes:
                    finish_part()
        finish_part()
    finally:
        if part_handle is not None:
            part_handle.close()
    return parts, encoded_digest.hexdigest(), encoded_size


def pack_one(source: Path, group: str, destination: Path,
             expected: tuple[int, int, int, int, int], chunk_bytes: int) -> dict:
    original_digest = hashlib.sha256()
    original_size = 0
    with tempfile.TemporaryFile(mode="w+b") as compressed:
        with source.open("rb") as journal:
            descriptor = os.fstat(journal.fileno())
            identity = (descriptor.st_dev, descriptor.st_ino, descriptor.st_size,
                        descriptor.st_mtime_ns, descriptor.st_ctime_ns)
            if identity != expected:
                raise RuntimeError(f"Journal changed before packing: {source}")
            with gzip.GzipFile(fileobj=compressed, mode="wb", filename="",
                               mtime=0, compresslevel=9) as zipper:
                while block := journal.read(READ_BYTES):
                    original_digest.update(block)
                    original_size += len(block)
                    zipper.write(block)
        if file_identity(source) != expected or original_size != expected[2]:
            raise RuntimeError(f"Journal changed during packing: {source}")
        compressed_size = compressed.tell()
        compressed.seek(0)
        compressed_digest = hashlib.sha256()
        while block := compressed.read(READ_BYTES):
            compressed_digest.update(block)
        compressed.seek(0)
        prefix = f"{group}/{source.name}.gz.b64"
        parts, encoded_hash, encoded_size = encode_parts(
            compressed, destination, prefix, chunk_bytes)
    return {
        "path": f"{group}/{source.name}",
        "original": {"sha256": original_digest.hexdigest(), "size_bytes": original_size},
        "compressed": {"sha256": compressed_digest.hexdigest(), "size_bytes": compressed_size},
        "encoded": {"sha256": encoded_hash, "size_bytes": encoded_size},
        "parts": parts,
    }


def pack(groups: dict[str, Path], output: Path,
         chunk_bytes: int = DEFAULT_CHUNK_BYTES) -> dict:
    if chunk_bytes < 4 or chunk_bytes > MAX_CHUNK_BYTES or chunk_bytes % 4:
        raise ValueError("Chunk size must be a multiple of 4, from 4 through 67108864 bytes")
    output = output.absolute()
    if output.exists() or output.is_symlink():
        raise FileExistsError(f"Archive output already exists: {output}")
    if set(groups) - {"study", "recommendation", "consequence"} or "study" not in groups:
        raise ValueError("A study group is required; only the three documented groups are supported")
    groups = {group: directory.absolute() for group, directory in groups.items()}
    for directory in groups.values():
        if output == directory or output in directory.parents or directory in output.parents:
            raise ValueError("Archive output and source journal directories must not overlap")
    before = {group: snapshot(directory) for group, directory in groups.items()}
    for group, files in before.items():
        if not files:
            raise ValueError(f"No .jsonl journals found for {group}: {groups[group]}")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.building-", dir=output.parent))
    try:
        journals = []
        for group in sorted(groups):
            (staging / group).mkdir()
            for name, identity in before[group].items():
                journals.append(pack_one(groups[group] / name, group, staging, identity, chunk_bytes))
        after = {group: snapshot(directory) for group, directory in groups.items()}
        if after != before:
            raise RuntimeError("Journal directories changed during packing; stop all writers and retry")
        manifest = {
            "format": "sse-journal-gzip-base64", "format_version": 1,
            "gzip": {"mtime": 0, "filename": "", "compression_level": 9},
            "base64": {"alphabet": "standard", "line_wrapping": False,
                       "max_part_size_bytes": chunk_bytes},
            "journals": journals,
        }
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        shutil.copyfile(SCRIPT_DIR / "reconstruct_stream_journals.py",
                        staging / "reconstruct_stream_journals.py")
        (staging / "README.txt").write_text(
            "Lossless SSE journal archive\n\n"
            "Each journal is deterministic gzip, then standard base64 split into parts.\n"
            "The manifest records SHA-256 hashes and byte lengths at every stage.\n"
            "No source journal was modified. Each archive part is at most 64 MiB.\n\n"
            "Restore into a NEW directory (all hashes are verified automatically):\n"
            "  python3 reconstruct_stream_journals.py --output /path/to/restored_journals\n",
            encoding="utf-8")
        if output.exists() or output.is_symlink():
            raise FileExistsError(f"Archive output appeared during packing: {output}")
        staging.rename(output)
        return manifest
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-complete", action="store_true",
                        help="Required assertion that ALL selected journal writers have exited")
    parser.add_argument("--study-journals", type=Path,
                        default=SCRIPT_DIR / "study" / "stream_journals")
    parser.add_argument("--recommendation-journals", type=Path)
    parser.add_argument("--consequence-journals", type=Path)
    parser.add_argument("--output", type=Path,
                        default=SCRIPT_DIR / "publication" / "stream_journal_archive")
    parser.add_argument("--chunk-bytes", type=int, default=DEFAULT_CHUNK_BYTES,
                        help="Base64 part size, a multiple of 4 and at most 67108864")
    args = parser.parse_args()
    if not args.runs_complete:
        parser.error("--runs-complete is required; do not pack live journals")
    groups = {"study": args.study_journals}
    if args.recommendation_journals is not None:
        groups["recommendation"] = args.recommendation_journals
    if args.consequence_journals is not None:
        groups["consequence"] = args.consequence_journals
    try:
        manifest = pack(groups, args.output, args.chunk_bytes)
    except (OSError, ValueError, RuntimeError) as error:
        parser.exit(1, f"Archive not created: {error}\n")
    total = sum(entry["original"]["size_bytes"] for entry in manifest["journals"])
    print(f"Archived {len(manifest['journals'])} journals ({total} original bytes) to {args.output}")


if __name__ == "__main__":
    main()
