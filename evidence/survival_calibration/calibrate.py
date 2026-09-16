"""#206: is `survival_probability` a mathematical representation of the chance this player
makes it back to my next selection?

THE OWNER'S CONTRACT, stated 2026-09-16: "survival percentage needs to be a mathematical
representation of what are the chances this player makes it back to my next selection."

That makes the quantity FALSIFIABLE, and it decides how it should be judged. Not by whether the
mechanism is elegant -- not the old rank table, not the mass normalisation, not a
cluster-consumption model -- but by CALIBRATION: of all the players the engine said had a ~30%
chance, did about 30% actually come back?

WHAT THIS MEASURES. For every seat turn that has a next turn, ask the engine for each
candidate's survival_probability, then look at that seat's NEXT pick and record whether the
player was still undrafted. That yields (predicted, observed) pairs. Bucketed, they give a
reliability curve; summed, a Brier score.

THE #56 LINE, HELD EXPLICITLY. This MEASURES calibration as a diagnostic. It does not tune a
constant to minimise the error, and no number it produces may be written back into the engine as
a constant -- the capture's LIMITS forbid calibrating to one league, and that prohibition is not
softened by the error being measured rather than guessed. Deriving a mechanism from constraints
and then reporting how far it lands from reality is validation; picking whichever mechanism fits
one league best is the thing the LIMITS forbid.

TWO ARMS, because one real league cannot tell a model defect from that league's quirks.

  SMOKE -- synthetic drafters with VARIED selection rules, all of them sane. Every policy reads
  the engine's REAL valuations and differs only in how it CHOOSES: best-player-available on the
  team-agnostic number, need-first, run-following, a mild reacher. This is the controlled arm:
  the drafting behaviour is known, so a calibration failure here is the model's, not the
  league's. It also answers the owner's request for variety that is still good draft behaviour.

  REAL -- the 270 resolved picks of Greatest Show on Paper 2 (evidence/take_model/). One league,
  and the LIMITS apply.

THREE CONTROLS, because a calibration number with no control is unfalsifiable.

  ORACLE     predicts the truth (1.0 / 0.0). Must come back perfectly calibrated with Brier 0.0.
             If it does not, the SCORER is broken and every other number here is noise.
  CONSTANT   predicts the base rate for everyone. Its Brier is the variance of the outcome --
             the score to beat. A model that cannot beat it carries no information.
  VACUITY    every bucket reports its n. A rate over an empty bucket is not a rate.

Run from the REPO ROOT. Writes calibration.json beside this file, incrementally, so a container
suspend costs one arm rather than the run (#215).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import run_draft_battery as rdb

OUT = Path(__file__).with_name("calibration.json")
CAPTURE = Path("data/league_captures/fourth_and_forever.json")
BUCKETS = [(0.0, 0.1), (0.1, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5),
           (0.5, 0.6), (0.6, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]


# ---------------------------------------------------------------- selection policies
#
# Every policy reads the engine's own valuations off a real board. They differ ONLY in the
# CHOICE rule, which is what the owner asked for: variety in selection that is still good draft
# behaviour, rather than a second valuation invented for the simulation. `simulate_full_draft`
# is deliberately not used or widened -- its docstring commits it to "every chair using the real
# production engine", and that contract is worth keeping intact.

def _pick_cdme(board, roster, league):
    """Production: the engine's own top candidate, team-specific final_score."""
    return board[0]


def _pick_bpa(board, roster, league):
    """Team-AGNOSTIC best available. Ignores the roster entirely, which is how a large share of
    real drafters behave early and the behaviour the owner named directly."""
    priced = [r for r in board if r.get("universal_value") is not None]
    return max(priced, key=lambda r: r["universal_value"]) if priced else board[0]


def _required_slots(league):
    return [s for s in (league.get("roster_positions") or [])
            if s not in ("BN", "IR", "TAXI")]


def _pick_need_first(board, roster, league):
    """Fill an unfilled required starting slot before taking value. A real and common posture,
    and the one that makes boards DIVERGE, which is the mechanism behind mid-round survival."""
    have = {}
    for p in roster:
        have[p] = have.get(p, 0) + 1
    want = {}
    for slot in _required_slots(league):
        want[slot] = want.get(slot, 0) + 1
    for slot, n in want.items():
        if have.get(slot, 0) < n:
            for row in board:
                if row.get("position") == slot:
                    return row
    return _pick_bpa(board, roster, league)


def _pick_run_follower(board, roster, league, last_position=None):
    """Chases the position most recently taken -- the herd behaviour positional runs are made
    of. Falls back to the engine's own top candidate when there is nothing to chase."""
    if last_position:
        for row in board:
            if row.get("position") == last_position:
                return row
    return board[0]


def _pick_mild_reach(board, roster, league, nth=0):
    """Takes the nth-best rather than the best, cycling deterministically. A drafter with a
    slightly different board than ours -- NOT noise: no seed, fully reproducible, and it never
    reaches past the top three, so it stays good draft behaviour."""
    return board[min(nth % 3, len(board) - 1)]


POLICIES = {
    "cdme": _pick_cdme,
    "bpa": _pick_bpa,
    "need_first": _pick_need_first,
    "run_follower": _pick_run_follower,
    "mild_reach": _pick_mild_reach,
}


def bucket_of(p):
    for lo, hi in BUCKETS:
        if lo <= p < hi:
            return f"{lo:.1f}-{hi:.1f}"
    return None


def calibration(pairs):
    """Reliability curve plus Brier. `pairs` is [(predicted, observed_bool, ...), ...] -- extra
    trailing fields (gap, rank) are carried along by the collector and ignored here, so the
    scorer stays one function no matter how the decomposition grows."""
    rows = []
    for lo, hi in BUCKETS:
        members = [(r[0], r[1]) for r in pairs if lo <= r[0] < hi]
        if not members:
            rows.append({"bucket": f"{lo:.1f}-{hi:.1f}", "n": 0,
                         "predicted_mean": None, "observed_rate": None})
            continue
        rows.append({
            "bucket": f"{lo:.1f}-{hi:.1f}",
            "n": len(members),
            "predicted_mean": round(sum(p for p, _ in members) / len(members), 4),
            "observed_rate": round(sum(1 for _, o in members if o) / len(members), 4),
        })
    brier = round(sum((r[0] - (1.0 if r[1] else 0.0)) ** 2 for r in pairs) / len(pairs), 5) if pairs else None
    base = round(sum(1 for r in pairs if r[1]) / len(pairs), 4) if pairs else None
    return {"n": len(pairs), "base_rate": base, "brier": brier, "curve": rows}


RANK_BANDS = [(0, 1), (1, 3), (3, 5), (5, 10), (10, 20), (20, 10 ** 6)]


def _group(pairs, key, label, order=None):
    """Aggregate predicted-vs-observed over any grouping of the pairs.

    A single reliability curve pools every turn together, and that pooling can INVERT the
    relationship it is meant to display: survival depends on how many picks intervene, so a
    bucket of predictions drawn from short-gap and long-gap turns at once is a mixture of two
    different questions. Decomposing by gap, and by board rank, is what separates "the model is
    miscalibrated" from "the curve is a Simpson's-paradox artifact of pooling"."""
    groups = {}
    for r in pairs:
        groups.setdefault(key(r), []).append(r)
    out = []
    for k in (sorted(groups, key=order) if order else sorted(groups)):
        members = groups[k]
        out.append({
            label: k,
            "n": len(members),
            "predicted_mean": round(sum(r[0] for r in members) / len(members), 4),
            "observed_rate": round(sum(1 for r in members if r[1]) / len(members), 4),
            "brier": round(sum((r[0] - (1.0 if r[1] else 0.0)) ** 2 for r in members) / len(members), 5),
        })
    return out


def _rank_band(rank):
    for lo, hi in RANK_BANDS:
        if lo <= rank < hi:
            return f"{lo}-{hi - 1}" if hi < 10 ** 6 else f"{lo}+"
    return "?"


def simulate_and_collect(merger, players_db, league, pick_order, policy_by_seat,
                         projections, rounds_cap=None):
    """Run one draft where each seat chooses by its own policy, and collect the
    (predicted survival, actually survived) pairs the contract is about.

    THE MEASUREMENT, stated so it cannot quietly become a different one. At seat S's turn we ask
    build_snapshot for each candidate's survival_probability -- the PRODUCTION quantity, not a
    re-derivation. We remember those players. When S comes back around, we look at which of them
    are still undrafted. Predicted against observed, one pair per candidate per turn.

    SCOPE LIMIT, stated rather than buried: the policies choose from build_snapshot's NARROWED
    candidate set, not the whole pool. So "bpa" here is best-available-within-the-shortlist, not
    over all 1,100 rows. That keeps every arm on one board build per turn, and it is the same
    shortlist the engine itself decides from -- but it means these drafters are all somewhat
    more disciplined than a human with the full list in front of them.

    ABSENCE IS NOT ZERO. A candidate whose survival_probability is None was never measured and
    is EXCLUDED from the pairs, counted separately. Scoring None as 0.0 would manufacture a
    confident prediction the engine never made (#187)."""
    picks = []
    pending = {}          # seat -> (gap, [(player_id, predicted, rank), ...])
    pairs = []
    turns = []            # one row per resolved turn, for the arithmetic ceiling below
    unmeasured = 0
    last_position = None
    reach_counter = {}
    limit = len(pick_order) if rounds_cap is None else min(len(pick_order), rounds_cap)

    for i in range(limit):
        seat = str(pick_order[i])
        snap = ps.build_snapshot(merger, players_db, picks, pick_order, i, seat, league,
                                 pick_label=f"P{i + 1}",
                                 sleeper_projections=projections,
                                 sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        cands = list(snap.candidates)
        if not cands:
            break

        # Resolve anything this seat was promised last time round.
        taken = {str(p["player_id"]) for p in picks}
        promised = pending.pop(seat, None)
        if promised is not None:
            gap, rows_ = promised
            survived = 0
            for player_id, predicted, rank in rows_:
                alive = player_id not in taken
                survived += 1 if alive else 0
                pairs.append((predicted, alive, gap, rank))
            turns.append({"gap": gap, "candidates": len(rows_),
                          "taken": len(rows_) - survived})

        # Record this turn's predictions, if this seat gets another turn.
        nxt = ds.find_next_pick_index(pick_order, seat, i)
        if nxt is not None and nxt < limit:
            fresh = []
            for rank, c in enumerate(cands):
                p = c.survival_probability
                if p is None:
                    unmeasured += 1
                    continue
                fresh.append((str(c.player_id), p, rank))
            pending[seat] = (nxt - i - 1, fresh)

        # Choose, by this seat's own policy.
        policy = policy_by_seat[seat]
        rows = [{"player_id": c.player_id, "position": c.position,
                 "universal_value": c.universal_value} for c in cands]
        roster = [p["position"] for p in picks if str(p["roster_id"]) == seat]
        if policy == "run_follower":
            chosen = _pick_run_follower(rows, roster, league, last_position)
        elif policy == "mild_reach":
            n = reach_counter.get(seat, 0)
            reach_counter[seat] = n + 1
            chosen = _pick_mild_reach(rows, roster, league, n)
        else:
            chosen = POLICIES[policy](rows, roster, league)
        picks.append({"player_id": str(chosen["player_id"]), "roster_id": seat,
                      "position": chosen.get("position")})
        last_position = chosen.get("position")

    return pairs, unmeasured, picks, turns


def main():
    cap = json.loads(CAPTURE.read_text())
    league = {
        "roster_positions": cap["roster_positions"],
        "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
        "total_rosters": cap.get("total_rosters", 12),
        "settings": {"type": 2},
    }
    merger = dm.DataMerger()
    players_db, provenance = rdb.build_players_db_from_capture()
    projections = rdb.season_projections_from_capture()
    merger.set_league_format(db.league_format_hint(league))

    teams = int(league["total_rosters"])
    seats = [str(i) for i in range(1, teams + 1)]
    pick_order = ds.generate_pick_order(seats, 10, "snake")

    # VARIETY, assigned round-robin so no policy owns a favourable seat. Every one of these is a
    # defensible way to draft; none is a strawman.
    names = ["cdme", "bpa", "need_first", "run_follower", "mild_reach"]
    policy_by_seat = {s: names[i % len(names)] for i, s in enumerate(seats)}

    report = {"arm": "SMOKE", "league_rulebook": cap.get("league"),
              "universe_provenance": provenance, "teams": teams, "rounds": 10,
              "policy_by_seat": policy_by_seat, "complete": False,
              "LIMITS": ("Measures calibration as a DIAGNOSTIC. No number here may be written "
                         "back into the engine as a constant (#56, and the capture's LIMITS).")}
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    pairs, unmeasured, picks, turns = simulate_and_collect(
        merger, players_db, league, pick_order, policy_by_seat, projections)

    report["picks_simulated"] = len(picks)
    report["pairs"] = len(pairs)
    report["unmeasured_excluded"] = unmeasured
    report["engine"] = calibration(pairs)
    # CONTROLS.
    report["control_oracle"] = calibration([(1.0 if r[1] else 0.0, r[1]) for r in pairs])
    base = report["engine"]["base_rate"] or 0.0
    report["control_constant_base_rate"] = calibration([(base, r[1]) for r in pairs])
    report["control_oracle_is_perfect"] = report["control_oracle"]["brier"] == 0.0
    # ARITHMETIC CEILING. Between a turn and the same seat's next turn exactly `gap` players
    # leave the pool, so at most `gap` of that turn's candidates can be taken. A turn reporting
    # more taken than that is impossible, and would mean the collector is resolving predictions
    # against the wrong turn -- the one failure that would make every other number here fiction.
    violations = [t for t in turns if t["taken"] > t["gap"]]
    report["control_arithmetic_ceiling"] = {
        "turns_resolved": len(turns),
        "violations": len(violations),
        # Named for what it is when the control PASSES: the turn with the least headroom, not a
        # violation. Reporting the margin is what makes a clean pass informative rather than
        # merely silent -- a ceiling with 20 picks of slack never tests anything.
        "closest_to_ceiling": max((t for t in turns), key=lambda t: t["taken"] - t["gap"],
                                  default=None),
        "holds": not violations,
    }
    report["by_gap"] = _group(pairs, lambda r: r[2], "intervening_picks")
    _band_order = {f"{lo}-{hi - 1}" if hi < 10 ** 6 else f"{lo}+": i
                   for i, (lo, hi) in enumerate(RANK_BANDS)}
    report["by_rank_band"] = _group(pairs, lambda r: _rank_band(r[3]), "board_rank",
                                    order=lambda k: _band_order.get(k, 99))
    report["beats_constant"] = (report["engine"]["brier"] is not None
                                and report["engine"]["brier"] < report["control_constant_base_rate"]["brier"])
    report["complete"] = True
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    e = report["engine"]
    print(f"SMOKE arm: {len(picks)} picks, {len(pairs)} pairs, {unmeasured} unmeasured excluded")
    print(f"  policies: {policy_by_seat}")
    print(f"  base rate (actually survived): {e['base_rate']}")
    print(f"  engine Brier   : {e['brier']}")
    print(f"  constant Brier : {report['control_constant_base_rate']['brier']}   <- the score to beat")
    print(f"  oracle Brier   : {report['control_oracle']['brier']}   <- must be 0.0 or the scorer is broken")
    print(f"  beats constant : {report['beats_constant']}")
    print("  reliability curve (predicted -> observed):")
    for row in e["curve"]:
        if row["n"]:
            print(f"     {row['bucket']}  n={row['n']:<5} predicted={row['predicted_mean']:<7} observed={row['observed_rate']}")
    ceil = report["control_arithmetic_ceiling"]
    print(f"  arithmetic ceiling holds: {ceil['holds']}  "
          f"({ceil['turns_resolved']} turns, {ceil['violations']} impossible)")
    print("  BY GAP (how many picks intervene before this seat's next turn):")
    for row in report["by_gap"]:
        print(f"     gap={row['intervening_picks']:<3} n={row['n']:<5} "
              f"predicted={row['predicted_mean']:<7} observed={row['observed_rate']:<7} brier={row['brier']}")
    print("  BY BOARD RANK:")
    for row in report["by_rank_band"]:
        print(f"     rank {row['board_rank']:<5} n={row['n']:<5} "
              f"predicted={row['predicted_mean']:<7} observed={row['observed_rate']:<7} brier={row['brier']}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
