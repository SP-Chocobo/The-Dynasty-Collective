#!/bin/sh
# Checkpoint the live VDS report to its tracked evidence path, obeying evidence/batteries/README
# rule 3: VALIDATE THE JSON BEFORE COMMITTING. The runner rewrites the report between arms, so a
# copy taken mid-write can be truncated, and a corrupt checkpoint is worse than none because it
# looks like protection.
set -e
NAME="$1"
DEST="evidence/batteries/${NAME}.json"
LOG="evidence/batteries/${NAME}.txt"
SRC_LOG="$2"
python - "$DEST" "$LOG" "$SRC_LOG" <<'PY'
import json, shutil, sys
from pathlib import Path
dest, log, src_log = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
live = Path("VDS_REPORT.json")
if not live.exists():
    print("no live report yet"); raise SystemExit(1)
try:
    data = json.loads(live.read_text())
except json.JSONDecodeError as exc:
    print(f"REFUSING: live report does not parse ({exc}); mid-write. Try again."); raise SystemExit(1)
arms = len(data.get("results", []))
if not arms:
    print("no arms finished yet"); raise SystemExit(1)
dest.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
if src_log.exists():
    shutil.copy(src_log, log)
print(f"checkpointed {arms} arms, complete={data.get('complete')} -> {dest}")
PY
