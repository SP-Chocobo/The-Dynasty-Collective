#!/bin/sh
# Copy every COMPLETED arm report out of the scratchpad and into the repo, where a container
# reclaim cannot take it. Idempotent; safe to run at any moment, including mid-arm -- a report
# only exists once its arm finished writing it.
#
# Run from the repo root. $1 is the scratchpad directory holding c4_<season>/.
set -e
SCRATCH="$1"
DEST=evidence/design_35/runs
mkdir -p "$DEST"
for f in "$SCRATCH"/c4_*/*.json; do
    [ -e "$f" ] || continue
    # Validate before committing anything: a half-written report is worse than a missing one,
    # because it looks like a result. (Battery rule: validate JSON before committing a checkpoint.)
    if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
        cp "$f" "$DEST/$(basename "$f")"
        echo "kept $(basename "$f")"
    else
        echo "SKIPPED (not valid JSON yet) $(basename "$f")"
    fi
done
