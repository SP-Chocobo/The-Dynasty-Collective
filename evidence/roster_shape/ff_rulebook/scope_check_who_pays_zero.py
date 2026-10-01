"""SCOPE CHECK on my own Fork Q finding. Run from the REPO ROOT with PYTHONPATH=.

Fork Q reported "WR pays exactly zero displacement, on every row". That was measured in ONE
league. Before that reads as a general property of the engine, two questions:

  (a) STRUCTURAL -- is "the highest-level position admitted by a flex slot pays zero for that
      slot" true by construction, independent of league? Answered from source, not measured:
      displacement_level fills each flex phantom with the best free player among the positions
      that slot admits, so a candidate at the highest-level admitted position evicting that
      phantom has displaced == his own level, and adjustment = level - displaced = 0 exactly.
      Format-independent by construction.

  (b) EMPIRICAL -- is that position WR in other league shapes, or is it an accident of Fourth
      and Forever? Only the DEMAND changes with roster shape; the projection curves are the
      same universe. So call production's own starter_slot_counts + replacement_levels on the
      REAL priced pool under a range of realistic roster shapes and read which admitted
      position tops the levels.

This narrows or widens a published claim of mine. It proposes nothing and changes nothing.
INVOCATION: dr.starter_slot_counts and dr.replacement_levels called directly on the pool saved
by aggregate_selection_probe.py -- production functions, production data, no board rebuild.
"""
import json, pathlib
import pandas as pd
import draft_room as dr

OUT = pathlib.Path("evidence/roster_shape/ff_rulebook")
FLEX = ("FLEX", "SUPER_FLEX", "WRRB_FLEX", "REC_FLEX")

SHAPES = {
    "Fourth and Forever (the measured league)":
        ["QB","RB","RB","WR","WR","TE","FLEX","FLEX","FLEX","SUPER_FLEX"],
    "classic 1QB redraft":
        ["QB","RB","RB","WR","WR","WR","TE","FLEX"],
    "superflex, 2 flex":
        ["QB","RB","RB","WR","WR","TE","FLEX","FLEX","SUPER_FLEX"],
    "TE-premium 2TE":
        ["QB","RB","RB","WR","WR","TE","TE","FLEX"],
    "4WR, no flex":
        ["QB","RB","RB","WR","WR","WR","WR","TE"],
    "RB-heavy 3RB":
        ["QB","RB","RB","RB","WR","WR","TE","FLEX"],
    "REC_FLEX league":
        ["QB","RB","RB","WR","WR","TE","REC_FLEX","REC_FLEX"],
}
NUM_TEAMS = 12


def main():
    raw = json.load(open(OUT / "aggregate_selection_raw.json"))
    df = pd.DataFrame(raw["rows"])
    pool = df[df["final_score"].notna()][["player_id", "position", "projected_points"]].copy()
    pool = pool.rename(columns={"projected_points": "_points"})
    print(f"priced pool: {len(pool)} rows  "
          f"({dict(pool['position'].value_counts())})\n")

    print(f"{'roster shape':<42}{'levels QB/RB/WR/TE':<34}{'pays 0 in FLEX':<16}{'in SUPER_FLEX'}")
    print("-" * 108)
    for label, rp in SHAPES.items():
        demand = dr.starter_slot_counts(rp)
        # remaining_starter_demand's pre-draft value is league-wide capacity: per-team x teams.
        rem = {p: v * NUM_TEAMS for p, v in demand.items() if v > 0}
        lv = dr.replacement_levels(pool, "_points", rp, NUM_TEAMS, rem)
        shown = "  ".join(f"{p} {lv[p]:>6.1f}" if p in lv else f"{p}   --  "
                          for p in ("QB", "RB", "WR", "TE"))

        def tops(slot):
            if slot not in rp:
                return "-"
            adm = [p for p in dr.FLEX_SLOT_POSITIONS[slot] if p in lv]
            if not adm:
                return "?"
            best = max(adm, key=lambda p: lv[p])
            return f"{best} ({lv[best]:.0f})"

        print(f"{label:<42}{shown:<34}{tops('FLEX'):<16}{tops('SUPER_FLEX')}")

    print("\nREC_FLEX / WRRB_FLEX where present:")
    for label, rp in SHAPES.items():
        for slot in ("REC_FLEX", "WRRB_FLEX"):
            if slot in rp:
                demand = dr.starter_slot_counts(rp)
                rem = {p: v * NUM_TEAMS for p, v in demand.items() if v > 0}
                lv = dr.replacement_levels(pool, "_points", rp, NUM_TEAMS, rem)
                adm = [p for p in dr.FLEX_SLOT_POSITIONS[slot] if p in lv]
                best = max(adm, key=lambda p: lv[p]) if adm else "?"
                print(f"  {label:<42}{slot}: {best} ({lv[best]:.0f})")


if __name__ == "__main__":
    main()
