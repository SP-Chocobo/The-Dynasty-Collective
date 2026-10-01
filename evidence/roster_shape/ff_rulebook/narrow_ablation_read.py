"""Reads the narrow-ablation arm against PREREG_narrow_upside_ablation.md.

Run from the REPO ROOT. Pure artifact read -- no engine, no board, no draft.
Evaluates the pre-registered CONTROL first and refuses to report anything if it fails.
"""
import json, collections, pathlib, sys

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
POS = ("QB", "RB", "WR", "TE")
HUMAN = {"QB": 20.0, "RB": 27.4, "WR": 37.1, "TE": 15.5}


def picks(name):
    return json.load(open(OUT / f"{name}.json"))["picks"]


def compo(rows):
    c = collections.Counter(r["position"] for r in rows)
    n = len(rows) or 1
    return {p: (c[p], round(100 * c[p] / n, 1)) for p in POS}, n


def shape(rows):
    """PHASE4's three roster-shape measures, computed the same way."""
    by_seat = collections.defaultdict(collections.Counter)
    for r in rows:
        by_seat[r["roster_id"]][r["position"]] += 1
    piles = [max(c.values()) for c in by_seat.values()]
    thin = sum(1 for c in by_seat.values() for p in ("RB", "WR", "TE") if c[p] <= 2)
    return {"largest_pile": max(piles),
            "seats_ge12": sum(1 for v in piles if v >= 12),
            "thin_pairs": thin}


def line(label, rows):
    c, n = compo(rows)
    return f"  {label:<34}n={n:>3}  " + "  ".join(f"{p} {c[p][0]:>3} ({c[p][1]:>5.1f}%)" for p in POS)


def main():
    base, narrow = picks("ff_draft"), picks("ff_draft_narrow")
    raw = json.load(open(OUT / "ff_draft_narrow.json"))

    # ---- CONTROL FIRST. Nothing is reported if it fails. ----
    b14 = [r for r in base if r["round"] <= 14]
    n14 = [r for r in narrow if r["round"] <= 14]
    match = sum(1 for x, y in zip(b14, n14) if x["player_id"] == y["player_id"])
    print("=" * 78)
    print(f"CONTROL: rounds 1-14 must match baseline player-for-player -> {match}/168")
    print(f"  patch stats: {raw.get('patch_stats')}   elapsed {raw.get('elapsed_s')}s")
    if match != 168:
        first = next((i + 1 for i, (x, y) in enumerate(zip(b14, n14))
                      if x["player_id"] != y["player_id"]), None)
        print(f"  !! CONTROL FAILED (first divergence at overall {first}). "
              "The instrument toggles more than one thing. NOTHING REPORTED.")
        sys.exit(1)
    print("  CONTROL PASSES.\n")

    print("COMPOSITION")
    print(line("baseline AUTO, whole draft", base))
    print(line("NARROW arm, whole draft", narrow))
    print(f"  {'twelve real managers':<34}       " +
          "  ".join(f"{p}     ({HUMAN[p]:>5.1f}%)" for p in POS))
    print()
    print(line("baseline AUTO, rounds 15-26", [r for r in base if r["round"] >= 15]))
    print(line("NARROW arm, rounds 15-26", [r for r in narrow if r["round"] >= 15]))

    sb, sn = shape(base), shape(narrow)
    print("\nROSTER SHAPE (guardrails; force-balanced was 19 / 7 / 7 and was rejected)")
    print(f"  {'measure':<38}{'AUTO':>8}{'NARROW':>9}{'bar':>8}")
    for k, bar in (("largest_pile", "<=12"), ("seats_ge12", "<=3"), ("thin_pairs", "<=0")):
        print(f"  {k:<38}{sb[k]:>8}{sn[k]:>9}{bar:>8}")

    te15 = compo([r for r in narrow if r["round"] >= 15])[0]["TE"][1]
    wr_all = compo(narrow)[0]["WR"][1]
    ok = (te15 < 52.1 and wr_all < 40.0 and sn["largest_pile"] <= 12
          and sn["seats_ge12"] <= 3 and sn["thin_pairs"] <= 0)
    print("\nFORK READ (pre-registered)")
    print(f"  TE rounds 15-26 = {te15}%  (baseline 52.1, force-balanced 29.2)")
    print(f"  WR whole draft  = {wr_all}%  (baseline 30.4, force-balanced 42.0, human 37.1)")
    if te15 >= 50.0:
        print("  -> FORK C: NOT THE LEVER. Restoring the counterweight alone does not carry it.")
    elif ok:
        print("  -> FORK A: SUPPORTED as a candidate. TE falls and every guardrail holds.")
    else:
        print("  -> FORK B: SAME TRADE, REJECTED. TE falls but a guardrail breached.")

    print("\nper-seat TE (slot order):")
    for label, rows in (("AUTO  ", base), ("NARROW", rows_n := narrow)):
        slot, te = {}, collections.Counter()
        for r in rows:
            if r["round"] == 1 and r["roster_id"] not in slot:
                slot[r["roster_id"]] = len(slot) + 1
            te[r["roster_id"]] += (r["position"] == "TE")
        print(f"  {label}: {[te[k] for k, _ in sorted(slot.items(), key=lambda kv: kv[1])]}")


if __name__ == "__main__":
    main()
