"""#206 step 1b: WHY the join fails, decomposed into causes instead of one muddy rate.

61.6% overall is not a finding, it is an unanswered question. The by-round shape answers part of
it already: R1-R3 resolve 34 of 34 and R25-R30 resolve 5 of 57. A broken matcher fails UNIFORMLY;
a monotone decay with draft depth is a different animal. So there are at least two causes, and a
single rate hides both.

THE THREE ARMS, each isolating one cause:
  strict   name + position + team, the engine's own rule (`#77` gave it team/position rejection)
  no_team  name + position only. The board is a JANUARY draft; our vendor rows are the 2026
           season. A player who changed teams between the two is REJECTED BY A CORRECT RULE
           applied across a time boundary it was never meant to cross.
  relaxed  no_team, plus suffix/punctuation normalisation ("A.J." / "DJ", "Kenneth Walker III",
           "Travis Etienne Jr."). These are spelling, not identity.

AMBIGUITY IS A REJECTION, NOT A GUESS (`#82`). Dropping the team constraint can make a surname
match several players; where it does, this counts the pick as ambiguous and resolves nothing.
Loosening a matcher until the number improves is how `#77`'s six crossed wires happened.

Run from the repo root.
    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 -u evidence/take_model/join_decomposition.py
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import data_merger as dm

BOARD = Path("evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json")
OUT = Path("evidence/take_model/join_decomposition.json")
SUFFIX = re.compile(r"\s+(jr|sr|ii|iii|iv|v)\.?$", re.IGNORECASE)


def loosen(name: str) -> str:
    """Spelling only: drop periods in initials and a trailing generational suffix."""
    return SUFFIX.sub("", name.replace(".", "").replace("'", "")).strip()


def main() -> int:
    board = json.loads(BOARD.read_text())
    real = [p for p in board["picks"]
            if not p.get("is_rookie_pick_placeholder") and not p.get("illegible")
            and p.get("raw_player")]
    merger = dm.DataMerger()
    proj = merger.projections

    def strict(p):
        return merger._find_match(p["raw_player"], position=p.get("position"),
                                  team=p.get("nfl_team")) is not None

    def no_team(p):
        return merger._find_match(p["raw_player"], position=p.get("position")) is not None

    def relaxed(p):
        if no_team(p):
            return True
        return merger._find_match(loosen(p["raw_player"]), position=p.get("position")) is not None

    arms = {"strict": strict, "no_team": no_team, "relaxed": relaxed}
    res = {k: [bool(f(p)) for p in real] for k, f in arms.items()}

    print(f"population: {len(real)} real, legible player picks\n", flush=True)
    print(f"   {'arm':<10} resolved   rate", flush=True)
    for k in arms:
        n = sum(res[k])
        print(f"   {k:<10} {n:>4}/{len(real)}   {n / len(real):.1%}", flush=True)

    # WHAT EACH RELAXATION BOUGHT, named rather than aggregated.
    team_only = [p["raw_player"] for p, s, nt in zip(real, res["strict"], res["no_team"])
                 if not s and nt]
    spell_only = [p["raw_player"] for p, nt, rx in zip(real, res["no_team"], res["relaxed"])
                  if not nt and rx]
    print(f"\n   recovered by DROPPING TEAM ({len(team_only)}): {team_only[:14]}", flush=True)
    print(f"   recovered by SPELLING  ({len(spell_only)}): {spell_only[:14]}", flush=True)

    # THE DEPTH EFFECT, which no matcher change can fix: is what remains simply absent?
    still = [p for p, rx in zip(real, res["relaxed"]) if not rx]
    by_round = Counter(p["round"] for p in still)
    print(f"\n   STILL UNRESOLVED after both relaxations: {len(still)}", flush=True)
    print(f"   by round: {dict(sorted(by_round.items()))}", flush=True)
    print(f"   examples: {[p['raw_player'] for p in still[:12]]}", flush=True)

    # IS WHAT REMAINS SIMPLY ABSENT? Asked through the RESOLVER with no position and no team,
    # never by comparing normalised strings against `projections["norm_name"]`.
    #
    # THE FIRST VERSION OF THIS CHECK DID COMPARE STRINGS, AND IT WAS WRONG. It reported
    # "81 of 81 absent -- a supply gap, not a join defect", which is a tidy, quotable, false
    # result. `norm_name` ABBREVIATES the first name (`b corum`, `d njoku`), so nothing with a
    # full first name ever matched. The control caught it: the same check found 0 of 224 RESOLVED
    # picks present. That is the SECOND time in one session this exact column has produced a
    # confident zero -- see `#112`'s near-miss -- so the control below is permanent, not a one-off.
    unconstrained = [p for p in still
                     if merger._find_match(p["raw_player"]) is None
                     and merger._find_match(loosen(p["raw_player"])) is None]
    pos_mismatch = len(still) - len(unconstrained)
    control = sum(1 for p in real[:60]
                  if res["relaxed"][real.index(p)] and merger._find_match(p["raw_player"]) is not None)
    expect = sum(res["relaxed"][:60])
    print(f"   of those, POSITION mismatches (resolve without position): {pos_mismatch}", flush=True)
    print(f"   of those, absent from the resolver entirely: {len(unconstrained)}", flush=True)
    print(f"   CONTROL {control}/{expect}: resolved picks must also resolve unconstrained; if "
          f"they do not, this absence check is broken and its number is void", flush=True)
    absent = len(unconstrained)

    OUT.write_text(json.dumps(
        {"population": len(real),
         "arms": {k: {"resolved": sum(res[k]), "rate": round(sum(res[k]) / len(real), 4)}
                  for k in arms},
         "recovered_by_dropping_team": team_only,
         "recovered_by_spelling": spell_only,
         "still_unresolved": len(still),
         "still_by_round": {str(k): v for k, v in sorted(by_round.items())},
         "still_absent_from_resolver": absent,
         "still_position_mismatch": pos_mismatch,
         "absence_check_control": {"passed": control, "of": expect}}, indent=1))
    print(f"\nwrote {OUT}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
