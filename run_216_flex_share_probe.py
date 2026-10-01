"""Is a flex slot really filled "roughly interchangeably" by whichever eligible position is best?

`draft_room.starter_slot_counts` splits a flex slot's capacity EVENLY across the positions it
admits -- a WR/RB/TE FLEX counts +1/3 toward each -- and its docstring justifies that with a
claim about the world: those slots "genuinely do get filled by whichever eligible position is
best roughly interchangeably in real drafting behavior". SUPER_FLEX is the one exception, and
that exception is a hand-set constant (`SUPER_FLEX_QB_SHARE = 0.85`).

Those slot counts are the demand that sets every replacement RANK, and the rank sets the
replacement LEVEL that `bpa` subtracts. So if the even split is wrong, every position's price is
wrong by a fixed amount in a direction the format decides -- which is the shape of #216 in both
of its observed directions at once:

  * 12T_ppr (one dedicated TE slot): the engine hoards tight ends.
  * the owner's league (NO dedicated TE slot, three flexes): the engine fields no tight end at
    all and fills all three flexes with running backs.

THIS INSTRUMENT ONLY MEASURES. It changes no engine behaviour and no constant. It answers one
question with a number: who actually wins each flex slot type in this league, on this pool,
under this rulebook, and how far that is from the even split the code assumes.

## The derivation, and why it is not circular

The obvious way to measure "who fills flexes" is to look at finished rosters -- and it is
worthless here, because the rosters were drafted BY the anchor under test. A pool that prices
tight ends high produces tight-end-heavy rosters, which would then "confirm" a high tight-end
flex share.

So the measurement never looks at a drafter. Who wins a flex is a property of the PROJECTION
CURVE and the RULEBOOK: field the whole league optimally out of the whole scoreable pool --
`num_teams` copies of every starting slot, one exact maximum-total-points assignment via the
lineup optimizer this repo already has (#126: no second solver) -- and read off which position
occupied each flex slot. Eligibility comes from `fantasy_positions`, not `position` (#172).

That is the same question `starter_slot_counts` is answering by assumption, asked of the data.
"""
from __future__ import annotations

import argparse
import collections
import json
from pathlib import Path

import data_merger as dm
import draft_battery as db
import draft_room as dr
import lineup_optimizer as lo
import resume_join
import run_216_bench_probe as bench
import run_draft_battery as rdb
import run_roster_proof as rp

FORMATS = ("12T_ppr", "12T_ppr_SF", bench.OWNER_LEAGUE["label"])


def league_wide_slots(roster_positions, num_teams):
    """`num_teams` copies of this league's STARTING slots, slot_ids made unique per team.

    slots_from_roster_positions already drops bench slots; copying it per team is what turns
    one roster's lineup solve into the league's fielding. The slot_id keeps its own type so
    the caller can group by slot type."""
    base = lo.slots_from_roster_positions(roster_positions)
    out = []
    for team in range(num_teams):
        for slot in base:
            out.append({**slot, "slot_id": f"t{team}:{slot['slot_id']}", "slot_type": slot["label"]})
    return out


def derived_flex_occupancy(points, players_db, roster_positions, num_teams):
    """Who occupies each slot type when the whole league is fielded optimally from the pool."""
    entries = []
    for pid, value in points.items():
        info = players_db.get(str(pid)) or {}
        eligible = set(info.get("fantasy_positions") or ([info["position"]] if info.get("position") else []))
        if not eligible:
            continue
        entries.append({"id": str(pid), "value": float(value), "eligible": eligible})
    slots = league_wide_slots(roster_positions, num_teams)
    solved = lo.optimize_lineup(entries, slots)
    by_type = {s["slot_id"]: s["slot_type"] for s in slots}
    pos_of = {e["id"]: (players_db.get(e["id"]) or {}).get("position") for e in entries}
    occupancy: dict = collections.defaultdict(collections.Counter)
    for a in solved["assignments"]:
        occupancy[by_type[a["slot_id"]]][pos_of[a["player_id"]]] += 1
    return {k: dict(v) for k, v in occupancy.items()}, len(solved["assignments"]), len(slots)


def derived_starter_counts(occupancy, num_teams):
    """The per-position starting demand PER TEAM implied by the measured occupancy -- the same
    quantity starter_slot_counts returns, derived instead of assumed."""
    counts: dict[str, float] = {p: 0.0 for p in dr.FANTASY_POSITIONS}
    for filled in occupancy.values():
        for position, n in filled.items():
            if position in counts:
                counts[position] += n / num_teams
    return counts


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--formats", default=",".join(FORMATS))
    args = ap.parse_args(argv)
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    scoring = rdb.scoring_settings_from_capture()
    merger = dm.DataMerger()
    players_db, universe = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    report = {"commit": resume_join.head_commit(), "universe": universe, "formats": []}
    lines = ["# Who actually wins a flex slot", ""]
    for label in args.formats.split(","):
        league, _draft_type = bench.build_league(label, scoring)
        merger.set_league_format(db.league_format_hint(league))           # NEVER SKIP
        roster_positions = league["roster_positions"]
        num_teams = league["total_rosters"]
        points = rp.scoreable_pool(merger, players_db, league, season)
        occupancy, filled, total = derived_flex_occupancy(points, players_db, roster_positions, num_teams)
        derived = derived_starter_counts(occupancy, num_teams)
        assumed = dr.starter_slot_counts(roster_positions)
        dedicated = dr.dedicated_slot_counts(roster_positions)
        assumed_demand = {p: num_teams * assumed.get(p, 0.0) for p in dr.FANTASY_POSITIONS}
        derived_demand = {p: num_teams * derived.get(p, 0.0) for p in dr.FANTASY_POSITIONS}
        ranks = {which: {p: dr._remaining_demand_rank(p, d) for p in ("QB", "RB", "WR", "TE")}
                 for which, d in (("assumed", assumed_demand), ("derived", derived_demand))}
        block = {"format": label, "roster_positions": roster_positions, "num_teams": num_teams,
                 "pool": len(points), "slots_filled": filled, "slots_total": total,
                 "flex_occupancy": occupancy, "assumed_per_team": assumed,
                 "derived_per_team": derived, "dedicated": dedicated, "ranks": ranks}
        report["formats"].append(block)
        lines.append(f"## {label} — {num_teams} teams, pool {len(points)}, "
                     f"{filled}/{total} league starting slots fillable")
        lines.append("")
        lines.append("Flex occupancy, league-wide optimal fielding (count of slots of that type "
                     "won by each position; even split would be the same number at each):")
        lines.append("")
        lines.append("| slot type | slots | occupancy | even split assumes |")
        lines.append("|---|---|---|---|")
        for slot_type, filled_by in sorted(occupancy.items()):
            if slot_type in dr.FANTASY_POSITIONS:
                continue
            n = sum(filled_by.values())
            eligible = dr.FLEX_SLOT_POSITIONS.get(slot_type, set())
            share = ", ".join(f"{p} {n / len(eligible):.0f}" for p in sorted(eligible)) if eligible else "-"
            got = ", ".join(f"{p} {c}" for p, c in sorted(filled_by.items(), key=lambda kv: -kv[1]))
            lines.append(f"| {slot_type} | {n} | {got} | {share} |")
        lines.append("")
        lines.append("| position | dedicated | assumed total | DERIVED total | assumed rank | DERIVED rank |")
        lines.append("|---|---|---|---|---|---|")
        for p in ("QB", "RB", "WR", "TE"):
            lines.append(f"| {p} | {dedicated.get(p, 0)} | {assumed.get(p, 0.0):.3f} | "
                         f"{derived.get(p, 0.0):.3f} | {ranks['assumed'][p]} | {ranks['derived'][p]} |")
        lines.append("")
    (out / "flex_share.json").write_text(json.dumps(report, indent=2) + "\n")
    (out / "TABLES_flex_share.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
