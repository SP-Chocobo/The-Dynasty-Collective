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

NO ENGINE EDIT. Every arm runs the same working tree at the same commit, in ONE process, and
differs from the baseline in exactly one thing: whether `dr.board_slot_alternatives` is the
shipped construction or the capped one, and -- for the third arm -- whether `dr.unfieldable_last`
returns its real sort key or an all-zero no-op. That is the in-process A/B the engine-measurement
skill requires, and both of the functions the cap patches document themselves as module-level and
patchable for exactly this.

THE THIRD ARM IS THE ONE THE OWNER ASKED FOR. A (the fieldability ceiling) is shipped and is what
took the engine from 0 of 12 seats to 11 of 12 on 2024; the owner's stated discomfort is with it
("I don't love forcing a ceiling"). C is a PRICING change where A is a COUNTING one, so
`capped_no_backstop` asks whether C's pricing would have made A's counting unnecessary. Pricing
alone has already failed this test once in a different guise: #30's streaming floor, without the
backstop, relocated the hoarding from defenses to KICKERS rather than removing it.

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
                    "max_reduction": 0.0, "no_reach": 0, "pool_missing": 0,
                    #: NON-VACUITY FOR THE THIRD ARM, in the same spirit. A no-backstop arm that
                    #: never reached the stand-in would be the shipped arm wearing another name.
                    "backstop_suppressed_calls": 0,
                    #: How often the #30 floor exemption saved a slot, and WHICH slots the cap
                    #: actually bit -- a cap that only ever bit K and DEF would be a #30 revert
                    #: wearing C's name, and a count that cannot tell them apart says nothing.
                    "slots_floor_exempt": 0, "capped_by_position": {},
                    #: C-prime's own counters. `levels_capped` must be > 0 in that arm or the
                    #: anchor cap never fired and the arm is C wearing another name.
                    "levels_capped": 0, "level_reduction_sum": 0.0, "max_level_reduction": 0.0,
                    "level_capped_by_position": {}}


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


#: THE #30 FLOORS THE BOARD ACTUALLY USED, remembered the same way the pool is. A streaming floor
#: is NOT a reading of the remaining pool, and `replacement_levels` applies it by ASSIGNMENT
#: (`levels[position] = float(floor)`) and raise-only -- so `level == floor` identifies a
#: floor-set level exactly, with no second model of the engine's own precedence.
_FLOORS: list = [None]


def install_floor_recorder():
    """Wrap `dr.streaming_replacement_levels` so the cap can tell a floor from a pool reading."""
    real = dr.streaming_replacement_levels

    def recorder(*args, **kwargs):
        floors = real(*args, **kwargs)
        if floors:
            _FLOORS[0] = dict(floors)
        return floors

    dr.streaming_replacement_levels = recorder
    return real


def floor_set_positions(levels) -> set:
    """Positions whose level IS a #30 streaming floor rather than a reading of the pool."""
    floors = _FLOORS[0] or {}
    return {p for p, f in floors.items()
            if p in levels and levels[p] is not None and float(levels[p]) == float(f)}


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


def capped_slot_alternatives(levels, roster_positions, exempt_floors: bool = False):
    """Formulation C: the shipped construction, capped at what the slot can actually still get.

    `exempt_floors` is the CORRECTED form, and the correction is derived rather than chosen.
    C's whole rationale is that the pool only drains, so no free player can be worth more than
    the best one undrafted now. A `#30` streaming floor is not a claim about a player at all: it
    is the season sum of each week's best WIRE option, and it is larger than any single player's
    season projection on purpose, because a manager streams. So C's premise is false exactly
    where the level is a floor, by `#30`'s own derivation -- and capping there does not correct a
    stale anchor, it reverts `#30`.

    Measured, 2024, `12T_ppr_K_DEF`, on the OPENING board before a single pick: DEF floor 146.05
    against a best remaining defense of 121.49, K floor 164.50 against 159.88. Both capped, from
    pick one to the last. `#30` was worth +328 on 2024 and +85 on 2023, so an uncorrected C arm
    measures C and a partial `#30` revert together and cannot attribute either.

    NOT EXTENDED TO `startable_floors` (superflex QB), and deliberately: that branch selects a
    RANK rather than assigning the floor's value, so `level == floor` does not identify it and a
    second model of the engine's precedence would be needed to. This format carries no
    SUPER_FLEX slot, so the case is not exercised here; it is `#34`'s ground."""
    import lineup_optimizer as lo
    priced = {p: float(v) for p, v in levels.items() if v is not None and not pd.isna(v)}
    best = best_remaining_by_position()
    if best is None:
        _CAP_STATS["pool_missing"] += 1
    floored = floor_set_positions(priced) if exempt_floors else set()
    out: dict[str, float] = {}
    for slot in lo.slots_from_roster_positions(roster_positions):
        candidates = [priced[p] for p in slot["eligible"] if p in priced]
        if not candidates:
            continue
        level_max = max(candidates)
        _CAP_STATS["slots_priced"] += 1
        # A slot whose level comes from a floor is left alone ENTIRELY rather than capped at the
        # next position down: the floor is what that slot's alternative IS.
        if floored and any(priced.get(p) == level_max for p in slot["eligible"] if p in floored):
            _CAP_STATS["slots_floor_exempt"] += 1
            out[slot["slot_id"]] = level_max
            continue
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
            _CAP_STATS["capped_by_position"][",".join(sorted(slot["eligible"]))] = (
                _CAP_STATS["capped_by_position"].get(",".join(sorted(slot["eligible"])), 0) + 1)
        out[slot["slot_id"]] = capped
    return out


#: FORMULATION C-PRIME: cap `bpa`'s ANCHOR instead of the slot alternative, keeping C's slot
#: alternatives. The derivation (evidence/DESIGN_35_CAPS_REDERIVATION.md) shows this prices every
#: row IDENTICALLY to C in balanced mode -- with `L'(p) = min(L(p), b(p))`, `bpa' = bpa + stale(p)`
#: and `adj' = adj - stale(p)`, so `team_acquisition_value` is unchanged -- while restoring the
#: registered non-positivity invariant verbatim and putting the premium back inside
#: TEAM_SPECIFIC_CAPS. That makes it the only ADMISSIBLE form of C.
#:
#: It is not identical everywhere, and this arm exists to measure exactly where it is not. Upside
#: mode scores `bpa + 0.5 * growth` and carries NO displacement term -- it reads nothing off the
#: roster -- so the cancellation has nothing to cancel against and C-prime's score exceeds C's by
#: exactly `stale(p)` on every row at a drained position. `stale(p)` is a non-negative per-position
#: constant, so it RE-ORDERS POSITIONS against each other in upside mode. Magnitude unmeasured
#: until this arm; shape derived.
#:
#: WHERE THE CAP IS APPLIED, and why not at `replacement_levels`. The level `bpa` actually uses is
#: whatever `point_replacement` holds AFTER `_fill_omitted_from_anchor` has filled the
#: exhausted-demand positions from the pre-draft anchor. Capping inside `replacement_levels` would
#: miss those; capping inside `predraft_replacement_anchor` would poison `_ANCHOR_CACHE`, which is
#: keyed by (universe, league) and carries no remaining-pool term, so one board's remaining pool
#: would leak into every later board's anchor. Wrapping `_fill_omitted_from_anchor` and capping the
#: dict it was handed, in place, after it returns, is the one seam that sees the final level and
#: leaves the cache alone -- and it runs before `_vor`, before `displacement_adjustments`, and
#: before the upside branch returns, which is every consumer that matters.
#:
#: THE BRANCH IS IDENTIFIED EXACTLY, not guessed. `_fill_omitted_from_anchor` is called once for
#: the points levels and once for the trade-value levels, and the two differ only in the anchor
#: factory they are handed: `lambda: _anchor("_points", ...)` against
#: `lambda: _anchor("trade_value", None)`. That literal is in the lambda's own `co_consts`, so the
#: wrapper reads which branch it is on from the engine's own code rather than inferring it from the
#: magnitude of the numbers. Capping a 0-100 vendor level with a season-points bound would be the
#: currency-mixing error this repository keeps removing, and a "it would be a no-op in practice"
#: argument is not a reason to risk it.
_UNCAPPED_LEVELS: list = [None]
_CPRIME_ACTIVE: list = [False]


def install_level_cap():
    """Wrap `_fill_omitted_from_anchor` so C-prime can cap the level `bpa` actually uses."""
    real = dr._fill_omitted_from_anchor

    def wrapper(levels, present_positions, startable_floors, build_anchor):
        filled = real(levels, present_positions, startable_floors, build_anchor)
        if not _CPRIME_ACTIVE[0]:
            return filled
        if "_points" not in (build_anchor.__code__.co_consts or ()):
            return filled          # the trade-value branch: a different currency, left alone
        # The UNCAPPED levels, kept for the slot alternatives, which C-prime leaves as C's.
        _UNCAPPED_LEVELS[0] = {k: v for k, v in levels.items()}
        best = best_remaining_by_position()
        if best is None:
            _CAP_STATS["pool_missing"] += 1
            return filled
        # EXEMPT exactly the levels that are ASSIGNED A VALUE rather than SELECTED FROM THE
        # REMAINING POOL. Only an assigned level can exceed the pool's own best and so be capped;
        # a rank selection cannot, by construction. #30's streaming floor is assigned
        # (`levels[position] = float(floor)`) and does exceed it -- measured on the 2024 opening
        # board at DEF 146.05 against a best remaining defense of 121.49.
        #
        # `startable_floors` is included and is REDUNDANT, which is recorded rather than quietly
        # left to look load-bearing. That branch sets `levels[position] = at_pos.iloc[rank-1]`,
        # a REMAINING player's own points, so L(p) <= b(p) always and `min(L, b) = L` is a no-op.
        # Measured draining QB on a 12T_ppr_SF board: the level holds at 207.50 while the best
        # remaining QB descends 372.46 -> 207.50, touching it exactly and never going below,
        # and one pick later the branch declines and there is no level at all. Kept because
        # removing it would be a change with no measured cause.
        floored = floor_set_positions(levels) | set(startable_floors or {})
        for position, level in list(levels.items()):
            if level is None or pd.isna(level) or position in floored:
                continue
            bound = best.get(position)
            if bound is None or bound >= float(level):
                continue
            _CAP_STATS["levels_capped"] += 1
            _CAP_STATS["level_reduction_sum"] += float(level) - bound
            _CAP_STATS["max_level_reduction"] = max(
                _CAP_STATS["max_level_reduction"], float(level) - bound)
            _CAP_STATS["level_capped_by_position"][position] = (
                _CAP_STATS["level_capped_by_position"].get(position, 0) + 1)
            levels[position] = bound
        return filled

    dr._fill_omitted_from_anchor = wrapper
    return real


def c_prime_slot_alternatives(levels, roster_positions):
    """C's slot alternatives, computed from the UNCAPPED levels.

    `levels` arrives already capped (the wrapper mutated the board's dict in place), and using it
    here would cap twice and stop being C-prime. Falling back to `levels` when nothing was recorded
    is the honest degenerate case: a board with no projected rows never reached the points branch,
    and its levels dict is empty anyway."""
    source = _UNCAPPED_LEVELS[0]
    return capped_slot_alternatives(levels if source is None else source,
                                    roster_positions, exempt_floors=True)


def floor_exempt_slot_alternatives(levels, roster_positions):
    return capped_slot_alternatives(levels, roster_positions, exempt_floors=True)


#: THE ARMS, and why the third one exists. `A` (the fieldability backstop, `unfieldable_last`) is
#: SHIPPED and measured: it is what took the engine from 0 of 12 seats to 11 of 12 on 2024. The
#: owner's stated discomfort is with it -- "I don't love forcing a ceiling" -- and C is a PRICING
#: change where A is a COUNTING one, so the live question is not only "is C worth its cost" but
#: "would C's pricing have made A's counting unnecessary". `capped_no_backstop` is the only arm
#: that can answer that, and it is the arm whose result the owner actually asked for.
#:
#: `control_no_backstop` is deliberately NOT here: it is the already-measured streaming-only arm
#: (2024 3 of 12, -18.5; 2023 0 of 12, -299.6), and re-running it would spend a season's compute
#: to reproduce a number rather than to learn one. Anyone who wants the full 2x2 in one process
#: can name it; the table admits it.
ARMS = {
    "control":             {"cap": None,           "backstop": True},
    "capped":              {"cap": "as_specified", "backstop": True},
    "capped_floor_exempt": {"cap": "floor_exempt", "backstop": True},
    "capped_no_backstop":  {"cap": "as_specified", "backstop": False},
    "capped_floor_exempt_no_backstop": {"cap": "floor_exempt", "backstop": False},
    "control_no_backstop": {"cap": None,           "backstop": False},
}

ARMS["c_prime"] = {"cap": "c_prime", "backstop": True}

CAP_FUNCTIONS = {"as_specified": capped_slot_alternatives,
                 "floor_exempt": floor_exempt_slot_alternatives,
                 "c_prime": c_prime_slot_alternatives}

#: `unfieldable_last` returns a SORT KEY, one row per candidate, 1 meaning "demote". All-zero is
#: the no-op, and it is built the same way `feasibility_first` is switched off in the skill's own
#: example -- an index-aligned Series of the right dtype, never a bare 0, so the sort behaves
#: identically except for this one key.
def _no_backstop(scored, picks, players_db, my_roster_id, roster_positions, pool_scope="all"):
    _CAP_STATS["backstop_suppressed_calls"] += 1
    return pd.Series(0, index=scored.index, dtype=int)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--season", default="2024")
    parser.add_argument("--out", required=True,
                        help="a DIRECTORY for the arm reports and the summary")
    parser.add_argument("--seats", type=int, default=0)
    parser.add_argument("--streaming", action="store_true", default=True,
                        help="grade the SHIPPED path (#30's floor wired), which is the "
                             "configuration the cap would ship into")
    parser.add_argument("--no-streaming", dest="streaming", action="store_false")
    parser.add_argument("--arms", nargs="+", default=["control", "capped", "capped_no_backstop"],
                        choices=sorted(ARMS),
                        help="which arms to run, in order. The FIRST is the baseline every "
                             "paired delta is taken against.")
    args = parser.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    shipped = dr.board_slot_alternatives
    shipped_backstop = dr.unfieldable_last
    install_pool_recorder()
    install_floor_recorder()
    install_level_cap()

    common = ["--season", args.season]
    if args.streaming:
        common.append("--streaming")
    if args.seats:
        common += ["--seats", str(args.seats)]

    arms = {}
    for name in args.arms:
        # ONE PROCESS, ONE CODE VERSION, ONE THING TOGGLED PER ARM.
        config = ARMS[name]
        dr.board_slot_alternatives = CAP_FUNCTIONS.get(config["cap"], shipped)
        _CPRIME_ACTIVE[0] = config["cap"] == "c_prime"
        _UNCAPPED_LEVELS[0] = None
        dr.unfieldable_last = (shipped_backstop if config["backstop"] else _no_backstop)
        for key, value in list(_CAP_STATS.items()):
            _CAP_STATS[key] = {} if isinstance(value, dict) else type(value)(0)
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
    dr.unfieldable_last = shipped_backstop
    _CPRIME_ACTIVE[0] = False

    # PAIRED BY SEAT, against the FIRST arm named. The unpaired means are in the arm blocks; the
    # paired delta is the measurement, because every arm drafts the same seat against the same
    # field, so a seat is its own control and the seat-to-seat variance drops out.
    base = args.arms[0]
    paired_all = {}
    for name in args.arms[1:]:
        deltas = {}
        for seat, base_total in arms[base]["engine_totals"].items():
            other = arms[name]["engine_totals"].get(seat)
            if other is not None:
                deltas[seat] = round(other - base_total, 2)
        paired_all[f"{name}_minus_{base}"] = {
            "by_seat": deltas,
            "improved": sum(1 for v in deltas.values() if v > 0),
            "unchanged": sum(1 for v in deltas.values() if v == 0),
            "worsened": sum(1 for v in deltas.values() if v < 0),
            "total": round(sum(deltas.values()), 2),
            "mean": round(sum(deltas.values()) / len(deltas), 2) if deltas else None,
        }
    summary = {
        "_comment": ("#35 Formulation C (cap each slot's free-player alternative at the best "
                     "REMAINING player eligible for that slot) vs the shipped construction, "
                     "graded on realized weekly outcomes. One process, one commit, one thing "
                     "toggled. See evidence/design_35/phantom_cap_experiment.py."),
        "season": args.season,
        "streaming_floor": bool(args.streaming),
        "arms": arms,
        "arm_order": list(args.arms),
        "baseline_arm": base,
        "paired": paired_all,
    }
    (out_dir / f"SUMMARY_{args.season}.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(f"\n=== #35 C vs shipped, {args.season} realized ===")
    for name, block in arms.items():
        print(f"{name:>8}: wins {block['wins']}/{block['seats']}  "
              f"mean {block['mean_delta']:+.1f}  median {block['median_delta']:+.1f}")
    for key, block in paired_all.items():
        print(f"paired {key}: {block['improved']} improved, {block['unchanged']} unchanged, "
              f"{block['worsened']} worsened, total {block['total']:+.1f}, mean {block['mean']}")
    for name in args.arms:
        print(f"cap fired ({name}): {arms[name]['cap_stats']}")
    print(f"-> {out_dir}/SUMMARY_{args.season}.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
