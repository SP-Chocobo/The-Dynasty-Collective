#!/bin/sh
# Copy the VDS battery's in-progress report out of the scratchpad and into the repo, where a
# container reclaim cannot take it. Idempotent; safe at any moment.
#
# run_vds_battery writes the whole report after EVERY arm (complete=False until the last), so a
# copy is always a valid checkpoint of every arm finished so far. Validate before copying: a
# half-written report is worse than a missing one, because it looks like a result.
#
# Run from the repo root. $1 is the scratchpad directory holding the live report.
set -e
SRC=$(ls "$1"/VDS_2026-*_varied_drafting_strategy_*.json 2>/dev/null | head -1)
[ -n "$SRC" ] || { echo "no live VDS report yet"; exit 0; }
DEST=evidence/batteries/$(basename "$SRC")
if python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(len(d.get('results') or []))" "$SRC" >/dev/null 2>&1; then
    ARMS=$(python3 -c "import json,sys; print(len(json.load(open(sys.argv[1])).get('results') or []))" "$SRC")
    COMPLETE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1])).get('complete'))" "$SRC")
    cp "$SRC" "$DEST"
    echo "kept $(basename "$SRC"): $ARMS arms, complete=$COMPLETE"
else
    echo "SKIPPED: report is not valid JSON yet (mid-write)"
fi
