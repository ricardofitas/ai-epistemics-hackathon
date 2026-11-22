#!/usr/bin/env bash
set -euo pipefail

campaign_dir="$(cd "$(dirname "$0")" && pwd)"
runtime="$(realpath "$1")"
run_id="$2"
receipt="$(realpath -m "$3")"
unit="${4:-$run_id}"

systemd-run --user --unit="$unit" \
    --description="WinoGrande campaign $run_id" --working-directory="$campaign_dir" \
    --property=RuntimeMaxSec=7200 --property=Restart=on-failure \
    --property=RestartSec=2min --property=StartLimitIntervalSec=20min \
    --property=StartLimitBurst=3 --setenv="PYTHONPATH=${PYTHONPATH:-}" \
    --setenv="SCIENCEQA_PYTHON=${SCIENCEQA_PYTHON:-python3}" --setenv=OMP_NUM_THREADS=2 \
    /usr/bin/bash "$campaign_dir/run_campaign.sh" "$runtime" "$run_id" "$receipt"
