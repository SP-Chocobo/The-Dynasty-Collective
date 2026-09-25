"""#35 Formulation C, measured on realized outcomes. RUN FROM THE REPO ROOT.

    python3 evidence/design_35/phantom_cap_experiment.py --season 2024 --out DIR

THE QUESTION. `shared_slot_alternatives` prices a slot at `max(level(p) for p in slot.eligible)`
-- the level being a replacement level the board already computed. Late in a draft that level can
be the STALE PRE-DRAFT ANCHOR: measured on a real round-14 board, WR's level was 216.25 while the
best receiver actually remaining projected 173.00, so a phantom worth 216.25 held BOTH flex slots,
out-valued the real occupant (Deebo, 197.8), and `displacement_adj` came out exactly 0.00 on all
145 WR rows. Formulation C caps each slot's alternative at what is actually still available for
it, on the ground that the pool only drains: no free player at draft end can be worth more than
the best one undrafted now.

NOBODY HAS MEASURED WHETHER THAT HELPS. The argument for C is entirely about coherence; its
registered cost is that it inverts a shipped invariant (`displacement_adj` non-positive for a
single-position candidate) and reaches two derived constants through
`pick_synthesis.TEAM_SPECIFIC_CAPS`. This instrument answers the prior question -- does capping
the phantom draft BETTER ROSTERS -- before any of that is paid for.

NO ENGINE EDIT. Both arms run the same working tree at the same commit, in ONE process, and
differ in exactly one thing: whether `dr.board_slot_alternatives` is the shipped function or the
capped one. That is the in-process A/B the engine-measurement skill requires, and both of the
functions this patches document themselves as module-level and patchable for exactly this.

WHERE THE REMAINING POOL COMES FROM. `board_slot_alternatives(levels, roster_positions)` never
receives the pool -- that is the first thing recorded about C, and it is why this cannot be a
one-line patch. So `dr.build_available_pool` is wrapped and the frame it returns is remembered,
which means the cap reads THE BOARD'S OWN REMAINING POOL rather than a second reconstruction of
it. Only calls with a NON-EMPTY drafted set are recorded: the two pre-draft-anchor call sites
(draft_room.py:2870, :2983) pass `set()`, and their full pool is not the remaining one. On the
opening board the drafted set is legitimately empty and the two pools coincide, so the holder is
also filled when it is still unset; every later board refills it from its own live call, which
`compute_draft_board` makes before any anchor is built.

THE CAP'S CURRENCY AND VOCABULARY. `point_replacement` is per PRIMARY position, because
`replacement_levels` groups the pool by its `position` column. The cap is therefore taken per
primary position too, from the same `_derive_points_and_source` mask the board uses. Taking it
over `fantasy_positions` instead would be a better answer to "who can field this slot" and a
WORSE one to "what is this level about" -- mixing the two vocabularies in one comparison is the
category error this repository keeps removing, so the narrower, consistent choice is made here
and the divergence is left for the writeup.

THE FORM. For each slot:

    capped_alternative = min( max(level(p) for p in eligible),
                              max(best_remaining_points(p) for p in eligible) )

`min` of the two maxima, not a per-position `min` then a `max`: the slot's alternative is one
number about one slot, and the cap is a statement about that slot's reachable pool, not about
each position separately. A slot no remaining priced row can reach keeps the uncapped level
rather than being dropped -- dropping it would route `displacement_level` to the candidate's own
`free_alternative`, which changes a SECOND thing and would confound the arm.

LIMITS. The grader's own limits all stand and are stated in run_backtest_grade's docstring (no
waivers, oracle weekly lineup, a capture that post-dates the drafted season). This adds one:
the cap is measured only where a level exists at all. A position the board declined to price
carries no level, so C has nothing to cap there and this instrument is silent about it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# RUN FROM THE REPO ROOT -- and this file lives two directories down from it, so `python3
# evidence/design_35/phantom_cap_experiment.py` puts THIS directory on sys.path[0] and not the
# root. That is the engine-measurement skill's first hazard wearing a different hat: `DataMerger`
# resolves its baseline paths against the working directory, so a probe that fixes the import by
# chdir'ing would load an empty frame and say so only by crashing three calls later. So the
# working directory is ASSERTED to be the root and then prepended, which fixes the import
# without moving anything.
_ROOT = Path.cwd()
if not (_ROOT / "draft_room.py").exists():
    raise SystemExit(f"run this from the repo root; cwd is {_ROOT} and has no draft_room.py")
sys.path.insert(0, str(_ROOT))

import pandas as pd

import draft_room as dr
import run_backtest_grade as bg

#: The board's own remaining pool, remembered by the wrapper below. A one-element list rather
#: than a bare name so the closures rebind the CONTENTS and not a shadow of the module global.
_LIVE_POOL: list = [None]

#: How often the cap actually bit, and by how much -- so a null result can be told apart from a
#: patch that never fired. `#246`'s lesson: identical arms usually mean a broken instrument.
_CAP_STATS: dict = {"slots_priced": 0, "slots_capped": 0, "reduction_sum": 0.0,
                    "max_reduction": 0.0, "no_reach": 0, "pool_missing": 0}


def install_pool_recorder():
    """Wrap `dr.build_available_pool` so the cap can see the board's own remaining pool."""
    real = dr.build_available_pool

    def recorder(merger, players_db, drafted_player_ids, usable_positions, **kwargs):
        pool = real(merger, players_db, drafted_player_ids, usable_positions, **kwargs)
        if drafted_player_ids or _LIVE_POOL[0] is None:
            _LIVE_POOL[0] = pool
        return pool

    dr.build_available_pool = recorder
    return real


def best_remaining_by_position() -> "dict[str, float] | None":
    """{primary position: best remaining projected points}, from the board's own live pool.

    None -- never an empty dict -- when no pool has been recorded or none of it is priced, so
    the caller can tell "nothing available" from "never measured" (#187)."""
    pool = _LIVE_POOL[0]
    if pool is None or pool.empty:
        return None
    frame = pool.copy()
    has_proj = dr._derive_points_and_source(frame)
    priced = frame[has_proj]
    if priced.empty:
        return None
    return {str(p): float(v) for p, v in
            priced.groupby("position")["_points"].max().items()}


def capped_slot_alternatives(levels, roster_positions):
    """Formulation C: the shipped construction, capped at what the slot can actually still get."""
    import lineup_optimizer as lo
    priced = {p: float(v) for p, v in levels.items() if v is not None and not pd.isna(v)}
    best = best_remaining_by_position()
    if best is None:
        _CAP_STATS["pool_missing"] += 1
    out: dict[str, float] = {}
    for slot in lo.slots_from_roster_positions(roster_positions):
        candidates = [priced[p] for p in slot["eligible"] if p in priced]
        if not candidates:
            continue
        level_max = max(candidates)
        _CAP_STATS["slots_priced"] += 1
        reach = [best[p] for p in slot["eligible"] if p in best] if best else []
        if not reach:
            _CAP_STATS["no_reach"] += 1
            out[slot["slot_id"]] = level_max
            continue
        capped = min(level_max, max(reach))
        if capped < level_max:
            _CAP_STATS["slots_capped"] += 1
            _CAP_STATS["reduction_sum"] += level_max - capped
            _CAP_STATS["max_reduction"] = max(_CAP_STATS["max_reduction"], level_max - capped)
        out[slot["slot_id"]] = capped
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default="2024")
    parser.add_argument("--out", required=True,
                        help="a DIRECTORY for the two arm reports and the summary")
    parser.add_argument("--seats", type=int, default=0)
    parser.add_argument("--streaming", action="store_true", default=True,
                        help="grade the SHIPPED path (#30's floor wired), which is the "
                             "configuration the cap would ship into")
    parser.add_argument("--no-streaming", dest="streaming", action="store_false")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    shipped = dr.board_slot_alternatives
    install_pool_recorder()

    common = ["--season", args.season]
    if args.streaming:
        common.append("--streaming")
    if args.seats:
        common += ["--seats", str(args.seats)]

    arms = {}
    for name in ("control", "capped"):
        # ONE PROCESS, ONE CODE VERSION, ONE THING TOGGLED.
        dr.board_slot_alternatives = shipped if name == "control" else capped_slot_alternatives
        for key in _CAP_STATS:
            _CAP_STATS[key] = 0 if isinstance(_CAP_STATS[key], int) else 0.0
        _LIVE_POOL[0] = None
        report = out_dir / f"{name}_{args.season}.json"
        started = time.time()
        print(f"\n########## ARM {name} ({args.season}) ##########", flush=True)
        rc = bg.main(common + ["--out", str(report)])
        if rc != 0:
            print(f"arm {name} refused to run (rc={rc}); no summary written")
            return rc
        block = json.loads(report.read_text())["results"][0]
        arms[name] = {
            "wins": block["wins"], "seats": block["seats_graded"],
            "mean_delta": block["mean_delta"], "median_delta": block["median_delta"],
            "distinct_rosters": block["distinct_engine_rosters"],
            "engine_totals": {r["seat"]: r["engine_realized"] for r in block["rows"]},
            "first_kdst_round": {r["seat"]: r["engine_first_kdst_round"] for r in block["rows"]},
            "cap_stats": dict(_CAP_STATS),
            "seconds": round(time.time() - started, 1),
            "report": str(report),
        }
        print(f"   arm {name}: wins {block['wins']}/{block['seats_graded']} "
              f"mean {block['mean_delta']:+.1f}  cap {_CAP_STATS}", flush=True)

    dr.board_slot_alternatives = shipped

    # PAIRED BY SEAT. The unpaired means are in the arm blocks; the paired delta is the
    # measurement, because the two arms draft the same seat against the same field.
    paired = {}
    for seat, control_total in arms["control"]["engine_totals"].items():
        capped_total = arms["capped"]["engine_totals"].get(seat)
        if capped_total is not None:
            paired[seat] = round(capped_total - control_total, 2)
    improved = sum(1 for v in paired.values() if v > 0)
    worsened = sum(1 for v in paired.values() if v < 0)
    summary = {
        "_comment": ("#35 Formulation C (cap each slot's free-player alternative at the best "
                     "REMAINING player eligible for that slot) vs the shipped construction, "
                     "graded on realized weekly outcomes. One process, one commit, one thing "
                     "toggled. See evidence/design_35/phantom_cap_experiment.py."),
        "season": args.season,
        "streaming_floor": bool(args.streaming),
        "arms": arms,
        "paired_capped_minus_control": paired,
        "seats_improved": improved,
        "seats_unchanged": len(paired) - improved - worsened,
        "seats_worsened": worsened,
        "paired_total": round(sum(paired.values()), 2),
        "paired_mean": round(sum(paired.values()) / len(paired), 2) if paired else None,
    }
    (out_dir / f"SUMMARY_{args.season}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"\n=== #35 C vs shipped, {args.season} realized ===")
    for name, block in arms.items():
        print(f"{name:>8}: wins {block['wins']}/{block['seats']}  "
              f"mean {block['mean_delta']:+.1f}  median {block['median_delta']:+.1f}")
    print(f"paired (capped - control): {improved} improved, {worsened} worsened, "
          f"total {summary['paired_total']:+.1f}, mean {summary['paired_mean']}")
    print(f"cap fired: {arms['capped']['cap_stats']}")
    print(f"-> {out_dir}/SUMMARY_{args.season}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
