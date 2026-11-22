#!/usr/bin/env bash
set -euo pipefail

campaign_dir="$(cd "$(dirname "$0")" && pwd)"
runtime="$(realpath "$1")"
run_id="$2"
pilot_receipt="$(realpath -m "$3")"
python_bin="${SCIENCEQA_PYTHON:-python3}"
protocol="${4:-$campaign_dir/pilot.json}"

completed() {
    [ -f "$1" ] && "$python_bin" -c 'import json,sys; sys.exit(json.load(open(sys.argv[1]))["status"] != "complete")' "$1"
}

if ! completed "$pilot_receipt"; then
    "$python_bin" -B "$campaign_dir/worker.py" "$runtime" "$run_id" "$pilot_receipt" --protocol "$protocol"
fi
pilot_dir="$runtime/runs/$run_id"
"$python_bin" -B "$campaign_dir/score_wino.py" "$pilot_dir/items.sqlite" "$pilot_dir/result.json" --split pilot --protocol "$protocol"
if "$python_bin" -c 'import json,sys; sys.exit(not json.load(open(sys.argv[1]))["eligible_for_heldout"])' "$pilot_dir/result.json"; then
    heldout="${run_id}-heldout"
    mkdir -p "$runtime/runs/$heldout"
    heldout_receipt="$runtime/runs/$heldout/receipt.json"
    if ! completed "$heldout_receipt"; then
        "$python_bin" -B "$campaign_dir/worker.py" "$runtime" "$heldout" "$heldout_receipt" --split heldout --protocol "$protocol"
    fi
    "$python_bin" -B "$campaign_dir/score_wino.py" "$runtime/runs/$heldout/items.sqlite" \
        "$runtime/runs/$heldout/result.json" --split heldout --protocol "$protocol"
else
    echo "Pilot stopped at the frozen held-out eligibility gate."
fi
