"""The SECOND half of the pre-registered ceiling reading. RUN FROM THE REPO ROOT.

    python3 evidence/design_35/ceiling_check.py evidence/design_35/runs/<arm>_<season>.json ...

`PREREGISTRATION_C.md`: A (the fieldability ceiling) becomes reconsiderable only if
`capped_floor_exempt_no_backstop` is within noise of `capped_floor_exempt` **AND** its rosters hold
no position past `slots(P) + 1`. Both conditions, not either -- matching on points while still
hoarding would mean the oracle ruler cannot see the defect, which is its known blind spot.

The points half comes out of the arm reports directly. THIS is the other half: it counts each
graded seat's roster by position and compares it against `draft_room.fieldable_ceiling`, the
engine's own producer of that bound, so the check cannot disagree with the backstop about what the
ceiling is (#126).

A position ABSENT from `fieldable_ceiling` is one that reaches a shared or flex slot, and the
ceiling deliberately says nothing about it -- absence here is not a licence to hoard, it is a
statement that the arithmetic bound does not apply. Reported as `-` rather than as a pass.
"""

from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

_ROOT = Path.cwd()
if not (_ROOT / "draft_room.py").exists():
    raise SystemExit(f"run this from the repo root; cwd is {_ROOT}")
sys.path.insert(0, str(_ROOT))

import draft_battery as db          # noqa: E402
import draft_room as dr             # noqa: E402
import run_draft_battery as rdb     # noqa: E402


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    scoring = rdb.scoring_settings_from_capture()
    for path in argv:
        block = json.loads(Path(path).read_text())["results"][0]
        arm = next(a for a in db.league_matrix(scoring) if a["label"] == block["label"])
        ceiling = dr.fieldable_ceiling(arm["league"]["roster_positions"])
        print(f"\n=== {Path(path).name}  ({block['label']}, {block['season']}) ===")
        print(f"fieldable_ceiling (dedicated slots + 1): {ceiling}")
        print("positions absent from it reach a shared/flex slot; the bound does not apply there")
        breaches = []
        for row in block["rows"]:
            counts = collections.Counter(p["position"] for p in row["engine_roster"])
            over = {pos: (n, ceiling[pos]) for pos, n in counts.items()
                    if pos in ceiling and n > ceiling[pos]}
            flag = "  <== PAST THE CEILING" if over else ""
            shape = " ".join(f"{p}{counts[p]}" for p in sorted(counts, key=lambda p: -counts[p]))
            print(f"  seat {row['seat']:>2}: {shape}{flag}")
            if over:
                for pos, (n, cap) in sorted(over.items()):
                    print(f"           {pos}: {n} rostered against a ceiling of {cap}")
                breaches.append((row["seat"], over))
        print(f"  --> seats holding a position past its ceiling: {len(breaches)} of "
              f"{len(block['rows'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
