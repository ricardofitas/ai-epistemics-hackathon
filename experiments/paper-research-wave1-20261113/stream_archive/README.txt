Lossless SSE journal archive

Each journal is deterministic gzip, then standard base64 split into parts.
The manifest records SHA-256 hashes and byte lengths at every stage.
No source journal was modified. Each archive part is at most 64 MiB.

Restore into a NEW directory (all hashes are verified automatically):
  python3 reconstruct_stream_journals.py --output /path/to/restored_journals
