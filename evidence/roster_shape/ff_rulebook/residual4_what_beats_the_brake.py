"""RESIDUAL4 -- what beats a ~100-point tight-end deduction?

RESIDUAL3 established that every seat carries a TE deduction near -100 through the divergence
window, and that four seats take tight ends anyway (8/8/6/5 of 12 picks) while five take almost
none. The brake is on and losing. team_acquisition_value has five terms:

    tav = universal_value + need_bonus + eligibility_bonus + depth_exposure + displacement_adj

and only one of them has ever been examined. This reads the WINNER and the best NON-TE
ALTERNATIVE, term by term, at the picks where a hoarder actually took a tight end.

FORKS, FIXED BEFORE THE RUN:
  A  the tight end wins on universal_value/bpa -- its points-minus-level margin over the best
     alternative exceeds the deduction. Since bpa = points - level and TE's level is anchored
     far below WR's, that would put the driver in the LEVEL GAP, i.e. consumer 1 (bpa), which
     the #50 work already identified as where the anchor's staleness reaches a price.
  B  the tight end wins on need_bonus, eligibility_bonus or depth_exposure -- a different term
     is responsible and has never been looked at.
  C  the tight end is NOT the top row by final_score at those picks -- something downstream
     selects it. narrow_candidates was exonerated on five picks; this would reopen it on more,
     and would need its own investigation rather than a conclusion here.

Artifact risks: one draft; the window is the divergence window so the roster states are
downstream of earlier choices; and "best non-TE alternative" is a CHOICE of comparator -- the
top non-TE row by final_score -- stated here so it is not mistaken for the only one possible.

Production-shaped picks, mode="balanced". Run from the repo root with PYTHONPATH=.
"""
import json, statistics as st
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
L = {"roster_positions": RP,
     "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
     "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft_balanced.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
HOARD = {"2", "5", "9", "12"}
STARVE = {"1", "3", "8", "10", "11"}
import sys
GROUP = STARVE if "--starve" in sys.argv else HOARD
WANT_TE = "--starve" not in sys.argv
def f(x):
    try: return float(x)
    except: return None
def prod_picks(upto):
    return [{"pick_no": i + 1, "round": i // 12 + 1, "roster_id": q["roster_id"],
             "player_id": q["player_id"]} for i, q in enumerate(D[:upto])]
assert not ({"pick_no", "round", "roster_id", "player_id"} - set(prod_picks(5)[0]))

# CORRECTED. The first version of this probe omitted time_horizon_adj and risk_adj, which are
# real terms of the BALANCED composition (see draft_room.score_row). Fork B was therefore tested
# against an incomplete list, and the term sums did not reconcile to final_score -- in one
# observation by 8.9 points, larger than the deciding margin. The reconciliation check below is
# what the first version lacked; it is the non-vacuity test for the decomposition itself.
TERMS = ("bpa", "time_horizon_adj", "risk_adj", "need_bonus", "eligibility_bonus",
         "depth_exposure", "displacement_adj")
rows = []
for seat in sorted(GROUP, key=int):
    idxs = [i for i, q in enumerate(D) if q["roster_id"] == seat]
    for n in range(9, 21):
        if n > len(idxs): continue
        at = idxs[n - 1]
        # CONTROL ARM: for starvers, take the picks where they did NOT take a TE.
        if WANT_TE != (D[at]["position"] == "TE"):
            continue
        board = dr.compute_draft_board(m, players_db, prod_picks(at), seat, L, mode="balanced",
                                       sleeper_projections=season,
                                       sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        priced = [r for r in board if f(r.get("final_score")) is not None]
        priced.sort(key=lambda r: -f(r["final_score"]))
        te = next((r for r in priced if r["position"] == "TE"), None)
        alt = next((r for r in priced if r["position"] != "TE"), None)
        if te is None or alt is None: continue
        chosen_is_top = priced[0]["player_id"] == D[at]["player_id"]
        _te_sum = sum(f(te.get(k)) or 0.0 for k in TERMS)
        _alt_sum = sum(f(alt.get(k)) or 0.0 for k in TERMS)
        rows.append({"seat": seat, "n": n, "top_pos": priced[0]["position"],
                     "te_recon": round(_te_sum - f(te["final_score"]), 2),
                     "alt_recon": round(_alt_sum - f(alt["final_score"]), 2),
                     "chosen_is_top_row": chosen_is_top,
                     "te": {k: f(te.get(k)) or 0.0 for k in TERMS},
                     "te_pts": f(te.get("projected_points")), "te_final": f(te["final_score"]),
                     "alt_pos": alt["position"],
                     "alt": {k: f(alt.get(k)) or 0.0 for k in TERMS},
                     "alt_pts": f(alt.get("projected_points")), "alt_final": f(alt["final_score"])})
json.dump(rows, open(("evidence/roster_shape/ff_rulebook/residual4_raw.json" if WANT_TE else "evidence/roster_shape/ff_rulebook/residual4_raw_control.json"), "w"), indent=1)
_arm = "HOARD took TE" if WANT_TE else "STARVE did NOT take TE"
print(f"RAW SAVED: {len(rows)} picks ({_arm})\n")

worst = max((abs(r["te_recon"]) for r in rows), default=0)
worst_a = max((abs(r["alt_recon"]) for r in rows), default=0)
print(f"RECONCILIATION -- sum(terms) minus final_score, worst |gap|: "
      f"chosen TE {worst:.2f}, alternative {worst_a:.2f}")
print("  (a non-zero gap means the decomposition is STILL incomplete and the margins below "
      "do not account for the whole decision)\n")
print(f"FORK C check -- was the chosen player the board's TOP ROW by final_score?")
print(f"  yes in {sum(1 for r in rows if r['chosen_is_top_row'])} of {len(rows)}"
      f"   top row was a TE in {sum(1 for r in rows if r['top_pos'] == 'TE')} of {len(rows)}\n")

print("per-term margin, chosen TE minus the best NON-TE row on the same board")
print(f"  {'':4}" + "".join(f"{t[:11]:>13}" for t in TERMS) + f"{'final':>10}{'TE pts':>9}{'alt':>6}")
mar = {t: [] for t in TERMS}
for r in rows:
    d = {t: r["te"][t] - r["alt"][t] for t in TERMS}
    for t in TERMS: mar[t].append(d[t])
    print(f"  s{r['seat']:<3}" + "".join(f"{d[t]:>+13.2f}" for t in TERMS)
          + f"{r['te_final'] - r['alt_final']:>+10.2f}{(r['te_pts'] or 0):>9.1f}{r['alt_pos']:>6}")
print(f"\n  {'MEAN':4}" + "".join(f"{st.mean(mar[t]):>+13.2f}" for t in TERMS))
print(f"\n  reading: a POSITIVE margin means that term favoured the tight end.")
