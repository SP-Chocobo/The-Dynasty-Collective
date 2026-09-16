"""#206 step 1: can the real draft board be JOINED to the engine's universe at all?

PROVE THE JOIN BEFORE MEASURING ANYTHING. The take-model measurement is worthless if the names on
a screenshot-extracted board do not resolve to the engine's players, and a broken matcher fails
SILENTLY -- it returns a tidy zero that reads as a finding. That is exactly the near-miss this
session already had on `#112`, where a hand-rolled normaliser reported 0 of 643 rows present and
the CONTROL (0 of 475 PRICED rows too) was the only thing that exposed it.

So this file measures the join and nothing else, using the repo's OWN resolver (`DataMerger._resolve`,
which `#77` gave team and position rejection) rather than a matcher invented here.

THE CONTROLS, because a match rate alone is not evidence:
  * ROUND 1 must match at or near 100%. Twelve first-round picks in a superflex league are the
    most famous players in the sport; if they do not resolve, the join is broken, not the data.
  * The rate must be reported BY ROUND. A matcher that works early and fails late is a different
    defect from one that fails uniformly, and the tail is where an unpriced/undrafted population
    legitimately lives.
  * Every failure is NAMED, not counted. A count cannot be inspected; a list can.

Run from the repo root. NEVER cd first -- DataMerger resolves baselines against cwd.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/identity_join.py
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import data_merger as dm

BOARD = Path("evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json")
OUT = Path("evidence/take_model/identity_join.json")


def main() -> int:
    board = json.loads(BOARD.read_text())
    picks = board["picks"]
    prov = board["provenance"]
    print(f"board: {prov['league']}   picks {len(picks)}   counts {prov['counts']}", flush=True)

    # The population under test is REAL PLAYER picks: kicker placeholders stand for rookie picks
    # and are not players, and illegible cells carry no name to resolve.
    real = [p for p in picks
            if not p.get("is_rookie_pick_placeholder") and not p.get("illegible")
            and p.get("raw_player")]
    print(f"real player picks with a legible name: {len(real)}", flush=True)

    merger = dm.DataMerger()
    hit, miss = [], []
    by_round = Counter()
    round_total = Counter()
    for p in real:
        row = merger._find_match(p["raw_player"], position=p.get("position"),
                                 team=p.get("nfl_team"))
        round_total[p["round"]] += 1
        if row is not None:
            hit.append(p)
            by_round[p["round"]] += 1
        else:
            miss.append({"pick_no": p["pick_no"], "name": p["raw_player"],
                         "position": p.get("position"), "nfl_team": p.get("nfl_team"),
                         "round": p["round"]})

    rate = len(hit) / len(real) if real else 0.0
    print(f"\n   RESOLVED {len(hit)} of {len(real)}  ({rate:.1%})", flush=True)

    r1 = by_round[1], round_total[1]
    print(f"   CONTROL round 1: {r1[0]} of {r1[1]} -- these are the most famous players in the "
          f"sport; anything short of all of them means the JOIN is broken, not the data",
          flush=True)

    print("\n   by round:", flush=True)
    for rnd in sorted(round_total):
        h, t = by_round[rnd], round_total[rnd]
        print(f"     R{rnd:<3} {h:>3}/{t:<3} {'#' * int(20 * h / t) if t else ''}", flush=True)

    if miss:
        print(f"\n   UNRESOLVED ({len(miss)}), named rather than counted:", flush=True)
        for m in miss[:40]:
            print(f"     {m['pick_no']:>4}  {m['name']:<26} {str(m['position']):<4} "
                  f"{str(m['nfl_team']):<4} R{m['round']}", flush=True)
        if len(miss) > 40:
            print(f"     ... and {len(miss) - 40} more (all in the JSON)", flush=True)

    OUT.write_text(json.dumps(
        {"board": prov["league"], "picks_total": len(picks), "real_legible": len(real),
         "resolved": len(hit), "rate": round(rate, 4),
         "round_1_control": {"resolved": r1[0], "of": r1[1]},
         "by_round": {str(r): {"resolved": by_round[r], "of": round_total[r]}
                      for r in sorted(round_total)},
         "unresolved": miss}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
