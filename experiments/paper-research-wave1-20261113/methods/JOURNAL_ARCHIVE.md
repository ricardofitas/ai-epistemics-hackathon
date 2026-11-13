# Journal archive preparation

Run only after every selected study, recommendation, and consequence journal writer has exited. The required `--runs-complete` flag is the caller's assertion of completion. The helper rejects source changes it observes during packing; it cannot prevent a writer from restarting afterward.

Pack the completed study journals from this directory:

```bash
python3 /workspace/scratch/3a7fad3d11db/paper_research_20261113/pack_stream_journals.py --runs-complete --study-journals /workspace/scratch/3a7fad3d11db/paper_research_20261113/study/stream_journals --output /workspace/scratch/3a7fad3d11db/paper_research_20261113/publication/stream_journal_archive
```

Add `--recommendation-journals /path/to/completed/recommendation/stream_journals` and/or `--consequence-journals /path/to/completed/consequence/stream_journals` to include those runs. Each selected directory must contain at least one direct `*.jsonl` regular file. The output directory must be new.

The helper reads journal bytes without parsing them, leaves the originals untouched, streams gzip with `mtime=0` and an empty filename, and encodes each compressed journal as standard base64. Each text part is at most 64 MiB, safely below a 100 MB Git file limit even when the original or compressed journal is larger. The manifest records SHA-256 and byte lengths for the original, compressed, and concatenated encoded journal, plus each encoded part. Archives exclude source timestamps and absolute source paths. Temporary compressed files are removed and are never placed in the archive.

Publish the archive directory and helper source files through the project's normal Git preparation. Keep the original journal directories excluded from Git; this helper does not change Git configuration, stage files, or publish anything.

Reconstruct the exact original bytes into a new directory:

```bash
python3 /workspace/scratch/3a7fad3d11db/paper_research_20261113/publication/stream_journal_archive/reconstruct_stream_journals.py --output /workspace/scratch/3a7fad3d11db/paper_research_20261113/restored_stream_journals
```

Restoration verifies every hash and size before publishing the restored directory. Both helpers clean up incomplete output staging on failure. Neither prints journal contents.

Run synthetic-only checks:

```bash
python3 -m unittest discover -s /workspace/scratch/3a7fad3d11db/paper_research_20261113 -p test_pack_stream_journals.py -v
```
