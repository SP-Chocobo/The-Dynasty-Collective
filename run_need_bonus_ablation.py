"""#87: does need_bonus change any PICK, or only a number? Measured, and the answer reversed
the prior it was built to test.

WHY IT WAS DOUBTED. need_bonus has ZERO within-position standard deviation in every round of a
real draft -- it cannot separate two RBs. It moves the board 8.72% of the universal_value
spread. It collapses to 0.67 from round 10. And by round 9 it disagrees with measured
depth_exposure, saying "you need a TE" (0.50) about a position whose measured exposure is 4.0
while RB sits at 77.9. Every one of those is true.

WHAT THE ABLATION FOUND (2026-09-03, real baseline, 12-team 1QB dynasty):

  ARM A, frozen trajectory, no compounding -- the top recommendation differs in 2 of 15
  rounds (r3 and r4). Small, and concentrated early.

  ARM B, each arm drafting its own way -- 13 of 15 picks differ, and the roster SHAPE is the
  result that matters:
      with need_bonus     RB 7  WR 5  TE 2  QB 1
      without need_bonus  RB 7  WR 2  TE 2  QB 4
  Without it the engine drafts FOUR QUARTERBACKS in a one-QB league.

CONCLUSION: need_bonus is load-bearing, and every measurement doubting it was judging it
against a job it does not have. It is a POSITIONAL GATE, not a player discriminator. It cannot
tell two RBs apart because that is not its function; it tells "you need a QB" from "you already
have four" -- precisely what a within-position variance test is blind to by construction.

CONSEQUENCE FOR #87: the question "is depth_label/depth_exposure independent of need_bonus"
has no correlation-shaped answer, and re-running one would void again. They operate at
different altitudes -- need_bonus prevents positional stacking, depth_exposure prices insurance
against a hole -- and they are temporally complementary too: need_bonus is strongest rounds
1-8, depth_exposure is only `measured` from round 9. Adding exposure to team_acquisition_value
alongside need_bonus is NOT double-counting.

STATED LIMITATION. The simulated opponents pick from a board computed for MY roster, so they
do not defend their own positional needs. That is unrealistic in absolute terms and likely
exaggerates how far QBs slide -- but it is IDENTICAL in both arms, so the comparison between
them holds even though the absolute QB count should not be read as a forecast. A real
opponent-state model (Gate 2) would tighten this.

NON-VACUITY: the ablation asserts it took effect -- need_bonus non-zero in one arm, exactly
zero in the other. A patch that silently failed to apply would report "nothing changed",
indistinguishable from an inert term, and would have recorded the opposite of the truth.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
from unittest import mock
import pandas as pd
import data_merger as dm, draft_room as dr
from run_asset_character_measurement import OFFENSE_POSITIONS

LEAGUE = {"roster_positions": ["QB","RB","RB","WR","WR","TE","FLEX","FLEX","BN","BN","BN","BN","BN"],
          "total_rosters": 12, "settings": {"type": 2}}
ME = "1"

m = dm.DataMerger(); proj, db, pid = m.projections, {}, 0
for pos in OFFENSE_POSITIONS:
    for _, r in proj[proj["position"] == pos].sort_values("trade_value", ascending=False).iterrows():
        pid += 1; parts = str(r["norm_name"]).split()
        db[str(pid)] = {"first_name": parts[0].upper(), "last_name": " ".join(parts[1:]).title(),
                        "position": pos, "fantasy_positions": [pos], "team": r.get("team")}

def board(picks, ablate):
    if not ablate:
        return dr.compute_draft_board(m, db, picks, my_roster_id=ME, league=LEAGUE, mode="balanced")
    with mock.patch.object(dr, "NEED_BONUS_PER_DEDICATED_SLOT", 0.0), \
         mock.patch.object(dr, "NEED_BONUS_PER_FLEX_SHARE", 0.0):
        return dr.compute_draft_board(m, db, picks, my_roster_id=ME, league=LEAGUE, mode="balanced")

print("=== NON-VACUITY: did the ablation actually take effect? ===")
live, dead = board([], False), board([], True)
lnb = max((r.get("need_bonus") or 0) for r in live[:40])
dnb = max((r.get("need_bonus") or 0) for r in dead[:40])
print(f"  max need_bonus  live={lnb}  ablated={dnb}")
assert lnb > 0, "need_bonus is already zero in the LIVE arm -- nothing to ablate"
assert dnb == 0, "ablation did not apply; a 'no change' result would be meaningless"
print("  ok -- the term is live in one arm and zero in the other\n")

# ---- ARM A: frozen trajectory, no compounding -------------------------------
picks, changed, rounds = [], 0, 0
detail = []
for rnd in range(1, 16):
    a, b = board(picks, False), board(picks, True)
    if not a or not b:
        break
    rounds += 1
    if a[0]["player_id"] != b[0]["player_id"]:
        changed += 1
        detail.append((rnd, a[0]["position"], a[0]["name"], b[0]["position"], b[0]["name"]))
    order = list(range(1, 13)) if rnd % 2 else list(range(12, 0, -1))
    for slot, row in zip(order, a[:12]):
        picks.append({"player_id": row["player_id"], "roster_id": str(slot), "round": rnd})

print(f"=== ARM A (frozen state): top recommendation differs in {changed}/{rounds} rounds ===")
for rnd, pa, na, pb, nb in detail:
    print(f"  r{rnd:<3} with need_bonus: {pa} {na:<22}  without: {pb} {nb}")
if not detail:
    print("  (identical in every round)")

# ---- ARM B: each arm drafts its own way -------------------------------------
def run(ablate):
    picks, mine = [], []
    for rnd in range(1, 16):
        bd = board(picks, ablate)
        if not bd:
            break
        order = list(range(1, 13)) if rnd % 2 else list(range(12, 0, -1))
        for slot, row in zip(order, bd[:12]):
            picks.append({"player_id": row["player_id"], "roster_id": str(slot), "round": rnd})
            if str(slot) == ME:
                mine.append((row["position"], row["name"]))
    return mine

with_nb, without_nb = run(False), run(True)
same = sum(1 for x, y in zip(with_nb, without_nb) if x == y)
print(f"\n=== ARM B (divergent): my roster, {len(with_nb)} picks ===")
print(f"  identical picks: {same}/{len(with_nb)}")
print(f"  {'rd':<4} {'with need_bonus':<32} without")
for i, (a, b) in enumerate(zip(with_nb, without_nb), 1):
    mark = "  " if a == b else "->"
    print(f"  {mark}{i:<2} {a[0]+' '+a[1]:<32} {b[0]+' '+b[1]}")
from collections import Counter
print(f"\n  positional shape WITH   : {dict(Counter(p for p, _ in with_nb))}")
print(f"  positional shape WITHOUT: {dict(Counter(p for p, _ in without_nb))}")
