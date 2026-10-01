"""C-F4/D10: the starting-slot arithmetic in the three new ambiguity messages.

`ambiguities` dedupes the unknown labels (`sorted({...})`) but states the league's declared
starting-slot count as `parsed_starting + len(starters)` / `+ len(unresolved)`, which are counts
of DISTINCT LABELS. The authority for "how many starting slots does this league declare" is
`league_config.starting_slots` over the roster_positions LIST.

Run from the repo root:  PYTHONPATH=. python3 evidence/blind_pass_v4/probes/probe_cf4_duplicate_unknown_slot.py
"""
import re

import league_config as lc
import lineup_optimizer as lo

CLEAN = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "K", "DEF", "BN", "BN", "IR"]


def report(rp, tag):
    priced_on = len(lo.slots_from_roster_positions(rp))      # what the solver parsed
    declared = len(lc.starting_slots(rp))                    # what the league declares (authority)
    print(f"--- {tag}")
    print(f"    solver parsed      : {priced_on}")
    print(f"    league DECLARES    : {declared}   <- lc.starting_slots over the LIST")
    for item in lc.ambiguities({"roster_positions": rp, "total_rosters": 12,
                                "settings": {"type": 2}, "scoring_settings": {"rec": 1.0}}):
        print(f"    kind   : {item['kind']}")
        print(f"    detail : {item['detail']}")
        claimed = re.search(r"declares (\d+)", item["detail"]) or \
            re.search(r"has up to (\d+)", item["detail"])
        if claimed:
            n = int(claimed.group(1))
            print(f"    MESSAGE CLAIMS     : {n}  ->  "
                  f"{'AGREES' if n == declared else f'WRONG, understates by {declared - n}'}")


report(CLEAN + ["super-flex"], "one occurrence of an unrecognised STARTING label")
report(CLEAN + ["super-flex"] * 3, "THREE occurrences of the same unrecognised STARTING label")
report(CLEAN + ["WIZARD"], "one occurrence of an unresolvable label")
report(CLEAN + ["WIZARD"] * 3, "THREE occurrences of the same unresolvable label")
