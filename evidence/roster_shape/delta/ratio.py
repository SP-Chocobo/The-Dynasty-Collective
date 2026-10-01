"""Owner: "10 of one position and 2 of another is too far off, out of balance. 7 vs 4 is about
the ratio i'd say is the lower edge."

Treat 7:4 as a CALIBRATION POINT, not a constant to hardcode. The job is to find which DERIVED
quantity, computed from the league's own roster_positions, passes through it -- so the criterion
generalises to the other 32 formats instead of being his number applied everywhere.
"""
import json, pathlib, collections
import lineup_optimizer as lo, run_216_bench_probe as bench, run_draft_battery as rdb

scoring = rdb.scoring_settings_from_capture()
FMTS = ["8T_half_ppr_SF", "12T_half_ppr_SF", "10T_half_ppr_SF", "12T_standard_SF",
        "8T_standard_SF", "10T_standard_SF", "12T_ppr_SF", "10T_standard", "OWNER_3RR_SF_noTE",
        "12T_ppr"]
print(f"{'format':22}{'slots':38}{'bench':>6}")
cap = {}
for f in FMTS:
    lg, _ = bench.build_league(f, scoring)
    rp = lg["roster_positions"]
    slots = lo.slots_from_roster_positions(rp)
    bn = sum(1 for p in rp if p == "BN")
    ded = collections.Counter(s["label"] for s in slots if len(s["eligible"]) == 1)
    # FIELDABLE CEILING: every slot a position can legally occupy, dedicated + shared.
    fieldable = {p: sum(1 for s in slots if p in s["eligible"]) for p in ("QB", "RB", "WR", "TE")}
    cap[f] = (ded, fieldable, bn, len(rp))
    print(f"{f:22}{'/'.join(f'{p}{fieldable[p]}' for p in ('QB','RB','WR','TE')):38}{bn:>6}"
          f"   dedicated {dict(ded)}")

print("\n\nCANDIDATE DERIVATIONS, scored against the owner's anchor.")
print("His anchor is 8T_half_ppr_SF, where he called 10 WR / 2 RB out of balance and named")
print("7 / 4 as the lower edge of acceptable.\n")
ded, fieldable, bn, rounds = cap["8T_half_ppr_SF"]
print(f"  8T_half_ppr_SF: {rounds} rounds, {bn} bench, fieldable {fieldable}, dedicated {dict(ded)}")
print()
for label, ceil_fn, floor_fn in [
    ("fieldable + 1", lambda p: fieldable[p] + 1, lambda p: ded.get(p, 0)),
    ("fieldable + 2", lambda p: fieldable[p] + 2, lambda p: ded.get(p, 0) + 1),
    ("dedicated x 2", lambda p: ded.get(p, 0) * 2, lambda p: ded.get(p, 0)),
    ("fieldable x 1.5", lambda p: round(fieldable[p] * 1.5), lambda p: ded.get(p, 0) + 1),
]:
    wr_c, rb_c = ceil_fn("WR"), ceil_fn("RB")
    wr_f, rb_f = floor_fn("WR"), floor_fn("RB")
    verdict_10_2 = "REJECTS 10/2" if (10 > wr_c or 2 < rb_f) else "accepts 10/2 (WRONG)"
    verdict_7_4 = "admits 7/4" if (wr_f <= 7 <= wr_c and rb_f <= 4 <= rb_c) else "REJECTS 7/4 (WRONG)"
    flag = "  <-- matches the owner" if ("REJECTS 10/2" in verdict_10_2 and "admits" in verdict_7_4) else ""
    print(f"  {label:18} WR [{wr_f}-{wr_c}]  RB [{rb_f}-{rb_c}]   {verdict_10_2:22}{verdict_7_4}{flag}")
