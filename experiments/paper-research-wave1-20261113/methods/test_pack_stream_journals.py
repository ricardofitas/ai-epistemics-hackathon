"""Synthetic-only checks; no real study journals are accessed."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import random
import tempfile
import unittest
from unittest.mock import patch

import pack_stream_journals as packer
import reconstruct_stream_journals as restore


class ArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "synthetic"
        self.source.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_synthetic(self) -> dict[str, bytes]:
        contents = {
            "empty.jsonl": b"",
            "one.jsonl": b"a",
            "two.jsonl": b"\x00\xff",
            "three.jsonl": b"\x00\xff\n",
            "binary.jsonl": random.Random(20261113).randbytes(49157),
        }
        for name, data in contents.items():
            (self.source / name).write_bytes(data)
        return contents

    def test_round_trip_hashes_boundaries_and_determinism(self) -> None:
        contents = self.write_synthetic()
        archives = [self.root / "archive1", self.root / "archive2"]
        for archive in archives:
            manifest = packer.pack({"study": self.source}, archive, chunk_bytes=64)
            for entry in manifest["journals"]:
                parts = [archive / item["path"] for item in entry["parts"]]
                self.assertTrue(all(part.stat().st_size <= 64 for part in parts))
                self.assertTrue(all(part.stat().st_size % 4 == 0 for part in parts))
                encoded = b"".join(part.read_bytes() for part in parts)
                compressed = base64.b64decode(encoded, validate=True)
                self.assertEqual(hashlib.sha256(encoded).hexdigest(), entry["encoded"]["sha256"])
                self.assertEqual(hashlib.sha256(compressed).hexdigest(), entry["compressed"]["sha256"])
                self.assertEqual(compressed[4:8], b"\x00\x00\x00\x00")
                self.assertEqual(compressed[3] & 8, 0)  # No original filename in gzip header.
        files1 = {path.relative_to(archives[0]): path.read_bytes()
                  for path in archives[0].rglob("*") if path.is_file()}
        files2 = {path.relative_to(archives[1]): path.read_bytes()
                  for path in archives[1].rglob("*") if path.is_file()}
        self.assertEqual(files1, files2)
        output = self.root / "restored"
        self.assertEqual(restore.reconstruct(archives[0], output), len(contents))
        self.assertEqual({path.name: path.read_bytes() for path in (output / "study").iterdir()}, contents)
        self.assertEqual({path.name: path.read_bytes() for path in self.source.iterdir()}, contents)

    def test_optional_groups(self) -> None:
        (self.source / "a.jsonl").write_bytes(b"study\x00")
        groups = {"study": self.source}
        for group in ("recommendation", "consequence"):
            directory = self.root / group
            directory.mkdir()
            (directory / "a.jsonl").write_bytes(group.encode())
            groups[group] = directory
        archive, output = self.root / "archive", self.root / "restored"
        packer.pack(groups, archive, 16)
        self.assertEqual(restore.reconstruct(archive, output), 3)
        for group, directory in groups.items():
            self.assertEqual((output / group / "a.jsonl").read_bytes(), (directory / "a.jsonl").read_bytes())

    def test_streaming_read_boundaries(self) -> None:
        data = random.Random(17).randbytes(restore.READ_BYTES + 7)
        (self.source / "large.jsonl").write_bytes(data)
        archive, output = self.root / "archive", self.root / "restored"
        manifest = packer.pack({"study": self.source}, archive, 8 * 1024 * 1024)
        parts = manifest["journals"][0]["parts"]
        encoded = b"".join((archive / part["path"]).read_bytes() for part in parts)
        self.assertGreater(len(encoded), restore.READ_BYTES)
        self.assertEqual(encoded.count(b"="), len(encoded) - len(encoded.rstrip(b"=")))
        restore.reconstruct(archive, output)
        self.assertEqual((output / "study" / "large.jsonl").read_bytes(), data)

    def test_corruption_leaves_no_output(self) -> None:
        (self.source / "a.jsonl").write_bytes(b"synthetic bytes")
        archive, output = self.root / "archive", self.root / "restored"
        manifest = packer.pack({"study": self.source}, archive, 16)
        part = archive / manifest["journals"][0]["parts"][0]["path"]
        data = part.read_bytes()
        part.write_bytes((b"A" if data[:1] != b"A" else b"B") + data[1:])
        with self.assertRaises(ValueError):
            restore.reconstruct(archive, output)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".restored.building-*")), [])

    def test_changed_source_is_rejected(self) -> None:
        source = self.source / "a.jsonl"
        source.write_bytes(b"synthetic original")
        original = packer.pack_one

        def pack_then_append(*args, **kwargs):
            result = original(*args, **kwargs)
            with source.open("ab") as handle:
                handle.write(b"synthetic change")
            return result

        output = self.root / "archive"
        with patch.object(packer, "pack_one", side_effect=pack_then_append):
            with self.assertRaisesRegex(RuntimeError, "changed"):
                packer.pack({"study": self.source}, output, 16)
        self.assertFalse(output.exists())
        self.assertEqual(list(self.root.glob(".archive.building-*")), [])

    def test_refuses_existing_output_and_symlinks(self) -> None:
        source = self.source / "a.jsonl"
        source.write_bytes(b"synthetic")
        output = self.root / "existing"
        output.mkdir()
        with self.assertRaises(FileExistsError):
            packer.pack({"study": self.source}, output)
        archive = self.root / "archive"
        packer.pack({"study": self.source}, archive, 16)
        with self.assertRaises(FileExistsError):
            restore.reconstruct(archive, output)
        (self.source / "link.jsonl").symlink_to(source)
        with self.assertRaisesRegex(ValueError, "non-symlink"):
            packer.pack({"study": self.source}, self.root / "other")

    def test_rejects_manifest_traversal(self) -> None:
        (self.source / "a.jsonl").write_bytes(b"synthetic")
        archive = self.root / "archive"
        manifest = packer.pack({"study": self.source}, archive, 16)
        manifest["journals"][0]["path"] = "../outside.jsonl"
        (archive / "manifest.json").write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, "Unsafe manifest path"):
            restore.reconstruct(archive, self.root / "restored")
        self.assertFalse((self.root / "outside.jsonl").exists())

    def test_rejects_bad_chunk_sizes(self) -> None:
        (self.source / "a.jsonl").write_bytes(b"synthetic")
        for chunk_bytes in (0, 3, 7, packer.MAX_CHUNK_BYTES + 4):
            with self.assertRaises(ValueError):
                packer.pack({"study": self.source}, self.root / "archive", chunk_bytes)


if __name__ == "__main__":
    unittest.main()
