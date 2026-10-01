"""GATE B: what the frozen engine ANSWERS, captured so a refactor can be proven not to change it.

`v4-freeze` certifies that the engine was correct IN ITS CURRENT SHAPE: 4,166 tests, 8 of 8
mutation arms, two full batteries. None of that survives an architectural move on its own. The
suites prove the code is self-consistent, and a refactored engine can be self-consistent too --
extracting a service layer, generating a thin runtime and rerouting a client all change shape,
and the existing gates would stay green across a change that quietly moved an answer.

So this file is a CAMERA, not a laboratory. It photographs what the engine answers at the
boundary a service would call, and `--check` re-takes the photograph and diffs it. It contains
no assertions about whether the answers are RIGHT -- that is what the suite and the batteries are
for, and duplicating their judgement here would be a second source of truth (`#126`).

WHAT "THE BOUNDARY" IS, derived rather than assumed: `app.py` reaches the engine through
`pick_synthesis.build_snapshot` and essentially nothing else. Counted over the hull, that is 3
calls against 1 for `draft_room.simulate_opponent_picks` and 1 for `build_mock_league`. So the
snapshot IS the contract a service layer would expose, and capturing it captures the thing that
must not move.

THREE STATES PER FORMAT, AND THE OPENING ONE ALONE WOULD HAVE PROVEN NOTHING. Measured here on
the first exploration run, at `12T_ppr_K_DEF` pick 1.01 over 72 candidates:

    displacement_adj   present 72/72   nonzero  0
    depth_exposure     present 72/72   nonzero  0
    risk_adj           present 72/72   nonzero  0
    need_bonus         present 72/72   nonzero 72

Those three are not quiet, they are STRUCTURALLY zero: with every dedicated slot open each
position's probe evicts its own phantom, so `displacement_adj` is identically zero for every
position at once; `depth_exposure` is only measured once a bench exists; `risk_adj` needs a
designation to price. A baseline taken at the opening board would pin them at a value the state
cannot produce, and a refactor that broke all three would diff clean. So each format is also
captured mid-draft and late, replaying a REAL committed draft rather than a synthetic one.

THE HISTORIES ARE PRODUCTION'S, NOT INVENTED. `evidence/batteries/VDS_*.json` carries each arm's
own `pick_sequence` -- the actual players its draft took, in order -- so a mid-draft state here is
a state the engine really reached, with the roster shapes and drained pools that come with it. A
hand-made history would be a second source of truth about what a draft looks like.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import time

import store_io

BASELINE_PATH = pathlib.Path("evidence/engine_baseline/ENGINE_BASELINE.json")

#: The committed draft whose states are replayed. Pinned by path so a later VDS run does not
#: silently move the baseline's inputs underneath it -- the capture would still be internally
#: consistent and would be about a different draft (`#245`).
VDS_RUN = pathlib.Path("evidence/batteries/VDS_2026-10-01_varied_drafting_strategy_dd4ade7.json")

#: The control strategy's arm supplies each format's history. `sharp_auto` is `vds_battery`'s own
#: CONTROL_STRATEGY, so these are the states the engine reaches with no strategy perturbation.
HISTORY_STRATEGY = "sharp_auto"

#: Fields of CandidateSnapshot that are not part of the engine's answer and would make every
#: capture differ for reasons that are not behavioural. Empty today, and kept as a named, empty
#: register rather than an absent concept: the day one is needed, it needs a reason beside it,
#: the way `draft_battery.UNCOVERED_AXES` does.
VOLATILE_CANDIDATE_FIELDS: dict[str, str] = {}

#: Same, for the snapshot envelope. `data_freshest_date` and `players_db_stamp` describe the
#: DATA the answer was computed over, not the answer -- they move when the capture is refreshed
#: and would force a baseline rewrite on every vendor update while telling you nothing about the
#: engine. They are recorded in the baseline's provenance block instead, where a reader can see
#: them without them gating the diff.
VOLATILE_SNAPSHOT_FIELDS = {
    "data_freshest_date": "describes the vendor data's age, not the engine's answer",
    "players_db_stamp": "a hash of the pool; moves on any data refresh, gates nothing",
}


def _jsonable(value):
    """JSON with the engine's absence contract intact.

    `None` must survive as `null` and must never become `0.0` or `""` -- `#187` is enforced
    engine-wide and a serialiser that blurred it would make the baseline unable to see the one
    class of regression this repo cares most about. frozensets become SORTED lists so set
    ordering, which is not part of the answer, cannot produce a spurious diff.
    """
    if value is None or isinstance(value, (bool, int, str)):
        return value
    if isinstance(value, float):
        # NaN is not JSON and is not None: it is the other absence this engine uses. Recorded as
        # a marker string so it round-trips and cannot be confused with a measured number.
        return "__NaN__" if value != value else value
    if isinstance(value, (frozenset, set)):
        return sorted(_jsonable(v) for v in value)
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in sorted(value.items(), key=lambda kv: str(kv[0]))}
    return str(value)


def _candidate_record(candidate) -> dict:
    import dataclasses
    return {f.name: _jsonable(getattr(candidate, f.name))
            for f in dataclasses.fields(candidate)
            if f.name not in VOLATILE_CANDIDATE_FIELDS}


def _snapshot_record(snap) -> dict:
    import dataclasses
    out = {}
    for f in dataclasses.fields(snap):
        if f.name in VOLATILE_SNAPSHOT_FIELDS or f.name == "candidates":
            continue
        out[f.name] = _jsonable(getattr(snap, f.name))
    out["candidates"] = [_candidate_record(c) for c in (snap.candidates or [])]
    return out


def _states_for(seq_len: int, teams: int, pick_order: list, me) -> list[dict]:
    """Which turns to photograph, DERIVED from the format's own length (`#56`).

    Three, each chosen for a property it alone has:

      opening -- the pre-draft anchor path, and the only state where `replacement_levels` runs
                 over the full pool.
      mid     -- round 9 or later, because `depth_exposure` is not MEASURED until a bench
                 exists and `displacement_adj` needs occupied slots to evict against.
      late    -- a drained board. A pool defect that does not remove itself looks harmless on
                 the opening board and dominates by the end: 5 of 72 candidates at the open
                 against 26 of 26 at round 16, measured on the backtest's ghost rows.

    EVERY TURN IS ONE OF MINE, and mid/late prefer a turn with real picks AHEAD of it.
    `survival_probability`, `positional_forfeit` and `rival_premium` are computed over the gap to
    MY NEXT PICK, so a turn with no intervening picks reports them as a clean null -- 0.00 for
    269 of 269 candidates, measured once on exactly that mistake. Hardcoding indices would also
    put `12T_ppr_SHORT_DRAFT` (8 rounds) and `HEAVY_IDP` (18) at incomparable depths.
    """
    mine = [i for i, seat in enumerate(pick_order[:seq_len]) if seat == me]
    if not mine:
        raise RuntimeError("no turn in this draft belongs to the captured seat")

    def with_gap_ahead(candidates: list[int]) -> list[int]:
        out = []
        for i in candidates:
            nxt = next((j for j in mine if j > i), None)
            if nxt is not None and nxt - i > 1:
                out.append(i)
        return out

    bench_opens = teams * 8          # first pick of round 9
    mid_pool = with_gap_ahead([i for i in mine if i >= bench_opens]) or \
               with_gap_ahead([i for i in mine if i >= seq_len // 2]) or mine[len(mine) // 2:]
    late_pool = with_gap_ahead([i for i in mine if i >= int(seq_len * 0.80)]) or \
                [i for i in mine if i >= int(seq_len * 0.80)] or mine[-1:]
    return [
        {"name": "opening", "index": mine[0]},
        {"name": "mid", "index": mid_pool[0]},
        {"name": "late", "index": late_pool[-1]},
    ]


def _picks_through(seq: list, index: int, pick_order: list, teams: int) -> list[dict]:
    """The pick history in PRODUCTION'S SHAPE, which is part of the input's identity.

    `mode="auto"` resolves upside-vs-balanced scoring from the CURRENT ROUND, and reads the round
    off these records. A history of `{player_id, roster_id}` therefore runs the whole capture in
    BALANCED mode while production is in UPSIDE -- two different valuations, no error and no
    warning, and a completely different top of the board. That cost a published finding, so the
    required fields are asserted rather than assumed.
    """
    import league_config as lc
    picks = [{"pick_no": i + 1, "round": lc.round_of(i, teams),
              "roster_id": pick_order[i], "player_id": str(pid)}
             for i, pid in enumerate(seq[:index])]
    if picks:
        required = {"pick_no", "round", "roster_id", "player_id"}
        missing = required - set(picks[0])
        assert not missing, f"pick records are missing {missing}; mode='auto' reads `round`"
    return picks


def capture() -> dict:
    """Photograph every format at every state. Returns the baseline document."""
    import data_merger as dm
    import draft_battery as db
    import draft_room as dr
    import draft_strategy as ds
    import pick_synthesis as ps
    import run_draft_battery as rdb
    import vds_battery as vb

    started = time.time()
    merger = dm.DataMerger()
    players_db, pool_provenance = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    scoring = rdb.scoring_settings_from_capture()

    vds = json.loads(VDS_RUN.read_text(encoding="utf-8"))
    histories = {r["format"]: r for r in vds["results"]
                 if r.get("strategy") == HISTORY_STRATEGY}

    by_label = {a["label"]: a for a in db.league_matrix(scoring)}
    missing = [f for f in vb.FORMATS if f not in by_label]
    if missing:
        raise RuntimeError(
            f"formats absent from league_matrix: {missing}. The matrix's labels have changed; "
            f"fix this list rather than capturing a baseline over fewer formats than it claims.")

    arms = []
    for label in vb.FORMATS:
        arm = by_label[label]
        league, teams = arm["league"], arm["teams"]
        history = histories.get(label)
        if history is None:
            raise RuntimeError(f"no {HISTORY_STRATEGY} history for {label} in {VDS_RUN}")

        # THE FORMAT'S OWN EXPORT. set_league_format selects a different rankings file; skipping
        # it drafts every format from one export and makes standard/half_ppr/ppr byte-identical.
        hint = db.league_format_hint(league)
        merger.set_league_format(hint)

        seats = [str(i) for i in range(1, teams + 1)]
        pick_order = ds.generate_pick_order(seats, arm["rounds"], "snake")
        me = pick_order[0]
        seq = history["pick_sequence"]

        states = []
        for state in _states_for(len(seq), teams, pick_order, me):
            idx = state["index"]
            picks = _picks_through(seq, idx, pick_order, teams)
            t0 = time.time()
            snap = ps.build_snapshot(
                merger, players_db, picks, pick_order, idx, me, league,
                pick_label=f"{(idx // teams) + 1}.{(idx % teams) + 1:02d}",
                mode="auto",
                sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM,
            )
            record = _snapshot_record(snap)
            cands = snap.candidates or []
            if not cands:
                raise RuntimeError(f"{label}/{state['name']}: zero candidates -- a baseline over "
                                   f"an empty population is not a baseline")
            # WHICH TERMS THIS STATE CAN EXERCISE, recorded beside the answer. A term reading
            # 0.00 because the state cannot produce it is not evidence that it does not matter,
            # and a future reader comparing states needs to see which ones were reachable here.
            reach = {}
            for term in ("displacement_adj", "depth_exposure", "risk_adj", "need_bonus",
                         "survival_probability", "rival_premium", "positional_forfeit",
                         "growth_signal", "waiting_cost", "time_horizon_adj"):
                vals = [getattr(c, term, None) for c in cands]
                present = [v for v in vals if v is not None and v == v]
                reach[term] = {"present": len(present),
                               "nonzero": sum(1 for v in present if v != 0),
                               "of": len(vals)}
            states.append({
                "state": state["name"], "pick_index": idx,
                "picks_consumed": len(picks), "candidates": len(cands),
                "seconds": round(time.time() - t0, 2),
                "term_reach": reach, "snapshot": record,
            })
            print(f"  {label:22s} {state['name']:7s} idx={idx:3d} "
                  f"candidates={len(cands):3d} {time.time()-t0:5.1f}s", flush=True)

        arms.append({"format": label, "teams": teams, "rounds": arm["rounds"],
                     "format_hint": hint, "history_from": history["label"],
                     "states": states})

    return {
        "_comment": ("What the engine ANSWERS at the boundary app.py calls, per format per draft "
                     "state. Regenerate with `python3 engine_baseline.py --write`; compare a "
                     "candidate tree with `--check`. See engine_baseline.py for why three states "
                     "and why the opening one alone proves nothing."),
        "provenance": {
            "commit": subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True,
                                     text=True).stdout.strip(),
            "tree": subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True,
                                   text=True).stdout.strip(),
            "players": len(players_db), "pool_provenance": _jsonable(pool_provenance),
            "season_projections": len(season),
            "vds_run": str(VDS_RUN), "history_strategy": HISTORY_STRATEGY,
            "seconds": round(time.time() - started, 1),
        },
        "volatile_fields_excluded": VOLATILE_SNAPSHOT_FIELDS,
        "arms": arms,
    }


def _diff(recorded, fresh, path="") -> list[str]:
    """Every place the two answers differ, as readable paths. Not a boolean (`#187` again: a
    bare True/False cannot say WHAT moved, and an equivalence claim nobody can inspect is worth
    about as much as a test with no assertion)."""
    out = []
    if type(recorded) is not type(fresh) and not (
            isinstance(recorded, (int, float)) and isinstance(fresh, (int, float))):
        return [f"{path}: type {type(recorded).__name__} -> {type(fresh).__name__}"]
    if isinstance(recorded, dict):
        for key in sorted(set(recorded) | set(fresh)):
            if key not in recorded:
                out.append(f"{path}.{key}: ABSENT -> {fresh[key]!r}")
            elif key not in fresh:
                out.append(f"{path}.{key}: {recorded[key]!r} -> ABSENT")
            else:
                out.extend(_diff(recorded[key], fresh[key], f"{path}.{key}"))
    elif isinstance(recorded, list):
        if len(recorded) != len(fresh):
            out.append(f"{path}: length {len(recorded)} -> {len(fresh)}")
        for i, (a, b) in enumerate(zip(recorded, fresh)):
            out.extend(_diff(a, b, f"{path}[{i}]"))
    elif recorded != fresh:
        out.append(f"{path}: {recorded!r} -> {fresh!r}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--write", action="store_true",
                        help="record the current engine's answers as the baseline")
    parser.add_argument("--check", action="store_true",
                        help="re-take the capture and diff it against the recorded baseline")
    parser.add_argument("--limit", type=int, default=40,
                        help="how many differences to print before truncating")
    args = parser.parse_args(argv)
    if not (args.write or args.check):
        parser.error("choose --write or --check")

    # THE RECORD IS READ BEFORE THE CAPTURE IS PAID FOR. `--check` used to capture first and
    # only then look for the baseline, so a missing record cost a full 150-second sweep before
    # reporting that it had nothing to compare against. Checked here, it costs nothing -- and the
    # verdict is the one `assertion_floors` already had to learn: a check with no record is
    # holding NOTHING, which is not the same as nothing having changed.
    recorded = None
    if args.check:
        if not BASELINE_PATH.exists():
            print(f"{BASELINE_PATH} does not exist -- this check is holding NOTHING, which is "
                  f"not the same as nothing having changed. Run --write at a tree you trust.")
            return 2
        # `read_state`, not `read`: it returns the one bit that separates a DAMAGED store from
        # an absent one, and the two mean opposite things here. An unparseable baseline must not
        # read as "nothing recorded" and silently become a clean verdict.
        recorded, readable = store_io.read_state(BASELINE_PATH, None)
        if not readable or recorded is None:
            print(f"{BASELINE_PATH} is unreadable -- holding NOTHING, which is not the same as "
                  f"nothing having changed. Run --write at a tree you trust.")
            return 2

    print(f"capturing the engine boundary at {subprocess.run(['git','rev-parse','--short','HEAD'], capture_output=True, text=True).stdout.strip()}", flush=True)
    fresh = capture()

    if args.write:
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        # THROUGH store_io, which is this repo's one home for a durable store (`#126`), and the
        # guard in test_store_io is what caught this file writing its own JSON directly. The
        # baseline IS a store by that module's own distinction: it is not re-fetchable, the
        # damaged bytes would be the only copy, and overwriting a store found damaged is how a
        # transient torn read becomes permanent loss.
        #
        # THE RETURN VALUE IS CHECKED BECAUSE IT CAN DECLINE. `store_io.write` refuses to
        # replace a store this process has found unparseable and says so in a bool -- and its
        # own docstring records what ignoring that cost downstream: a caller reported success
        # for a batch that never reached disk. A capture that silently did not land, reported as
        # a written baseline, would be worse here than no baseline at all.
        if not store_io.write(BASELINE_PATH, fresh):
            print(f"\n{BASELINE_PATH} was NOT written -- store_io declined, which means it has "
                  f"found the existing file unparseable and is refusing to overwrite the only "
                  f"copy. Move the damaged file aside deliberately, then re-run.")
            return 2
        states = sum(len(a["states"]) for a in fresh["arms"])
        cands = sum(s["candidates"] for a in fresh["arms"] for s in a["states"])
        print(f"\nwrote {BASELINE_PATH}")
        print(f"  {len(fresh['arms'])} formats, {states} states, {cands} candidate records, "
              f"{fresh['provenance']['seconds']}s")
        return 0

    # The provenance block is ABOUT the capture, not the answer, so it is reported and not
    # compared -- a baseline recorded at another commit is the normal case for this check.
    print(f"\nbaseline recorded at {recorded['provenance']['commit'][:12]} "
          f"over {recorded['provenance']['players']} players")
    print(f"this tree   is         {fresh['provenance']['commit'][:12]} "
          f"over {fresh['provenance']['players']} players")
    if recorded["provenance"]["players"] != fresh["provenance"]["players"]:
        print("\nTHE POOL CHANGED SIZE. Any difference below may be about the data rather than "
              "the engine; re-run against the baseline's own capture before reading it as a "
              "behavioural change.")

    differences = _diff(recorded["arms"], fresh["arms"], "arms")
    # `seconds` is wall-clock and differs on every run; it is in the document because a reader
    # wants it, and it is not an answer. FILTERED BEFORE THE VERDICT IS DECIDED, not after.
    #
    # THE VERDICT USED TO BRANCH ON THE UNFILTERED LIST, which meant a clean tree -- whose only
    # differences are the 18 per-state timings -- fell past the success path and printed the
    # regression prose over `0 behavioural difference(s)`, returning 1. A check that reports
    # failure on a passing run is the same defect as one that reports success on a failing run,
    # and this file's own subject is catching exactly that. It is the second time this session
    # that a verifier of mine printed the failure branch on the pass path; the fix is to compute
    # the thing the verdict is about FIRST and branch on that alone.
    timing_only = [d for d in differences if d.endswith("seconds") or ".seconds:" in d]
    behavioural = [d for d in differences if d not in timing_only]

    if not behavioural:
        states = sum(len(a["states"]) for a in fresh["arms"])
        cands = sum(s["candidates"] for a in fresh["arms"] for s in a["states"])
        print(f"\nIDENTICAL: {len(fresh['arms'])} formats, {states} states, {cands} candidate "
              f"records, every field. This tree answers exactly as the baseline does.")
        if timing_only:
            print(f"  ({len(timing_only)} wall-clock timing difference(s), which are not answers)")
        return 0

    print(f"\n{len(behavioural)} behavioural difference(s) "
          f"({len(timing_only)} timing-only, ignored):\n")
    for line in behavioural[:args.limit]:
        print(f"  {line}")
    if len(behavioural) > args.limit:
        print(f"  ... and {len(behavioural) - args.limit} more")
    print("\nThis tree does NOT answer as the baseline does. Either the change was intended -- in "
          "which case declare a new engine version, enumerate the deltas and re-run --write -- or "
          "it was not, and this is the regression the baseline exists to catch.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
