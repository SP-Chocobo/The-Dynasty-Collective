"""#216 -- the falsification battery for the degenerate-roster defect, written BLIND to any fix.

WHY THIS FILE EXISTS. Tests written beside a fix are shaped by it. This battery was written by an
adversary who had not seen the implementation and was forbidden to look, against the code as it
stood at f580c11, with every claim below MEASURED here rather than inherited from the item's
trace. Each test states what it detects, what it read on unfixed code, and how it was
mutation-checked. A test that passes on today's code is an OVER-CORRECTION GUARD and says so.

THE LOAD-BEARING TEST IS THE ABLATION (class A). Measured with my own instrument
(run_216_adversary_probe.py, real rulebook, engine at one seat via compute_draft_board, the
roster-proof control everywhere else):

    12T_ppr seat 1   backstop ON   RB 3  TE 8  WR 2  QB 1   legal, backstop OVERRODE 3 of 14 picks (r12-14)
    12T_ppr seat 1   backstop OFF  RB 3  TE 11              ZERO WR, ZERO QB -- illegal
    12T_ppr seat 6   backstop OFF  RB 3  TE 11              ZERO WR, ZERO QB -- illegal
    12T_ppr seat 12  backstop OFF  RB 9  TE 3  WR 1  QB 1   illegal (one WR slot)
    12T_ppr_SF seat 1 backstop OFF RB 3  TE 7  QB 4  WR 1   illegal (one WR slot)

The two receivers and the quarterback in every recorded #216 roster were NEVER the value
board's choice. They are feasibility_first (#154 tier 3) overriding the board in the last
rounds. Any test that measures a roster with the backstop ON is measuring the backstop, and a
fix could leave the value board exactly this broken and still pass it. So class A disables the
backstop and asks whether the value board ALONE drafts a legal roster, and then asks, with the
backstop ON, how often it had to intervene. The ON compositions here reproduce
evidence/roster_shape exactly, which is what licenses compute_draft_board's first row as the
engine's pick (the probe verified 6/6 agreement with build_snapshot's top candidate).

WHAT MY MEASUREMENTS SAY ABOUT THE HANDED-DOWN TRACE (pool-derived replacement gap widening;
need_bonus capped below it). Partly confirmed, and wrong in one important direction:
  - The TE/WR replacement gap at an empty board is 43.56 (1QB) / 52.4 (SF) -- confirmed.
  - It does NOT widen for the first two TEs I take (43.56 at k=0,1,2): starter_slot_counts gives
    TE 1 + 2/3 per team, so my first two picks reduce demand by exactly the rows they remove.
    It widens from the THIRD (53.6, 58.5, 64.8, 67.8 at k=3..6).
  - "need_bonus reads 0.00 and simply cannot matter" UNDERSTATES it. With the pool held
    IDENTICAL (three surplus TEs owned by me vs by a rival who already had his TE, 0 of 1114
    rows differ in universal_value), owning four tight ends gave the fifth a HIGHER acquisition
    value than owning one: 71.86 vs 68.81. depth_exposure prices insurance for the two TEs
    now sitting in my FLEX slots (+3.72, basis `measured`). The roster-aware sum is not merely
    too small; in 1QB it points the wrong way. In superflex it is +0.72 against a 63.6 bias.
  - The stack is a value-board fact independent of the widening: with the backstop off the
    board takes eleven TEs and never a WR or QB, and it does so in rounds where the gap has
    not yet widened at all.

Every measurement here: engine-measurement skill's fixture, from the repo root, set_league_format
before every board, populations printed in every failure message.
"""

from __future__ import annotations

import collections
import unittest
from pathlib import Path

import pandas as pd

import data_merger as dm
import draft_battery as db
import draft_room as dr
import draft_strategy as ds
import lineup_optimizer as lo
import run_draft_battery as rdb
import run_roster_proof as rp

CAPTURE = Path("data/fixtures/sleeper_capture.json")

_RULEBOOK: dict = {}


def _rulebook() -> dict:
    """The five-line fixture, built once per process (rule 1: from the repo root; rule 2: the
    real capture, never a hand-rolled loop)."""
    if not _RULEBOOK:
        merger = dm.DataMerger()
        players_db, universe = rdb.build_players_db_from_capture()
        _RULEBOOK.update(
            merger=merger, players_db=players_db, universe=universe,
            season=rdb.season_projections_from_capture(),
            scoring=rdb.scoring_settings_from_capture(),
            pools={},
        )
    return _RULEBOOK


def _league(superflex: bool) -> dict:
    rb = _rulebook()
    league = dr.build_mock_league(teams=12, superflex=superflex, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=rb["scoring"])
    rb["merger"].set_league_format(db.league_format_hint(league))     # rule 3, every time
    return league


def _board(league: dict, picks: list, me) -> list[dict]:
    rb = _rulebook()
    rb["merger"].set_league_format(db.league_format_hint(league))     # rule 3, every board
    return dr.compute_draft_board(
        rb["merger"], rb["players_db"], picks, me, league, mode="balanced",
        sleeper_projections=rb["season"], sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)


def _points(league: dict) -> dict[str, float]:
    """{player_id: projected_points} over the players both arms can price (rule 2 of the
    roster proof), cached per format."""
    rb = _rulebook()
    key = "SF" if "SUPER_FLEX" in league["roster_positions"] else "1QB"
    if key not in rb["pools"]:
        rb["merger"].set_league_format(db.league_format_hint(league))
        rb["pools"][key] = rp.scoreable_pool(rb["merger"], rb["players_db"], league, rb["season"])
    return rb["pools"][key]


def _pos(pid) -> str:
    return (_rulebook()["players_db"].get(str(pid)) or {}).get("position") or "?"


def _name(pid) -> str:
    info = _rulebook()["players_db"].get(str(pid)) or {}
    return " ".join(x for x in (info.get("first_name"), info.get("last_name")) if x) or str(pid)


def _ranked(points: dict, position: str) -> list[str]:
    return sorted((p for p in points if _pos(p) == position), key=lambda p: (-points[p], p))


def _priced(board: list[dict]) -> list[dict]:
    return [r for r in board if r.get("final_score") is not None]


def _levels(board: list[dict]) -> dict[str, tuple[float, float, int]]:
    """Implied replacement level per position = projected_points - bpa, as (min, max, n).
    min == max is the precondition every derivation below rests on: the level is a
    per-position constant, so a difference of levels is a difference of anchors, not of
    players."""
    by: dict[str, list[float]] = collections.defaultdict(list)
    for r in board:
        if r.get("bpa") is not None and r.get("projected_points") is not None:
            by[r["position"]].append(round(r["projected_points"] - r["bpa"], 3))
    return {p: (min(v), max(v), len(v)) for p, v in by.items()}


def _pick(player_id: str, roster_id: str, pick_no: int, round_no: int) -> dict:
    return {"pick_no": pick_no, "round": round_no, "roster_id": roster_id, "player_id": str(player_id)}


def _draft_my_seat(league: dict, seat: str, *, backstop_on: bool) -> dict:
    """One full draft, the engine at `seat`, run_roster_proof.control_pick everywhere else.

    ONE PROCESS, ONE CODE VERSION, ONE TOGGLE: `backstop_on=False` replaces feasibility_first
    with its own documented no-op (all 1s) for the duration, exactly the ablation idiom the
    engine-measurement skill prescribes, and restores it in `finally`.
    """
    rb = _rulebook()
    points, slots = _points(league), lo.slots_from_roster_positions(league["roster_positions"])
    seats = [str(i) for i in range(1, league["total_rosters"] + 1)]
    rounds = len(league["roster_positions"])
    order = ds.generate_pick_order(seats, rounds, "snake")
    real = dr.feasibility_first
    if not backstop_on:
        dr.feasibility_first = lambda scored, *a, **k: pd.Series(1, index=scored.index, dtype=int)
    try:
        picks, taken, mine, log = [], set(), collections.defaultdict(list), []
        for idx, who in enumerate(str(s) for s in order):
            rnd = idx // len(seats) + 1
            free = [p for p in points if p not in taken]
            if not free:
                break
            if who == seat:
                avail = [r for r in _board(league, picks, seat)
                         if str(r["player_id"]) in points and str(r["player_id"]) not in taken]
                chosen_row = avail[0]
                priced = _priced(avail)
                pure = min(priced, key=lambda r: (-r["final_score"], str(r["player_id"]))) if priced else None
                chosen = str(chosen_row["player_id"])
                log.append({
                    "round": rnd, "chosen": _name(chosen), "position": _pos(chosen),
                    "bound": bool(chosen_row.get("fills_required_slot")),
                    "overrode": pure is not None and str(pure["player_id"]) != chosen,
                    "pure_value_top": _name(pure["player_id"]) if pure else None,
                })
            else:
                chosen = rp.control_pick(free, points, mine[who], rb["players_db"], slots)
            taken.add(str(chosen))
            mine[who].append(str(chosen))
            picks.append(_pick(chosen, who, idx + 1, rnd))
    finally:
        dr.feasibility_first = real
    composition = dict(collections.Counter(_pos(p) for p in mine[seat]))
    dedicated = dr.dedicated_slot_counts(league["roster_positions"])
    return {
        "seat": seat, "backstop_on": backstop_on, "rounds": rounds, "pool": len(points),
        "composition": composition,
        "sequence": " ".join(f"{l['round']}:{l['position']}{'*' if l['overrode'] else ''}" for l in log),
        "missing_dedicated": {p: dedicated[p] - composition.get(p, 0)
                              for p in dedicated if dedicated[p] > composition.get(p, 0)},
        # THE SHIPPED OPTIMIZER decides fillability, not a second slot rule (#126).
        "unfillable_starting_slots": sorted(rp.unmet_slot_positions(mine[seat], rb["players_db"], slots)),
        "bound": sum(1 for l in log if l["bound"]),
        "overrode": sum(1 for l in log if l["overrode"]),
        "log": log,
    }


def _describe(run: dict) -> str:
    return (f"seat {run['seat']} backstop={'ON' if run['backstop_on'] else 'OFF'} "
            f"pool={run['pool']} rounds={run['rounds']} composition={run['composition']} "
            f"sequence={run['sequence']} missing_dedicated={run['missing_dedicated']} "
            f"unfillable={run['unfillable_starting_slots']} bound={run['bound']} overrode={run['overrode']}")


_DRAFTS: dict = {}


def _draft(superflex: bool, seat: str, backstop_on: bool) -> dict:
    key = (superflex, seat, backstop_on)
    if key not in _DRAFTS:
        _DRAFTS[key] = _draft_my_seat(_league(superflex), seat, backstop_on=backstop_on)
    return _DRAFTS[key]


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class A_TheValueBoardAloneMustDraftALegalRosterTests(unittest.TestCase):
    """THE PRIMARY FALSIFICATION. With feasibility_first disabled, the value board is the whole
    engine. It must fill every named starting slot and a full starting lineup on its own; the
    backstop is a safety net, not the thing carrying legality.

    Measured on f580c11 (see module docstring): FAILS -- seat 1 and seat 6 finish with eleven
    tight ends and neither a receiver nor a quarterback in a league that starts one QB and two WR.
    """

    def test_1QB_seat_1_without_the_backstop_every_dedicated_starting_slot_is_filled(self):
        run = _draft(False, "1", backstop_on=False)
        self.assertEqual(run["missing_dedicated"], {}, _describe(run))

    def test_1QB_seat_1_without_the_backstop_a_full_starting_lineup_is_fillable(self):
        run = _draft(False, "1", backstop_on=False)
        self.assertEqual(run["unfillable_starting_slots"], [], _describe(run))

    def test_1QB_seat_12_without_the_backstop_is_legal(self):
        # A late seat, so the finding cannot be read as "this draft slot does this".
        run = _draft(False, "12", backstop_on=False)
        self.assertEqual((run["missing_dedicated"], run["unfillable_starting_slots"]), ({}, []),
                         _describe(run))

    def test_superflex_seat_1_without_the_backstop_is_legal(self):
        run = _draft(True, "1", backstop_on=False)
        self.assertEqual((run["missing_dedicated"], run["unfillable_starting_slots"]), ({}, []),
                         _describe(run))

    def test_the_ablation_actually_fired(self):
        """Non-vacuity. With the backstop replaced, no chosen row may carry
        fills_required_slot -- if one does, the patch did not reach the board and the OFF arm
        is the ON arm wearing a different label."""
        for sf, seat in ((False, "1"), (False, "12"), (True, "1")):
            run = _draft(sf, seat, backstop_on=False)
            self.assertEqual(run["bound"], 0, _describe(run))
            self.assertGreater(len(run["log"]), 10, "the engine made too few picks to measure")

    def test_with_the_backstop_on_it_never_has_to_override_the_value_board(self):
        """A backstop that fires is a value board that failed. Counted, not snapshotted: each
        of my picks where the row taken is not the pure team_acquisition_value argmax.

        Measured on f580c11: FAILS -- 3 of 14 picks overridden in seat 1 (rounds 12, 13, 14:
        WR, WR, QB), 3 in seat 6, 1 in seat 12, 1 in superflex seat 1."""
        run = _draft(False, "1", backstop_on=True)
        self.assertEqual(run["overrode"], 0, _describe(run))

    def test_the_backstop_arm_is_legal_which_is_what_makes_the_off_arm_the_engine(self):
        """Control for the class: the ON arm is legal today. If it ever is not, #154's backstop
        has regressed and the OFF-arm findings are about something else."""
        run = _draft(False, "1", backstop_on=True)
        self.assertEqual((run["missing_dedicated"], run["unfillable_starting_slots"]), ({}, []),
                         _describe(run))


def _ab_states(league: dict) -> tuple[list, list, list[str]]:
    """The pool-identical pair. Both states: I ("1") own TE#1 and rival "2" owns TE#5 (so his
    TE slot is already filled and his later TEs move no demand). Then TE#2, #3, #4 go to the
    rival (state A: I own ONE) or to me (state B: I own FOUR). Same rows leave the pool, the
    league's remaining starter demand is identical, so every row's universal_value must be
    identical -- asserted, not assumed -- and the only thing that differs is my roster."""
    te = _ranked(_points(league), "TE")
    base = [_pick(te[0], "1", 1, 1), _pick(te[4], "2", 2, 1)]
    a = base + [_pick(p, "2", 3 + i, 2) for i, p in enumerate(te[1:4])]
    b = base + [_pick(p, "1", 3 + i, 2) for i, p in enumerate(te[1:4])]
    return a, b, te


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class B_FeedbackDirectionTests(unittest.TestCase):
    """THE MECHANISM. Does owning more of a position make the next one look better or worse
    to THIS roster? A fix that flattens a level without reversing this direction has not fixed
    the stack; the stack is what this direction produces when iterated fourteen times."""

    def _ab(self, superflex: bool):
        league = _league(superflex)
        a, b, te = _ab_states(league)
        ba = {str(r["player_id"]): r for r in _board(league, a, "1")}
        bb = {str(r["player_id"]): r for r in _board(league, b, "1")}
        differing = [pid for pid in ba if ba[pid].get("universal_value") != bb[pid].get("universal_value")]
        self.assertGreater(len(ba), 500, "board too small to be the real pool")
        self.assertEqual(differing, [], f"{len(differing)} of {len(ba)} rows changed universal_value "
                                        "between the two states -- the pool is not identical and "
                                        "nothing below isolates the roster")
        return league, ba[te[5]], bb[te[5]], ba, bb

    def test_1QB_owning_four_tight_ends_makes_the_fifth_worth_LESS_to_me_than_owning_one(self):
        """Measured on f580c11: FAILS. Next TE (Sam LaPorta, 230.85 proj): state A final 68.81
        (need 0.67), state B final 71.86 (need 0.00, depth_exposure +3.72 `measured`)."""
        _, ra, rb_, ba, bb = self._ab(False)
        self.assertLess(
            rb_["final_score"], ra["final_score"],
            f"{ra['name']}: own-one final {ra['final_score']} (need {ra['need_bonus']}, depth "
            f"{ra.get('depth_exposure')}/{ra.get('depth_basis')}) vs own-four final "
            f"{rb_['final_score']} (need {rb_['need_bonus']}, depth {rb_.get('depth_exposure')}/"
            f"{rb_.get('depth_basis')}); universal_value identical at {ra['universal_value']} "
            f"over {len(ba)} rows")

    def test_superflex_owning_four_tight_ends_makes_the_fifth_worth_less_to_me_than_owning_one(self):
        """Measured on f580c11: PASSES, by 0.72 -- the flex-share need that drops off. Kept as
        the superflex half of the direction test; C's magnitude test is what fails there."""
        _, ra, rb_, ba, bb = self._ab(True)
        self.assertLess(rb_["final_score"], ra["final_score"],
                        f"{ra['name']}: own-one {ra['final_score']} vs own-four {rb_['final_score']}")

    def test_the_same_tight_end_is_not_worth_more_to_me_after_i_hoard_six(self):
        """A FIXED player across two of my roster states, no rival picks: TE#7 by projection
        (Travis Kelce) with my roster empty, and with my roster holding TE#1..#6. The pool
        differs (six TEs gone), so his universal_value legitimately moves with the league's
        scarcity; what may not happen is that his value TO ME rises because I already own six
        of him.

        Measured on f580c11: FAILS. Empty roster: uv 44.27, need 4.67, final 48.94. Six tight
        ends owned: uv 68.48, need 0.00, depth +3.72, final 72.20 -- twenty-three points MORE,
        and the room shows that number."""
        league = _league(False)
        te = _ranked(_points(league), "TE")
        empty = {str(r["player_id"]): r for r in _board(league, [], "1")}[te[6]]
        six = {str(r["player_id"]): r for r in _board(
            league, [_pick(te[i], "1", i + 1, i + 1) for i in range(6)], "1")}[te[6]]
        self.assertLessEqual(
            six["final_score"], empty["final_score"],
            f"{empty['name']}: empty roster uv {empty['universal_value']} need {empty['need_bonus']} "
            f"final {empty['final_score']}; owning six TEs uv {six['universal_value']} need "
            f"{six['need_bonus']} depth {six.get('depth_exposure')} final {six['final_score']}")


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class C_MagnitudeTests(unittest.TestCase):
    """Can the roster-aware terms actually reorder the board? Measured as the roster-term
    SEPARATION the engine puts between a benched tight end and a same-projection receiver at
    an empty named slot, against the positional bias the tight end is handed for free.

    THE BIAS IS DERIVED (#56), not chosen: a surplus TE cannot start at TE; the best he can do
    for this roster is FLEX, where the freely available replacement is the best flex-eligible
    replacement-rank player -- WR's level on this pool (216 vs RB 186 vs TE 173). So a surplus
    TE is over-credited, relative to a same-projection WR, by level_WR - level_TE, read off the
    rows themselves (projected_points - bpa, asserted constant within a position). The roster
    terms overcome that only if (lift_WR - lift_TE) reaches it, where lift = final_score -
    universal_value -- whichever side a fix works from (lifting the receiver, depressing the
    surplus, re-anchoring the surplus row). A cap on the terms below the bias is unfixable by
    definition, and this is the measurement of that.

    Measured on f580c11: FAILS. 1QB separation 4.95 (8.67 - 3.72) against a 58.47 bias;
    superflex 9.44 against 63.61. (An earlier draft measured only the tight end's own swing
    between owning one and four and failed under a stand-in fix that lifts the receiver instead
    -- over-specified to one side; this form is not.) A fix that reorders by sort key alone and
    leaves these numbers would still fail here, on purpose: the room would then display 71.86
    above 20.98 while ranking them the other way round, which is the display contract broken.
    """

    def _separation_and_bias(self, superflex: bool):
        league = _league(superflex)
        _, b, te = _ab_states(league)
        rows = _priced(_board(league, b, "1"))
        levels = _levels(rows)
        for p in ("TE", "WR"):
            lo_, hi_, n = levels[p]
            self.assertEqual(lo_, hi_, f"{p} level is not a per-position constant ({lo_}..{hi_} over {n})")
        bias = levels["WR"][0] - levels["TE"][0]
        self.assertGreater(bias, 0, f"WR level {levels['WR']} is not above TE level {levels['TE']}")
        te_row = next(r for r in rows if str(r["player_id"]) == te[5])
        wr_row = min((r for r in rows if r["position"] == "WR"),
                     key=lambda r: abs(r["projected_points"] - te_row["projected_points"]))
        self.assertLessEqual(abs(wr_row["projected_points"] - te_row["projected_points"]), 5.0,
                             "no receiver projects within five points of the benched tight end")
        lift = lambda r: r["final_score"] - r["universal_value"]
        return te_row, wr_row, lift(wr_row) - lift(te_row), bias, levels

    def _assert_reaches(self, superflex: bool):
        te_row, wr_row, separation, bias, levels = self._separation_and_bias(superflex)
        self.assertGreaterEqual(
            separation, bias,
            f"{te_row['name']} TE proj {te_row['projected_points']} uv {te_row['universal_value']} "
            f"final {te_row['final_score']} vs {wr_row['name']} WR proj {wr_row['projected_points']} "
            f"uv {wr_row['universal_value']} final {wr_row['final_score']}: roster-term separation "
            f"{separation:.2f} against bias level_WR - level_TE = {bias:.2f}; levels {levels}")

    def test_1QB_the_roster_terms_can_span_the_positional_bias(self):
        self._assert_reaches(False)

    def test_superflex_the_roster_terms_can_span_the_positional_bias(self):
        self._assert_reaches(True)


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class D_SamePointsPairTests(unittest.TestCase):
    """The user-facing shape of the defect. I own four tight ends and no receiver; a receiver
    and a tight end project within two season points of each other. The receiver fills an
    empty named slot; the tight end sits on my bench. The receiver must out-rank him.

    Measured on f580c11: FAILS on all six pairs found -- e.g. Sam LaPorta TE 230.85 -> 71.86
    over Davante Adams WR 230.50 -> 20.98; Harold Fannin TE 201.2 -> 45.84 over Brian Thomas WR
    201.6 -> -8.14."""

    def test_1QB_a_receiver_at_an_empty_slot_outranks_a_benched_tight_end_of_equal_projection(self):
        league = _league(False)
        _, b, _ = _ab_states(league)
        priced = _priced(_board(league, b, "1"))
        pairs = []
        for te in (r for r in priced if r["position"] == "TE"):
            wr = next((w for w in priced if w["position"] == "WR"
                       and abs(w["projected_points"] - te["projected_points"]) <= 2.0), None)
            if wr is not None:
                pairs.append((te, wr))
            if len(pairs) >= 6:
                break
        self.assertGreaterEqual(len(pairs), 3, "too few equal-projection TE/WR pairs on this pool")
        losses = [f"{te['name']} TE {te['projected_points']} -> {te['final_score']} outranks "
                  f"{wr['name']} WR {wr['projected_points']} -> {wr['final_score']}"
                  for te, wr in pairs if not wr["final_score"] > te["final_score"]]
        self.assertEqual(losses, [], f"{len(losses)} of {len(pairs)} pairs: " + "; ".join(losses))


def _startable_positions(league: dict, my_ids: list[str]) -> set[str]:
    """Positions that would still fill an uncovered STARTING slot on my roster, decided by the
    shipped optimizer (run_roster_proof.unmet_slot_positions), never a second slot rule."""
    return rp.unmet_slot_positions(my_ids, _rulebook()["players_db"],
                                   lo.slots_from_roster_positions(league["roster_positions"]))


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class E_OverCorrectionGuards(unittest.TestCase):
    """PASS on today's code, and must still pass on a fix. An engine that refuses a second tight
    end, drafts strictly to slot counts, penalises a player who can still start, or collapses
    into the projection control has replaced one defect with another. The implementer is the
    person least likely to write these against their own fix, so they are written here.

    Each was mutation-checked by breaking the engine in the over-corrected direction (see
    MUTATIONS at the bottom of the file)."""

    def test_roster_context_never_subtracts_from_a_player_who_fills_an_open_starting_slot(self):
        """I own four TEs and nothing else. QB, RB and WR all fill uncovered starting slots;
        no roster term may take value AWAY from those rows. Surplus is a property of the
        position I am stacked at, not of the positions I am empty at."""
        league = _league(False)
        _, b, _ = _ab_states(league)
        mine = [p["player_id"] for p in b if p["roster_id"] == "1"]
        startable = _startable_positions(league, mine)
        self.assertTrue({"QB", "RB", "WR"} <= startable, f"fixture: startable={startable}")
        rows = [r for r in _priced(_board(league, b, "1")) if r["position"] in startable]
        penalised = [f"{r['name']} {r['position']} uv {r['universal_value']} final {r['final_score']}"
                     for r in rows if r["final_score"] < r["universal_value"] - 1e-9]
        self.assertGreater(len(rows), 100, "population too small")
        self.assertEqual(penalised, [], f"{len(penalised)} of {len(rows)} startable rows penalised: "
                                        + "; ".join(penalised[:5]))

    # ------------------------------------------------------------------------------------
    # RULING (#221): the two guards below were PRE-REGISTERED WITH A RULER THAT IS THE DEFECT.
    #
    # Both ranked candidates by `universal_value` across positions and required the board's
    # order to agree. `universal_value` contains `bpa` -- each player's surplus over HIS OWN
    # position's replacement level -- so it is not commensurable between positions (#211/#155,
    # and #216's own reason for existing). The five pairs the first version named as violations
    # settle it, measured on the real capture with one tight end owned (Bowers) and a FLEX open:
    #
    #   Trey McBride     TE  projects 300.85   reaches FLEX only        alternative 216.25
    #   CeeDee Lamb      WR  projects 327.93   reaches an open WR slot  alternative 216.25
    #   Nico Collins     WR  projects 325.61   open WR                  alternative 216.25
    #   Justin Jefferson WR  projects 315.69   open WR                  alternative 216.25
    #   Jeremiyah Love   RB  projects 288.47   open RB                  alternative 185.64
    #   Kenneth Walker   RB  projects 283.51   open RB                  alternative 185.64
    #
    # Three of the five simply OUTPROJECT McBride by 15-27 points. The other two project LESS
    # and are still worth more to this roster, because they fill an open DEDICATED slot whose
    # free alternative is 30 points cheaper than the flex McBride would take. The board is right
    # on all five, and the guard's ordering was the tight-end bias restated as a criterion.
    #
    # WHAT REPLACES IT, and what it can and cannot falsify. The quantity these guards need --
    # what a player adds over what his slot would get free -- IS the quantity under test, so no
    # fully independent re-derivation exists; a test that re-implemented it would be a second
    # home for the vocabulary (#126). Two things are still worth pinning and are pinned below:
    # that the BOARD applies the term faithfully (no double application, no cap, no sign error,
    # no extra positional penalty on top), and the fully independent within-position ordering,
    # which is where "refuses a second tight end" would actually show up.
    #
    # marginal_lineup_value was considered as the ruler and REJECTED: with a near-empty roster
    # it reduces to raw projection, which is precisely the projection control that
    # test_the_board_is_not_the_projection_control below exists to reject.
    # ------------------------------------------------------------------------------------

    def _surplus(self, league, picks, board):
        """Projection minus the free alternative at the cheapest slot each position can still
        reach on THIS roster -- one call into the shipped term, never a reimplementation."""
        levels = {}
        for r in board:
            if r.get("bpa") is not None and r.get("projected_points") is not None:
                levels.setdefault(r["position"], round(r["projected_points"] - r["bpa"], 4))
        rpos = league["roster_positions"]
        alts = dr.shared_slot_alternatives(levels, rpos)
        pdb = _rulebook()["players_db"]
        by_id = {str(r["player_id"]): r for r in board}
        roster = [{"id": str(p["player_id"]), "value": float(by_id[str(p["player_id"])]["projected_points"]),
                   "eligible": {by_id[str(p["player_id"])]["position"]}}
                  for p in picks if str(p["roster_id"]) == "1" and str(p["player_id"]) in by_id]
        if not roster:
            # A drafted player is off the board, so his projection comes from the pool both arms
            # can price -- the same source _points uses everywhere else in this file.
            pool = _points(league)
            roster = [{"id": str(p["player_id"]), "value": float(pool[str(p["player_id"])]),
                       "eligible": {dr.player_position(pdb[str(p["player_id"])])}}
                      for p in picks if str(p["roster_id"]) == "1"
                      and str(p["player_id"]) in pool]
        displaced = {}
        for pos, level in levels.items():
            d = lo.displacement_level(roster, rpos, pos, level, slot_alternatives=alts)
            displaced[pos] = d["displaced"]
        return {str(r["player_id"]): r["projected_points"] - displaced[r["position"]]
                for r in board if r["position"] in displaced}

    def test_a_startable_player_outranks_anyone_who_adds_less_at_the_slot_he_can_reach(self):
        """The replacement for the universal_value ordering, on the corrected ruler: what a
        player adds over what the cheapest slot he can still reach would get for free.

        This falsifies a board that applies the anchor correction twice, caps it, gets its sign
        wrong, or adds a positional penalty on top of it -- every one of which would break the
        agreement between the board's order and the term the board says it is applying. It
        cannot falsify the choice of alternative itself; that was settled by measurement
        (evidence/roster_shape/shared_slot/), not here."""
        league = _league(False)
        te = _ranked(_points(league), "TE")
        picks = [_pick(te[0], "1", 1, 1)]
        startable = _startable_positions(league, [te[0]])
        self.assertIn("TE", startable, f"fixture: FLEX should leave TE startable; got {startable}")
        board = _priced(_board(league, picks, "1"))
        surplus = self._surplus(league, picks, board)
        index = {str(r["player_id"]): i for i, r in enumerate(board)}
        priced = sorted(board, key=lambda r: -r["universal_value"])[:150]
        pairs = violations = 0
        examples = []
        for i in (r for r in priced if r["position"] in startable):
            si = surplus.get(str(i["player_id"]))
            if si is None:
                continue
            for j in priced:
                sj = surplus.get(str(j["player_id"]))
                # Guarded only where the surplus gap exceeds every OTHER term's whole reach, so
                # a legitimate need_bonus or depth_exposure reordering is not counted a defect.
                if sj is None or si - sj <= dr.NEED_BONUS_MAX + dr.DEPTH_EXPOSURE_MAX:
                    continue
                pairs += 1
                if index[str(i["player_id"])] > index[str(j["player_id"])]:
                    violations += 1
                    if len(examples) < 5:
                        examples.append(f"{i['name']} {i['position']} surplus {si:.1f} "
                                        f"below {j['name']} {j['position']} surplus {sj:.1f}")
        self.assertGreater(pairs, 100, f"only {pairs} guarded pairs -- fixture too flat")
        self.assertEqual(violations, 0, f"{violations} of {pairs} pairs inverted: " + "; ".join(examples))

    def test_every_ROSTER_term_is_identical_for_two_players_at_the_same_position(self):
        """FULLY INDEPENDENT of everything above, and the place a refusal would really show.

        need_bonus, depth_exposure and displacement_adj are per-POSITION by construction: they
        read my roster and the league's slots, and the candidate does not enter them at all. So
        their SUM must be one number per position, identical for the tight end who would start
        and the tight end who would sit. An engine that "drafts strictly to slot counts" --
        refusing a second tight end because one TE slot is filled -- has to break this to do it.

        Deliberately NOT "the board's order matches projection order within a position": that is
        false and should be, because risk_adj, the time horizon and the growth signal are
        per-PLAYER and legitimately reorder same-position rows (measured: Jaxson Dart 329.01
        ranks below Patrick Mahomes 328.6). Asserting it would have pinned a claim this engine
        does not make. eligibility_bonus is likewise excluded -- it is the one roster term that
        is per-CANDIDATE, since it prices a multi-position player's extra reach."""
        league = _league(False)
        te = _ranked(_points(league), "TE")
        board = _priced(_board(league, [_pick(te[0], "1", 1, 1)], "1"))
        checked = 0
        for position in ("QB", "RB", "WR", "TE"):
            rows = [r for r in board if r["position"] == position]
            self.assertGreater(len(rows), 5, f"too few {position} rows")
            sums = {round((r.get("need_bonus") or 0.0) + (r.get("depth_exposure") or 0.0)
                          + (r.get("displacement_adj") or 0.0), 6) for r in rows}
            checked += len(rows)
            self.assertEqual(len(sums), 1,
                             f"{position}: roster terms differ between same-position rows: {sorted(sums)}")
        self.assertGreater(checked, 200, "population too small")

    def test_a_second_tight_end_is_still_taken_when_he_is_the_best_value_left(self):
        """The refusal case, still stated on one player, on the corrected ruler. With Bowers
        owned and a FLEX open, Trey McBride's rank must not exceed the count of players who
        actually add MORE than he does at the slot each can reach."""
        league = _league(False)
        te = _ranked(_points(league), "TE")
        picks = [_pick(te[0], "1", 1, 1)]
        board = _priced(_board(league, picks, "1"))
        surplus = self._surplus(league, picks, board)
        mcbride = next(r for r in board if str(r["player_id"]) == te[1])
        mine = surplus[str(mcbride["player_id"])]
        # Contenders: everyone who adds more than he does, plus everyone within the ROSTER
        # terms' whole reach of him -- the same bound the pair guard above uses, taken from the
        # engine's own constants rather than chosen to fit. The slack is needed and is not a
        # fudge: risk_adj, the time horizon and the growth signal are per-PLAYER and legitimately
        # move a row a place or two (measured here, Chris Olave adds 82.1 against McBride's 84.6
        # and sits two rows above him). Without the slack this would pin per-player noise as if
        # it were the refusal the test is looking for.
        reach = dr.NEED_BONUS_MAX + dr.DEPTH_EXPOSURE_MAX
        contenders = [r for r in board if str(r["player_id"]) != te[1]
                      and surplus.get(str(r["player_id"]), float("-inf")) > mine - reach]
        rank = board.index(mcbride)
        self.assertGreater(mine, 0.0, f"{mcbride['name']} must still be worth starting: {mine}")
        self.assertLessEqual(rank, len(contenders),
                             f"{mcbride['name']} projects {mcbride['projected_points']}, surplus "
                             f"{mine:.1f}, ranked {rank}; only {len(contenders)} players are within "
                             f"the roster terms' reach of him")

    def test_the_board_is_not_the_projection_control(self):
        """A fix that flattens replacement toward zero turns the board into "best projected
        points" -- the control this repo already measured taking 24 consecutive quarterbacks.
        The derived form: in a one-QB league a quarterback priced BELOW his replacement level
        (bpa < 0) who nonetheless out-projects the best receiver must rank below that receiver.
        The projection control takes him first; the engine must not. (An earlier draft of this
        test assumed the projection argmax is a QB; under the real PPR rulebook it is Christian
        McCaffrey, so the precondition is stated on the QB tail instead.)"""
        # (Second draft: under this PPR rulebook the top receiver projects 395, above every
        # below-replacement QB, so that form was vacuous too. The control's SIGNATURE is that
        # its order never disagrees with projection order. So: there must exist QB/WR pairs
        # where the QB out-projects the WR by more than horizon + risk could ever move a row
        # and the board still prices the WR higher, and on those pairs the WR must rank first.)
        league = _league(False)
        priced = _priced(_board(league, [], "1"))[:200]
        index = {str(r["player_id"]): i for i, r in enumerate(priced)}
        margin = (dr.TIME_HORIZON_CLAMP[1] - dr.TIME_HORIZON_CLAMP[0]) + max(abs(v) for v in dr.RISK_ADJ.values())
        qbs = [r for r in priced if r["position"] == "QB"]
        wrs = [r for r in priced if r["position"] == "WR"]
        pairs = [(q, w) for q in qbs for w in wrs
                 if q["projected_points"] - w["projected_points"] > margin
                 and q["universal_value"] < w["universal_value"]]
        self.assertGreater(len(pairs), 5, f"the board never disagrees with projection order "
                                          f"(margin {margin}): it IS the projection control; "
                                          f"{len(qbs)} QB x {len(wrs)} WR rows examined")
        inverted = [f"{q['name']} proj {q['projected_points']} uv {q['universal_value']} above "
                    f"{w['name']} proj {w['projected_points']} uv {w['universal_value']}"
                    for q, w in pairs if index[str(q["player_id"])] < index[str(w["player_id"])]
                    and w["universal_value"] - q["universal_value"] > q["final_score"] - q["universal_value"]]
        self.assertEqual(inverted, [], f"{len(inverted)} of {len(pairs)} pairs follow projection, not value: {inverted[:3]}")

    def test_an_elite_still_leads_when_his_positions_named_slots_are_filled_but_flex_is_open(self):
        """I own RB#10 and RB#11 by projection -- both named RB slots filled, FLEX open. The
        board's best RB by universal_value must still be first when his talent gap over the best
        non-RB exceeds that row's whole roster lift. On f580c11 that is Jahmyr Gibbs."""
        league = _league(False)
        rbs = _ranked(_points(league), "RB")
        picks = [_pick(rbs[9], "1", 1, 1), _pick(rbs[10], "1", 2, 2)]
        priced = _priced(_board(league, picks, "1"))
        elite = max((r for r in priced if r["position"] == "RB"), key=lambda r: r["universal_value"])
        rival = max((r for r in priced if r["position"] != "RB"), key=lambda r: r["final_score"])
        lift = rival["final_score"] - rival["universal_value"]
        self.assertGreater(elite["universal_value"] - rival["universal_value"], lift,
                           f"precondition: {elite['name']} uv {elite['universal_value']} vs "
                           f"{rival['name']} uv {rival['universal_value']} lift {lift:.2f}")
        self.assertEqual(priced[0]["player_id"], elite["player_id"],
                         f"board top is {priced[0]['name']} {priced[0]['position']} {priced[0]['final_score']}, "
                         f"not {elite['name']} {elite['final_score']}")

    def test_with_every_starter_filled_talent_still_orders_the_board(self):
        """Eight mid-tier starters owned (QB#10, RB#15/#16, WR#20/#21, TE#8, RB#17 and WR#22 at
        FLEX). The uv argmax on the board must lead whenever his talent gap over every other row
        exceeds that row's lift -- a fix that hands out counts-based credit once slots are full
        would reorder this on something other than talent."""
        league = _league(False)
        pts = _points(league)
        q, r_, w, t = (_ranked(pts, p) for p in ("QB", "RB", "WR", "TE"))
        mine = [q[9], r_[14], r_[15], w[19], w[20], t[7], r_[16], w[21]]
        self.assertEqual(_startable_positions(league, mine), set(), "fixture: a starting slot is still open")
        picks = [_pick(p, "1", i + 1, i + 1) for i, p in enumerate(mine)]
        priced = _priced(_board(league, picks, "1"))
        best = max(priced, key=lambda r: r["universal_value"])
        blockers = [r for r in priced if r is not best
                    and best["universal_value"] - r["universal_value"] <= r["final_score"] - r["universal_value"]]
        self.assertEqual(blockers, [], "precondition: some row's lift covers the talent gap: "
                                       + "; ".join(f"{r['name']} lift {r['final_score'] - r['universal_value']:.2f}" for r in blockers[:3]))
        self.assertEqual(priced[0]["player_id"], best["player_id"],
                         f"top is {priced[0]['name']} {priced[0]['final_score']}, uv argmax is {best['name']} {best['universal_value']}")


# MEASURED STATUS ON UNFIXED CODE (f580c11) and MUTATION RESULTS -- filled in by the adversary
# after running this file; see the bottom of the file in the committed version.
if __name__ == "__main__":
    unittest.main()
