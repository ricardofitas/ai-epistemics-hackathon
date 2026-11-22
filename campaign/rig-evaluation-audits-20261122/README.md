# Evaluation audits on the local rig

This campaign starts from revision `0224dc282a4b6e20c423dd79f34b5c54b3667ddd` and tracks the owner coordination goal `01a202e3-62ac-7e62-9b1d-b62d6c5825b3`. [The campaign results](RESULTS.md) summarize the completed runs. The decision record is in [RELATED-WORK.md](RELATED-WORK.md). The frozen WinoGrande and HELM methods are in [PROTOCOL.md](PROTOCOL.md) and [ARCHIVE-PROTOCOL.md](ARCHIVE-PROTOCOL.md).

## Replay ScienceQA on CPU

Reuse the original archive directory if available. The script can also fetch its pinned sources with `--fetch`.

```bash
python3 -B evidence/scienceqa-20261115/audit_science.py --data /path/to/archive/raw --out /path/to/runtime/cpu-replay
```

[The independently verified receipt](receipts/scienceqa-cpu.json) records the manuscript and table hashes. The saved GPT-3 scoring reproduces 3,188/4,241 on the official full set and 1,360/2,017 on exactly the image questions. Four published comparisons reverse after matching images and one becomes a tie at published precision. The 20 comparisons share one GPT-3 arm and one comparator source.

## Run WinoGrande

Use Python 3.12 with CUDA-enabled PyTorch 2.8.0, Transformers 4.51.3, and a working NVIDIA driver. On the rig the existing PyTorch is CUDA 12.6. Set explicit GPU UUID and PCI identity and the matching BOINC RPC endpoint in the protocol when replicating on a different machine. The published run's receipt fingerprints the original protocol. The worker checks RPC status and available VRAM while holding the per-UUID advisory lock. BOINC's RTX 4060 instance is on port 31418. The campaign reserves no BOINC capacity and stops no BOINC or H6 processes.

From the repository root, with the runtime outside the Git tree and dependencies importable using the selected Python:

```bash
campaign=campaign/rig-evaluation-audits-20261122
runtime=/path/to/runtime
mkdir -p "$runtime/raw" "$runtime/weights"
wget -O "$runtime/raw/winogrande_1.1.zip" https://storage.googleapis.com/ai2-mosaic/public/winogrande/winogrande_1.1.zip
python3 -B "$campaign/freeze.py" "$runtime/raw/winogrande_1.1.zip" "$runtime/rebuilt-items.json"
cmp "$runtime/rebuilt-items.json" "$campaign/frozen-items.json"
python3 -B "$campaign/stage_models.py" "$runtime"
touch "$runtime/packages.ready"
bash "$campaign/launch.sh" "$runtime" wino-rtx4060-20261122-p01 ../first-gpu-receipt.json
```

For the BF16 forced-choice follow-up, pass `forced-choice-bf16.json` as the fifth argument to `launch.sh` and use the follow-up run ID and receipt path. See [the follow-up protocol](FORCED-CHOICE-PROTOCOL.md) and [GPU results](WINO-RESULTS.md).

For a restart, keep the same run ID and receipt path, verify the previous transient unit has ended, and pass a fresh systemd unit name as the fourth argument. The SQLite primary key checkpoints each model, item and variant. Each completed CUDA batch is atomic and receipt progress updates after its checkpoint. The shell controller applies the frozen eligibility gate and runs the untouched split only if the pilot qualifies. Inspect the external runtime's `runs/<run-id>/items.sqlite` for per-item outputs and timing, `result.json` for scores, and `journalctl --user -u <unit>` for retries or errors. Keep raw records and snapshots outside Git.

## Replay HELM MMLU

Use NumPy 2.2.6 with Python 3.12. Download the original MMLU release linked from the authors' repository. Check the official file and the Stanford archive against the campaign's input manifest before comparing the result. [Original MMLU repository](https://github.com/hendrycks/test) · [HELM MMLU v1.0.0](https://crfm.stanford.edu/helm/mmlu/v1.0.0/)

```bash
campaign=campaign/rig-evaluation-audits-20261122
runtime=/path/to/runtime
mkdir -p "$runtime/raw"
wget -O "$runtime/raw/mmlu-data.tar" https://people.eecs.berkeley.edu/~hendrycks/data.tar
python3 -B "$campaign/fetch_helm.py" "$runtime/raw/helm"
OPENBLAS_NUM_THREADS=1 python3 -B "$campaign/score_helm.py" \
  "$runtime/raw/mmlu-data.tar" "$runtime/raw/helm" "$runtime/helm-audit.json"
```

## Replay the MadinahQA context repair

Use the same Python and NumPy environment as the MMLU audit. Fetch and score the two published releases on the frozen General subset. See [the protocol](CONTEXT-PROTOCOL.md) and [results](CONTEXT-RESULTS.md).

```bash
python3 -B "$campaign/fetch_context.py" "$runtime/raw/helm-context"
OPENBLAS_NUM_THREADS=1 python3 -B "$campaign/score_context.py" \
  "$runtime/raw/helm-context" "$runtime/helm-context-audit.json"
```
