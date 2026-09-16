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

  REAL -- the real picks of Greatest Show on Paper 2 (evidence/real_drafts/extracted/), resolved
  to player ids by evidence/take_model/observed_take_distribution.resolve_picks -- the SAME
  resolver the take-model measurement used, imported rather than copied. 301 of the 360 turns
  carry a resolvable player; 48 are rookie-pick placeholders and 11 cannot be resolved (7
  illegible, 3 unmatched, 1 ambiguous). One league, and the LIMITS apply. Seat identity is the
  PICKING team (82 of 360 picks were traded), because "my next selection" belongs to whoever
  actually picks next, not to the slot. Every prediction is resolved against the REAL pick
  sequence: was the player still undrafted when that team actually picked again.

THREE CONTROLS, because a calibration number with no control is unfalsifiable.

  ORACLE     predicts the truth (1.0 / 0.0). Must come back perfectly calibrated with Brier 0.0.
             If it does not, the SCORER is broken and every other number here is noise.
  CONSTANT   predicts the base rate for everyone. Its Brier is the variance of the outcome --
             the score to beat. A model that cannot beat it carries no information.
  VACUITY    every bucket reports its n. A rate over an empty bucket is not a rate.

Run from the REPO ROOT, never cd first (DataMerger resolves its baseline relative to cwd):
    PYTHONDONTWRITEBYTECODE=1 python3 evidence/survival_calibration/calibrate.py [smoke|real]

SMOKE (the default) writes calibration.json beside this file; REAL writes calibration_real.json
and its raw pairs to calibration_real_raw.json. Separate files so a rerun of one arm never
clobbers the other. Both are written incrementally -- SMOKE once per arm, REAL every 12 turns
with `complete: false` -- so a container suspend costs a checkpoint rather than the run (#215).
Both arms go through ONE scorer, assemble_scores(): one calibration(), one _group(), the same
three controls. A second scorer would be a second source of truth for the same verdict.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "take_model"))

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import run_draft_battery as rdb

import observed_take_distribution as otd   # noqa: E402  (evidence/take_model, path above)

OUT = Path(__file__).with_name("calibration.json")
OUT_REAL = Path(__file__).with_name("calibration_real.json")
OUT_REAL_RAW = Path(__file__).with_name("calibration_real_raw.json")
CAPTURE = Path("data/league_captures/fourth_and_forever.json")
REAL_BOARD = Path("evidence/real_drafts/extracted/greatest_show_on_paper_2_board.json")
REAL_RULEBOOK = Path("data/league_captures/greatest_show_on_paper_2.json")
REAL_CHECKPOINT_EVERY = 12
LIMITS = ("Measures calibration as a DIAGNOSTIC. No number here may be written back into the "
          "engine as a constant (#56, and the capture's LIMITS).")
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

        # MY OWN PICK IS NOT A SURVIVAL FAILURE. The contract asks what the chances are that a
        # player "makes it back to my next selection". The player I take at THIS turn never had
        # to make it back -- he is mine. Leaving him in the pairs scores the engine wrong for a
        # removal the engine did not predict and could not have: it is the drafter's own choice.
        # This lands almost entirely on board[0], which cdme, run_follower and a third of
        # mild_reach all take, so it biases exactly the rank band the result turns on.
        # Found by the arithmetic ceiling, which failed 102 of 108 turns by exactly +1.
        if seat in pending:
            gap_, rows_ = pending[seat]
            mine = str(chosen["player_id"])
            pending[seat] = (gap_, [r for r in rows_ if r[0] != mine])

    return pairs, unmeasured, picks, turns


def assemble_scores(report, pairs, turns):
    """THE ONE SCORER. Both arms hand their (predicted, observed, gap, rank) pairs and per-turn
    rows here and nowhere else: one calibration(), one _group(), the same three controls, the
    same arithmetic ceiling. Mutates and returns `report`."""
    report["pairs"] = len(pairs)
    report["engine"] = calibration(pairs)
    # CONTROLS.
    report["control_oracle"] = calibration([(1.0 if r[1] else 0.0, r[1]) for r in pairs])
    base = report["engine"]["base_rate"] or 0.0
    report["control_constant_base_rate"] = calibration([(base, r[1]) for r in pairs])
    report["control_oracle_is_perfect"] = report["control_oracle"]["brier"] == 0.0
    # ARITHMETIC CEILING. `gap` counts the picks made by OTHER seats between this turn and this
    # seat's next one, and this seat's own pick is excluded from the pairs above, so at most
    # `gap` of a turn's scored candidates can be taken. A turn reporting more than that is
    # impossible, and would mean the collector is resolving predictions against the wrong turn
    # -- the one failure that would make every other number here fiction.
    #
    # This control has already earned its place: on the first decomposed run it failed 102 of
    # 108 turns, all by exactly +1, and the +1 was the drafter's own pick being scored as a
    # survival failure. The pooled reliability curve gave no hint of it.
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
    # THE TIGHTER CEILING, where a turn row carries one. In the REAL arm some intervening turns
    # remove no identifiable player (rookie-pick placeholders, unresolved picks), so the bound
    # that actually binds is the count of RESOLVED intervening picks, not the raw gap. Same
    # control, tighter number; reported separately so the two never get confused.
    if any("gap_resolved" in t for t in turns):
        tight = [t for t in turns if t["taken"] > t["gap_resolved"]]
        report["control_arithmetic_ceiling_resolved"] = {
            "turns_resolved": len(turns),
            "violations": len(tight),
            "closest_to_ceiling": max((t for t in turns),
                                      key=lambda t: t["taken"] - t["gap_resolved"], default=None),
            "holds": not tight,
        }
    report["by_gap"] = _group(pairs, lambda r: r[2], "intervening_picks")
    _band_order = {f"{lo}-{hi - 1}" if hi < 10 ** 6 else f"{lo}+": i
                   for i, (lo, hi) in enumerate(RANK_BANDS)}
    report["by_rank_band"] = _group(pairs, lambda r: _rank_band(r[3]), "board_rank",
                                    order=lambda k: _band_order.get(k, 99))
    report["beats_constant"] = (report["engine"]["brier"] is not None
                                and report["engine"]["brier"] < report["control_constant_base_rate"]["brier"])
    return report


def _print_summary(report, headline):
    e = report["engine"]
    print(headline)
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
          f"({ceil['turns_resolved']} turns, {ceil['violations']} impossible)  "
          f"closest: {ceil['closest_to_ceiling']}")
    if "control_arithmetic_ceiling_resolved" in report:
        c2 = report["control_arithmetic_ceiling_resolved"]
        print(f"  tighter ceiling (resolved intervening picks) holds: {c2['holds']}  "
              f"({c2['violations']} impossible)  closest: {c2['closest_to_ceiling']}")
    print("  BY GAP (how many picks intervene before this seat's next turn):")
    for row in report["by_gap"]:
        print(f"     gap={row['intervening_picks']:<3} n={row['n']:<5} "
              f"predicted={row['predicted_mean']:<7} observed={row['observed_rate']:<7} brier={row['brier']}")
    print("  BY BOARD RANK (rank among the narrowed candidates, 0 = the engine's own top):")
    for row in report["by_rank_band"]:
        print(f"     rank {row['board_rank']:<5} n={row['n']:<5} "
              f"predicted={row['predicted_mean']:<7} observed={row['observed_rate']:<7} brier={row['brier']}")


# ---------------------------------------------------------------- the REAL arm

def _source_state():
    """Which engine code this measurement ran on. The three engine modules are edited
    concurrently on this branch, so a hash beside the number is the only way a reader can
    tell two runs apart (the before/after rule in the engine-measurement skill)."""
    files = ("draft_strategy.py", "pick_synthesis.py", "draft_room.py")
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True,
                              text=True, check=False).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", *files],
                               capture_output=True, text=True, check=False).stdout.strip().splitlines()
    except OSError:
        head, dirty = None, ["<git unavailable>"]
    return {"git_head": head, "engine_files_modified_in_tree": dirty,
            "sha256_12": {f: hashlib.sha256(Path(f).read_bytes()).hexdigest()[:12] for f in files}}


def real_collect(merger, players_db, league, picks_all, resolved, projections, checkpoint=None):
    """Replay the real draft turn by turn and collect the (predicted survival, actually
    survived) pairs, resolved against the REAL pick sequence.

    THE MEASUREMENT, same as the SMOKE arm's. At turn i the team on the clock is asked (via
    build_snapshot, the production path) for each candidate's survival_probability. Those
    predictions are held until that same TEAM actually picks again, at which point each held
    player is scored: still undrafted then, or not. One pair per candidate per turn.

    WHO IS "ME". `pick_order` is the real sequence of PICKING teams (`picked_by`), not the slot
    owners -- 82 of 360 picks in this draft were traded, and the contract's "my next selection"
    belongs to whoever selects next. Seats are the team's original slot number so ids stay
    numeric like every other caller's. The engine's own `intervening_picks` is cross-checked
    against this harness's gap at every measured candidate and the run STOPS on a mismatch:
    a disagreement there means predictions are being resolved against the wrong turn, which
    would make every other number fiction.

    WHAT THE ENGINE SEES. `picks` carries production's shape ({pick_no, round, roster_id,
    player_id}) so `PickSnapshot.round` is the real round (SMOKE's picks carry no round, so its
    snapshots all read round 1 -- that reaches pick_necessity only, not survival). Turns that
    remove no identifiable player (48 rookie-pick placeholders, 11 unresolved picks) stay in
    pick_order -- they intervene -- but add nothing to `picks`, so the engine's pace terms see
    len(picks) slightly below the true pick count. Stated, not hidden.

    EXCLUSIONS, each counted, none scored as anything:
      unmeasured        survival_probability is None -- never measured (#187). Not 0.0.
      own_pick          the player this team took at THIS turn. He never had to make it back.
      unknowable        a candidate whose name matches an UNRESOLVED real pick made before the
                        resolution turn. His fate is unknown to the harness (an illegible or
                        unmatched pick took him, or did not), so he is not scored -- and he is
                        not resolved to an id either, because that would be guessing.
        ghost           the subset of those whose matching unresolved pick came BEFORE the
                        prediction: the engine is predicting for a player already gone.
      undraftable_rookie a 2026 rookie (years_exp == 0 in the capture). This was a January-2026
                        startup with a separate rookie draft (the 48 placeholders), so the 2026
                        class could not be taken by anyone; a player nobody can take has no
                        survival question. The flag is derived from the capture, and 0 of the
                        301 resolved real picks carry it. Kept aside and reported as a
                        sensitivity, so the effect of excluding them is visible, not assumed.

    `checkpoint(pairs, turns, counts, done)` is called every REAL_CHECKPOINT_EVERY turns."""
    slot_team = {p["slot"]: p["team"] for p in picks_all}
    team_slot = {t: str(s) for s, t in slot_team.items()}
    pick_order = [team_slot[p["picked_by"]] for p in picks_all]

    # Unresolved-but-named turns, for the unknowable exclusion. A truncated name ("Croskey-M…")
    # matches by prefix; everything else must match the resolver's own normalisation exactly.
    unresolved = []
    for idx, p in enumerate(picks_all):
        if p["pick_no"] in resolved or p.get("is_rookie_pick_placeholder") or not p.get("raw_player"):
            continue
        raw = p["raw_player"]
        nm = dm.normalize_name(otd.SUFFIX.sub("", raw.replace("…", "").replace(".", "")
                                              .replace("'", "")))
        unresolved.append((idx, nm, raw.endswith("…"), raw))

    def _unresolved_hit(name, before_index):
        n = dm.normalize_name(name)
        for idx, nm, prefix, _raw in unresolved:
            if idx < before_index and (n.startswith(nm) if prefix else n == nm):
                return idx
        return None

    eng_picks = []
    pending = {}         # seat -> (gap, gap_resolved, [(pid, p, rank)], [(pid, p, rank)] rookies)
    pairs, rookie_pairs, turns = [], [], []
    counts = {"unmeasured": 0, "own_pick": 0, "unknowable": 0, "ghost": 0,
              "undraftable_rookie": 0, "turns_predicted": 0, "turns_no_next": 0}

    for i, p in enumerate(picks_all):
        seat = pick_order[i]
        snap = ps.build_snapshot(merger, players_db, eng_picks, pick_order, i, seat, league,
                                 pick_label=p.get("pick_label") or f"P{i + 1}",
                                 sleeper_projections=projections,
                                 sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
        cands = list(snap.candidates)

        # Resolve what this team was promised last time it picked.
        taken = {str(q["player_id"]) for q in eng_picks}
        promised = pending.pop(seat, None)
        if promised is not None:
            gap, gap_res, rows_, rookies_ = promised
            survived = 0
            for pid, predicted, rank in rows_:
                alive = pid not in taken
                survived += 1 if alive else 0
                pairs.append((predicted, alive, gap, rank))
            for pid, predicted, rank in rookies_:
                rookie_pairs.append((predicted, pid not in taken, gap, rank))
            turns.append({"index": i, "gap": gap, "gap_resolved": gap_res,
                          "candidates": len(rows_), "taken": len(rows_) - survived})

        # Record this turn's predictions, if this team picks again.
        nxt = ds.find_next_pick_index(pick_order, seat, i)
        if nxt is None:
            counts["turns_no_next"] += 1
        else:
            counts["turns_predicted"] += 1
            gap = nxt - i - 1
            gap_res = sum(1 for j in range(i + 1, nxt) if picks_all[j]["pick_no"] in resolved)
            fresh, rookies = [], []
            for rank, c in enumerate(cands):
                pr = c.survival_probability
                if pr is None:
                    counts["unmeasured"] += 1
                    continue
                if c.intervening_picks is not None and c.intervening_picks != gap:
                    raise RuntimeError(
                        f"turn {i} seat {seat}: engine intervening_picks={c.intervening_picks} "
                        f"but harness gap={gap} -- predictions would resolve against the wrong turn")
                pid = str(c.player_id)
                hit = _unresolved_hit(c.name, nxt)
                if hit is not None:
                    counts["unknowable"] += 1
                    if hit < i:
                        counts["ghost"] += 1
                    continue
                if (players_db.get(pid) or {}).get("years_exp") == 0:
                    counts["undraftable_rookie"] += 1
                    rookies.append((pid, pr, rank))
                    continue
                fresh.append((pid, pr, rank))
            pending[seat] = (gap, gap_res, fresh, rookies)

        # The REAL pick. Unresolved and placeholder turns add nothing -- counted up front.
        pid = resolved.get(p["pick_no"])
        if pid is not None:
            eng_picks.append({"pick_no": p["pick_no"], "round": p["round"], "roster_id": seat,
                              "player_id": pid,
                              "position": (players_db.get(pid) or {}).get("position")})
            # MY OWN PICK IS NOT A SURVIVAL FAILURE -- see simulate_and_collect.
            if seat in pending:
                gap, gap_res, fresh, rookies = pending[seat]
                kept = [r for r in fresh if r[0] != pid]
                counts["own_pick"] += len(fresh) - len(kept)
                pending[seat] = (gap, gap_res, kept, [r for r in rookies if r[0] != pid])

        if checkpoint is not None and ((i + 1) % REAL_CHECKPOINT_EVERY == 0 or i + 1 == len(picks_all)):
            checkpoint(pairs, rookie_pairs, turns, counts, i + 1)

    return pairs, rookie_pairs, turns, counts


def main_real():
    board = json.loads(REAL_BOARD.read_text())
    rules = json.loads(REAL_RULEBOOK.read_text())
    picks_all = sorted(board["picks"], key=lambda p: p["pick_no"])
    rounds = max(p["round"] for p in picks_all)

    # THE LEAGUE, SUPPLIED DIRECTLY -- the way draft_battery builds its captured-league arm and
    # the way main() above does. Never through build_mock_league: it overwrites `rec`, and
    # `rec` selects the rankings EXPORT (#248). observed_take_distribution.py predates that
    # rule and still uses the mock builder; it is not copied here.
    league = {
        "roster_positions": list(rules["roster_positions"]),
        "scoring_settings": {k: v["value"] for k, v in rules["scoring_settings_observed"].items()},
        "total_rosters": int(rules["total_rosters"]),
        "settings": {"type": 2},
        "draft_rounds": rounds,            # the draft that actually happened: 30 rounds
    }
    merger = dm.DataMerger()
    players_db, provenance = rdb.build_players_db_from_capture()
    projections = rdb.season_projections_from_capture()
    hint = db.league_format_hint(league)
    merger.set_league_format(hint)                                          # NEVER SKIP

    resolved, ambiguous, unmatched = otd.resolve_picks(picks_all, players_db)
    placeholders = sum(1 for p in picks_all if p.get("is_rookie_pick_placeholder"))
    illegible = [p["raw_player"] for p in picks_all
                 if p.get("illegible") and not p.get("is_rookie_pick_placeholder")]
    slot_team = {p["slot"]: p["team"] for p in picks_all}
    report = {
        "arm": "REAL", "league_rulebook": rules["league"], "rulebook_path": str(REAL_RULEBOOK),
        "board_path": str(REAL_BOARD), "universe_provenance": provenance,
        "teams": league["total_rosters"], "rounds": rounds, "league_format_hint": hint,
        "seat_identity": ("picked_by team, as its original slot number. 'My next selection' "
                          "belongs to the picker, not the slot; "
                          f"{sum(1 for p in picks_all if p['picked_by'] != p['team'])} of "
                          f"{len(picks_all)} picks were traded."),
        "seat_map": {str(s): t for s, t in sorted(slot_team.items())},
        "picks_total": len(picks_all), "picks_resolved": len(resolved),
        "picks_placeholder_rookie_assets": placeholders,
        "picks_unresolved": {"illegible": illegible, "unmatched": unmatched, "ambiguous": ambiguous,
                             "total": len(picks_all) - len(resolved) - placeholders},
        "resolver": "evidence/take_model/observed_take_distribution.resolve_picks",
        "source_state": _source_state(),
        "complete": False, "turns_done": 0, "LIMITS": LIMITS,
    }
    print(f"REAL arm: {rules['league']}  {len(picks_all)} turns, {len(resolved)} resolved, "
          f"{placeholders} placeholders, {report['picks_unresolved']['total']} unresolved  "
          f"hint={hint}  engine={report['source_state']}", flush=True)

    def checkpoint(pairs, rookie_pairs, turns, counts, done):
        # RAW FIRST, then derived (#215): the pairs are the expensive part.
        OUT_REAL_RAW.write_text(json.dumps({
            "arm": "REAL", "turns_done": done, "complete": done == len(picks_all),
            "pair_fields": ["predicted", "observed_survived", "intervening_picks",
                            "rank_among_narrowed_candidates"],
            "pairs": pairs, "undraftable_rookie_pairs": rookie_pairs, "turns": turns,
            "counts": counts}) + "\n")
        report["turns_done"] = done
        report["exclusions"] = counts
        assemble_scores(report, pairs, turns)
        report["sensitivity_including_undraftable_rookies"] = calibration(pairs + rookie_pairs)
        report["complete"] = done == len(picks_all)
        OUT_REAL.write_text(json.dumps(report, indent=2) + "\n")
        e = report["engine"]
        print(f"   checkpoint {done}/{len(picks_all)} turns  pairs={len(pairs)}  "
              f"brier={e['brier']} vs constant={report['control_constant_base_rate']['brier']}  "
              f"ceiling={'ok' if report['control_arithmetic_ceiling']['holds'] else 'VIOLATED'}  "
              f"excl={counts}", flush=True)

    pairs, rookie_pairs, turns, counts = real_collect(
        merger, players_db, league, picks_all, resolved, projections, checkpoint=checkpoint)
    if not report["complete"]:
        checkpoint(pairs, rookie_pairs, turns, counts, len(picks_all))
    _print_summary(report, f"REAL arm: {len(picks_all)} turns, {len(pairs)} pairs, "
                           f"exclusions {counts}")
    sens = report["sensitivity_including_undraftable_rookies"]
    print(f"  sensitivity, 2026 rookies included: n={sens['n']} base={sens['base_rate']} "
          f"brier={sens['brier']}")
    print(f"wrote {OUT_REAL} and {OUT_REAL_RAW}")
    return 0


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
              "policy_by_seat": policy_by_seat, "complete": False, "LIMITS": LIMITS}
    OUT.write_text(json.dumps(report, indent=2) + "\n")

    pairs, unmeasured, picks, turns = simulate_and_collect(
        merger, players_db, league, pick_order, policy_by_seat, projections)

    report["picks_simulated"] = len(picks)
    report["unmeasured_excluded"] = unmeasured
    assemble_scores(report, pairs, turns)
    report["complete"] = True
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    _print_summary(report, f"SMOKE arm: {len(picks)} picks, {len(pairs)} pairs, "
                           f"{unmeasured} unmeasured excluded\n  policies: {policy_by_seat}")
    print(f"wrote {OUT}")
    return 0


if __name__ == "__main__":
    arm = (sys.argv[1] if len(sys.argv) > 1 else "smoke").lower()
    if arm not in ("smoke", "real"):
        raise SystemExit(f"usage: calibrate.py [smoke|real]  (got {arm!r})")
    raise SystemExit(main_real() if arm == "real" else main())
