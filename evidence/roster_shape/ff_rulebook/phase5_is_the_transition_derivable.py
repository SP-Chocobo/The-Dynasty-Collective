"""Is the roster-aware -> roster-blind transition DERIVABLE from draft state, or is round 15
an unjustified global constant?

Deliberately NOT "what should 15 be." That is tuning. This asks whether the architecture
already carries an observable that corresponds to the intended transition, using ONLY
quantities production already computes. If none of them tracks it, the finding is a DESIGN GAP
-- the system cannot express the transition it is trying to make -- which is a different and
more useful result than a bad number.

Candidate observables, all existing, all exact, none invented:
  A  league-wide remaining starter demand reaches zero        (remaining_starter_demand)
  B  a seat's own DEDICATED starting slots are all filled     (_team_starters_filled +
                                                               dedicated_slot_counts)
  C  a seat's picks remaining <= its unfillable named slots   (feasibility_first's own test)
  D  every position has left replacement_levels' domain       (replacement_ranks -> None)

Run from the repo root with PYTHONPATH=.
"""
import json
import draft_room as dr

CAP = json.load(open("data/league_captures/fourth_and_forever.json"))
RP = CAP["roster_positions"]
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
NUM_TEAMS, ROUNDS = 12, 26
BOUNDARY = (dr.UPSIDE_MODE_DEFAULT_ROUND - 1) * NUM_TEAMS + 1     # first upside pick
players_db = {str(p["player_id"]): {"position": p["position"],
                                    "fantasy_positions": [p["position"]]} for p in D}
PICKS = [{"pick_no": i + 1, "round": i // NUM_TEAMS + 1, "roster_id": p["roster_id"],
          "player_id": p["player_id"]} for i, p in enumerate(D)]
POS = ("QB", "RB", "WR", "TE")

print(f"UPSIDE_MODE_DEFAULT_ROUND = {dr.UPSIDE_MODE_DEFAULT_ROUND} -> upside begins at "
      f"overall pick {BOUNDARY} of {len(D)} ({100*(len(D)-BOUNDARY+1)/len(D):.0f}% of the draft)\n")

# ---- A: league-wide starter demand ------------------------------------------------------
print("A  league-wide remaining starter demand, by pick")
first_zero = None
for k in range(0, len(D) + 1):
    dem = dr.remaining_starter_demand(RP, NUM_TEAMS, PICKS[:k], players_db)
    tot = sum(dem.get(p, 0.0) for p in POS)
    if tot <= 1e-9 and first_zero is None:
        first_zero = k
for k in (0, 60, 120, BOUNDARY - 1, BOUNDARY, 200, 240, 312):
    dem = dr.remaining_starter_demand(RP, NUM_TEAMS, PICKS[:k], players_db)
    mark = "  <- mode boundary" if k in (BOUNDARY - 1, BOUNDARY) else ""
    print(f"   after {k:>3} picks: total={sum(dem.get(p,0.0) for p in POS):7.2f}   "
          + " ".join(f"{p}={dem.get(p,0.0):6.2f}" for p in POS) + mark)
print(f"   -> league starter demand first reaches ZERO after {first_zero} picks "
      f"(round {(first_zero-1)//NUM_TEAMS + 1}); the mode boundary is pick {BOUNDARY} "
      f"(round {dr.UPSIDE_MODE_DEFAULT_ROUND}).  GAP = {first_zero - BOUNDARY:+d} picks\n")

# ---- B/C: per-seat roster completion and the feasibility test ---------------------------
ded = dr.dedicated_slot_counts(RP)
print(f"B/C per seat: when are its DEDICATED slots full, vs the mode boundary (pick {BOUNDARY})")
print(f"   dedicated slots = {ded}")
print(f"   {'seat':>5}{'own picks made at boundary':>28}{'slots full after own pick #':>30}"
      f"{'==> in rounds':>15}")
fulls = []
for seat in sorted({p["roster_id"] for p in D}, key=int):
    full_at = None
    for k in range(0, len(D) + 1):
        filled = dr._team_starters_filled(PICKS[:k], players_db, seat)
        if all(filled.get(p, 0) >= n for p, n in ded.items()):
            full_at = k
            break
    own_before = sum(1 for p in PICKS[:BOUNDARY - 1] if p["roster_id"] == seat)
    own_at_full = sum(1 for p in PICKS[:full_at] if p["roster_id"] == seat) if full_at else None
    fulls.append(own_at_full)
    print(f"   {seat:>5}{own_before:>28}{str(own_at_full):>30}"
          f"{(str((full_at - 1)//NUM_TEAMS + 1) if full_at else 'never'):>15}")
print(f"   -> seats fill their dedicated slots after {min(x for x in fulls if x)}-"
      f"{max(x for x in fulls if x)} of their OWN picks; the mode boundary hits every seat at "
      f"its {sum(1 for p in PICKS[:BOUNDARY-1] if p['roster_id']=='1')}th.\n")

# ---- B2: ALL TEN starting slots, using PRODUCTION's own optimiser -----------------------
# dedicated_slot_counts deliberately excludes flex (feasibility_first's own docstring says
# why), so B above is satisfied while four of this league's ten starting slots are still
# empty. This asks the fuller question with lineup_optimizer.optimize_lineup -- production's
# solver, not a count rule of mine: from which of a seat's own picks can it field a COMPLETE
# legal lineup?
import lineup_optimizer as lo
SLOTS = lo.slots_from_roster_positions(RP)
n_slots = len(SLOTS)
print(f"B2 all {n_slots} STARTING slots filled (production optimize_lineup), vs boundary")
print(f"   {'seat':>5}{'full lineup after own pick #':>31}{'==> in round':>14}")
full2 = []
for seat in sorted({p["roster_id"] for p in D}, key=int):
    mine, hit = [], None
    for i, pk in enumerate(PICKS):
        if pk["roster_id"] != seat:
            continue
        info = players_db[str(pk["player_id"])]
        # optimize_lineup's own documented player shape: {"id", "value", "eligible"}.
        mine.append({"id": pk["player_id"], "value": 1.0,
                     "eligible": set(info["fantasy_positions"])})
        res = lo.optimize_lineup(mine, SLOTS)
        if sum(1 for a in res["assignments"] if a.get("player_id")) >= n_slots:
            hit = (len(mine), (i // NUM_TEAMS) + 1)
            break
    full2.append(hit)
    print(f"   {seat:>5}{str(hit[0] if hit else 'never'):>31}"
          f"{str(hit[1] if hit else 'never'):>14}")
rounds2 = [h[1] for h in full2 if h]
print(f"   -> complete lineups land in rounds {min(rounds2)}-{max(rounds2)}; "
      f"the boundary is round {dr.UPSIDE_MODE_DEFAULT_ROUND}.\n")

# ---- D: replacement_ranks domain --------------------------------------------------------
print("D  positions still inside replacement_levels' domain (replacement_ranks not None)")
for k in (0, 120, BOUNDARY - 1, BOUNDARY, 240, 312):
    ranks = dr.replacement_ranks(RP, NUM_TEAMS, PICKS[:k], players_db)
    live = [p for p in POS if ranks.get(p) is not None]
    mark = "  <- mode boundary" if k in (BOUNDARY - 1, BOUNDARY) else ""
    print(f"   after {k:>3} picks: live={live or '[]'}{mark}")
