"""#216 -- the fix: the displacement term, its derivation, its wiring and the reviewer's
invariants that the adversary's battery does not itself pin (2, 4 and 6).

The term (lineup_optimizer.displacement_level -> draft_room.displacement_adjustments ->
displacement_adj in team_acquisition_value) is derived, not tuned: replacement level minus what
a player at that position must displace in MY optimal lineup, with every open slot's free
alternative set to the league replacement level the board already computes. The tests below
assert what the derivation implies -- exact reduction to the league anchor wherever a reachable
slot is open, a deduction of exactly the surplus where none is, non-positivity everywhere, a
per-position constant at a board state, no numeric constant in the value path -- and the three
reviewer invariants on the real rulebook.

MUTATION RESULTS are recorded at the bottom of this file after each mutation was applied by
hand, the test run, and the file restored byte-identical (POST_AUDIT_PLAN #215's three rules).
"""
from __future__ import annotations

import ast
import inspect
import unittest
from pathlib import Path
from unittest import mock

import pandas as pd

import draft_room as dr
import lineup_optimizer as lo

CAPTURE = Path("data/fixtures/sleeper_capture.json")
ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 6

#: #52 phase 6 (W1-01). A rulebook with IDP slots, because the sign of this term depends on a
#: slot the candidate's SECOND eligibility can reach and ROSTER above has none -- which is
#: exactly why "never positive" was pinned for so long over a population that cannot break it.
IDP_ROSTER = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
              "DL", "LB", "DB", "IDP_FLEX"] + ["BN"] * 6
#: Replacement levels the board would compute. Written out so every number below is checkable
#: by hand against shared_slot_alternatives' own rule (a slot is worth max(level) over what it
#: admits): DB_9 -> 104, IDP_FLEX_10 -> max(DL, LB, DB) = 131, FLEX_6 -> max(RB, WR, TE) = 216.
LEVELS = {"QB": 290.0, "RB": 186.0, "WR": 216.0, "TE": 173.0,
          "DL": 118.0, "LB": 131.0, "DB": 104.0}


def _p(pid, value, *positions):
    return {"id": pid, "value": float(value), "eligible": set(positions)}


class DisplacementLevelDerivationTests(unittest.TestCase):
    """The primitive, on hand-built rosters where every number can be checked by hand."""

    def test_an_empty_roster_reduces_exactly_to_the_league_anchor(self):
        out = lo.displacement_level([], ROSTER, "TE", 173.0)
        self.assertEqual((out["displaced"], out["adjustment"], out["basis"]), (173.0, 0.0, lo.DISPLACEMENT_MEASURED))

    def test_an_open_reachable_slot_means_no_deduction_even_with_a_better_starter_held(self):
        # TE slot held by a 300 -- but FLEX is open, so a second TE is priced against the
        # league anchor, not against the 300. This is the over-correction guard's own case
        # (McBride with Bowers owned) stated on the primitive.
        out = lo.displacement_level([_p("te1", 300, "TE")], ROSTER, "TE", 173.0)
        self.assertEqual((out["displaced"], out["adjustment"]), (173.0, 0.0))

    def test_every_reachable_slot_held_above_the_anchor_deducts_exactly_the_weakest_holder(self):
        four = [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE"), _p("t4", 200, "TE")]
        out = lo.displacement_level(four, ROSTER, "TE", 173.0)
        # TE, FLEX, FLEX hold 300/250/220; the fourth (200) is benched and is NOT the answer.
        self.assertEqual((out["displaced"], out["adjustment"]), (220.0, -47.0))
        # ...and the same roster deducts nothing from a receiver: every WR slot is open.
        self.assertEqual(lo.displacement_level(four, ROSTER, "WR", 216.0)["adjustment"], 0.0)

    def test_a_holder_below_the_anchor_is_not_an_occupant(self):
        # A 150 receiver does not hold a slot against a free 216: the phantom takes it, so a
        # candidate WR is priced against the league anchor and never LIFTED for my weak starter.
        out = lo.displacement_level([_p("w", 150, "WR")], ROSTER, "WR", 216.0)
        self.assertEqual((out["displaced"], out["adjustment"]), (216.0, 0.0))

    # THIS TEST WAS CALLED test_the_adjustment_is_never_positive AND IT WAS WRONG (#52 phase 6,
    # W1-01). Not wrong in what it asserted -- every case it ran really is non-positive -- but
    # wrong in what it was taken to prove. Every case passed NO `slot_alternatives` and a
    # SINGLE-position probe, and the term can only go positive with both: a multi-eligible probe
    # reaching a per-slot alternative priced below his own anchor. So it pinned "never positive"
    # over precisely the population in which that cannot fail, while the shipped engine ran a
    # population in which it does (Travis Hunter, +79.44). The claim is now split in two, and
    # each half is exercised where it actually lives.

    def test_a_single_position_candidate_is_never_lifted(self):
        # Half one, and it holds for a reason rather than by observation: shared_slot_alternatives
        # prices a slot at max(level) over the positions it ADMITS, so every slot a one-position
        # probe can reach is priced at or above his own anchor. Run WITH slot_alternatives and on
        # the IDP rulebook as well -- the two things the old version left out.
        rosters = [
            [], [_p("w", 150, "WR")], [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")],
            [_p("q", 400, "QB"), _p("r1", 260, "RB"), _p("r2", 240, "RB"), _p("w1", 250, "WR"),
             _p("w2", 240, "WR"), _p("t", 230, "TE"), _p("f1", 235, "RB"), _p("f2", 233, "WR")],
        ]
        seen = 0
        for rpos in (ROSTER, IDP_ROSTER):
            alts = dr.shared_slot_alternatives(LEVELS, rpos)
            for roster in rosters:
                for position, level in LEVELS.items():
                    for supplied in (None, alts):
                        with self.subTest(rulebook=len(rpos), roster=len(roster),
                                          position=position, per_slot=supplied is not None):
                            out = lo.displacement_level(roster, rpos, position, level,
                                                        slot_alternatives=supplied)
                            if out["basis"] == lo.DISPLACEMENT_NOT_APPLICABLE:
                                continue          # no reachable slot; nothing to claim
                            seen += 1
                            self.assertLessEqual(out["adjustment"], 0.0)
                            self.assertGreaterEqual(out["displaced"], level)
        # Exactly, not "enough": 2 rulebooks x 4 rosters x 7 positions x 2 (with and without
        # per-slot alternatives) = 112, less the 24 cases where ROSTER offers no slot at all for
        # DL/LB/DB (3 positions x 4 rosters x 2). A claim over an unstated population is how this
        # test's predecessor came to mean nothing, so the population is stated and checked.
        self.assertEqual(seen, 112 - 24, "the grid changed shape; re-derive it before moving this")

    def test_a_multi_eligible_candidate_is_lifted_to_the_cheapest_slot_he_can_reach(self):
        # Half two: the branch the old test could not reach. A WR/DB is anchored on the WR level
        # his bpa was built against (216), but the DB slot he can also fill is worth 104 to this
        # roster, so passing on him costs 104, not 216 -- and the term says so with a LIFT.
        alts = dr.shared_slot_alternatives(LEVELS, IDP_ROSTER)
        out = lo.displacement_level([], IDP_ROSTER, {"WR", "DB"}, LEVELS["WR"], slot_alternatives=alts)
        self.assertEqual((out["displaced"], out["adjustment"]), (104.0, 112.0))
        # The lift is the CHEAPEST reachable slot, not any reachable one: a WR/LB reaches LB (131)
        # and IDP_FLEX (131) but no DB slot, so he is lifted by 85 and not by 112.
        out = lo.displacement_level([], IDP_ROSTER, {"WR", "LB"}, LEVELS["WR"], slot_alternatives=alts)
        self.assertEqual((out["displaced"], out["adjustment"]), (131.0, 85.0))
        # ...and it is the cheapest slot he can still EVICT. Fill DB with a 200 -- above its 104
        # alternative, so the phantom is gone -- and the WR/DB falls back to the IDP_FLEX phantom
        # at 131, exactly the WR/LB answer. The lift tracks the lineup, not the eligibility list.
        held = [_p("w1", 260, "WR"), _p("w2", 250, "WR"), _p("f", 240, "RB"),
                _p("d", 200, "DB"), _p("lb", 190, "LB"), _p("dl", 180, "DL")]
        out = lo.displacement_level(held, IDP_ROSTER, {"WR", "DB"}, LEVELS["WR"], slot_alternatives=alts)
        self.assertEqual((out["displaced"], out["adjustment"]), (131.0, 85.0))
        # The same roster lifts a WR-ONLY candidate by nothing at all: both WR slots are held
        # above the anchor, but FLEX is open at 216, which is his anchor. Same board, same
        # levels, opposite sign -- the eligibility set is the whole of the difference.
        out = lo.displacement_level(held, IDP_ROSTER, "WR", LEVELS["WR"], slot_alternatives=alts)
        self.assertEqual(out["adjustment"], 0.0)

    def test_the_one_bound_that_covers_both_populations(self):
        # What replaced "never positive". Derived, not chosen: the clamp in displacement_level
        # floors `displaced` at the cheapest alternative among the slots the probe REACHES, so
        # the lift can never exceed the distance from his anchor down to that floor. For a
        # single-position probe that bound is exactly 0.0, which is why this is ONE statement.
        import itertools
        checked = positive = 0
        for rpos in (ROSTER, IDP_ROSTER):
            alts = dr.shared_slot_alternatives(LEVELS, rpos)
            slots = lo.slots_from_roster_positions(rpos)
            for a, b in itertools.permutations(LEVELS, 2):
                probe = {a, b}
                reach = [s for s in slots if probe & s["eligible"]]
                if not reach:
                    continue
                out = lo.displacement_level([], rpos, probe, LEVELS[a], slot_alternatives=alts)
                bound = round(LEVELS[a] - min(alts.get(s["slot_id"], LEVELS[a]) for s in reach), 2)
                checked += 1
                positive += out["adjustment"] > 0.0
                with self.subTest(rulebook=len(rpos), probe=f"{a}/{b}"):
                    self.assertLessEqual(out["adjustment"], bound + 1e-9)
        self.assertGreater(checked, 40)
        # Non-vacuous in the direction that matters: if nothing in this grid went positive the
        # bound above would be asserting nothing, exactly as its predecessor did.
        self.assertGreater(positive, 0, "no probe was lifted -- this grid re-pins the old vacuity")

    def test_a_full_lineup_prices_each_position_against_its_own_weakest_reachable_starter(self):
        full = [_p("q", 400, "QB"), _p("r1", 260, "RB"), _p("r2", 240, "RB"), _p("w1", 250, "WR"),
                _p("w2", 240, "WR"), _p("t", 230, "TE"), _p("f1", 235, "RB"), _p("f2", 233, "WR")]
        # RB reaches RB, RB, FLEX, FLEX -> weakest held is 233 (the WR in FLEX); TE reaches TE
        # and both FLEX -> weakest 230 (its own TE); QB reaches QB only -> 400.
        self.assertEqual(lo.displacement_level(full, ROSTER, "RB", 186.0)["displaced"], 233.0)
        self.assertEqual(lo.displacement_level(full, ROSTER, "TE", 173.0)["displaced"], 230.0)
        self.assertEqual(lo.displacement_level(full, ROSTER, "QB", 290.0)["displaced"], 400.0)

    def test_a_multi_eligible_probe_reaches_every_slot_its_eligibility_reaches(self):
        # WR, WR, FLEX, FLEX all held above the WR anchor; a WR-only probe must displace the
        # weakest holder, a WR/DB probe reaches the open IDP_FLEX phantom and is not deducted --
        # anchored, both times, on the WR level his price is built against.
        roster_idp = ROSTER[:8] + ["IDP_FLEX"] + ["BN"] * 6
        held = [_p("w1", 250, "WR"), _p("w2", 240, "WR"), _p("w3", 235, "WR"), _p("w4", 230, "WR")]
        self.assertEqual(lo.displacement_level(held, roster_idp, "WR", 216.0)["adjustment"], -14.0)
        self.assertEqual(lo.displacement_level(held, roster_idp, {"WR", "DB"}, 216.0)["adjustment"], 0.0)
        # ...and a second position no slot accepts adds nothing to the reach.
        self.assertEqual(lo.displacement_level(held, ROSTER, {"WR", "DB"}, 216.0)["adjustment"], -14.0)

    def test_a_position_no_slot_accepts_is_not_applicable_and_deducts_nothing(self):
        out = lo.displacement_level([_p("t1", 300, "TE")], ROSTER, "K", 100.0)
        self.assertEqual((out["displaced"], out["adjustment"], out["basis"]), (None, 0.0, lo.DISPLACEMENT_NOT_APPLICABLE))

    def test_an_unpriced_rostered_player_who_could_block_the_position_downgrades_the_basis(self):
        four = [_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")]
        partial = lo.displacement_level(four, ROSTER, "TE", 173.0, unpriced_eligible=[{"WR"}])
        self.assertEqual(partial["basis"], lo.DISPLACEMENT_ROSTER_PARTIAL, "a WR can hold FLEX, which a TE reaches")
        self.assertEqual(partial["adjustment"], -47.0, "the number is still reported, as a floor")
        clean = lo.displacement_level(four, ROSTER, "QB", 290.0, unpriced_eligible=[{"WR"}])
        self.assertEqual(clean["basis"], lo.DISPLACEMENT_MEASURED, "a WR cannot reach the QB slot")

    def test_the_probe_value_never_reaches_the_answer(self):
        # Doubling the probe changes nothing: it is subtracted back out.
        with mock.patch.object(lo, "_DISPLACEMENT_PROBE_VALUE", 2e6):
            doubled = lo.displacement_level([_p("t1", 300, "TE"), _p("t2", 250, "TE"), _p("t3", 220, "TE")], ROSTER, "TE", 173.0)
        self.assertEqual(doubled["displaced"], 220.0)

    def test_every_vocabulary_token_has_words(self):
        names = {n: v for n, v in vars(lo).items() if n.startswith("DISPLACEMENT_") and isinstance(v, str)}
        self.assertEqual({n: v for n, v in names.items() if v not in lo.DISPLACEMENT_BASIS_LABELS}, {})


class NoConstantInTheValuePathTests(unittest.TestCase):
    """#56. The term's derivation is the optimizer and the board's own levels. Read off the
    AST: no numeric literal other than 0 reaches the arithmetic of either function."""

    def _numeric_literals(self, func):
        tree = ast.parse(inspect.getsource(func).lstrip())
        return sorted({n.value for n in ast.walk(tree)
                       if isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
                       and not isinstance(n.value, bool) and n.value not in (0, 0.0, 2)})

    def test_displacement_adjustments_has_no_numeric_literal(self):
        self.assertEqual(self._numeric_literals(dr.displacement_adjustments), [])

    def test_displacement_level_has_no_numeric_literal_but_the_probe_and_rounding(self):
        # `2` is round()'s digit count and is excluded above; the probe is a named module
        # constant, so it does not appear as a literal in the function either.
        self.assertEqual(self._numeric_literals(lo.displacement_level), [])


def _rulebook():
    import data_merger as dm
    import draft_battery as db
    import run_draft_battery as rdb
    import run_roster_proof as rp
    merger = dm.DataMerger()
    players_db, _ = rdb.build_players_db_from_capture()
    season = rdb.season_projections_from_capture()
    league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                  dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
    merger.set_league_format(db.league_format_hint(league))
    points = rp.scoreable_pool(merger, players_db, league, season)
    return merger, players_db, season, league, points


_RB: dict = {}


def _board(picks, me="1"):
    if not _RB:
        _RB["v"] = _rulebook()
    merger, players_db, season, league, _ = _RB["v"]
    return dr.compute_draft_board(merger, players_db, picks, me, league, mode="balanced",
                                  sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)


def _ranked(position):
    if not _RB:
        _RB["v"] = _rulebook()
    _, players_db, _, _, points = _RB["v"]
    pos = lambda p: (players_db.get(str(p)) or {}).get("position")
    return sorted((p for p in points if pos(p) == position), key=lambda p: (-points[p], p))


def _pick(pid, roster, n, rnd):
    return {"pick_no": n, "round": rnd, "roster_id": roster, "player_id": str(pid)}


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class WiringOnTheRealRulebookTests(unittest.TestCase):

    def test_the_identity_closes_with_the_fourth_term_on_every_priced_row(self):
        te = _ranked("TE")
        rows = [r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(4)]) if r["final_score"] is not None]
        self.assertGreater(len(rows), 400)
        for r in rows:
            self.assertAlmostEqual(
                r["final_score"],
                r["universal_value"] + r["need_bonus"] + r["eligibility_bonus"] + r["depth_exposure"] + r["displacement_adj"],
                places=2, msg=r["name"])
            self.assertLessEqual(r["displacement_adj"], 0.0, r["name"])
            self.assertIn(r["displacement_basis"], lo.DISPLACEMENT_BASIS_LABELS, r["name"])

    def test_how_far_the_non_positive_claim_above_actually_reaches(self):
        # #52 phase 6 (W1-01). The assertion above is TRUE and it is nearly vacuous, which is a
        # combination worth making visible rather than deleting. _rulebook() builds a
        # superflex=False, no-IDP league, and the term can only go positive for a MULTI-eligible
        # candidate whose second eligibility reaches a slot priced below his anchor. Measured on
        # this exact board: 477 priced rows, of which ONE is multi-eligible -- Travis Hunter,
        # WR/DB -- and in a league with no IDP slot his DB half reaches nothing, so he reports
        # exactly +0.00. The claim above therefore ranges over a population in which it cannot
        # fail, and it was read for years as evidence that the term is non-positive in general.
        #
        # This test pins the SHAPE of that population, so the day the fixture gains an IDP slot
        # or a second dual-eligible row, the reach of the claim above changes visibly instead of
        # silently. The unit-level tests carry the actual two-population invariant.
        te = _ranked("TE")
        rows = [r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(4)])
                if r["final_score"] is not None]
        _, players_db, _, league, _ = _RB["v"]
        self.assertNotIn("IDP_FLEX", league["roster_positions"])

        def eligibility(row):
            info = players_db.get(str(row.get("player_id"))) or {}
            return {p for p in (info.get("fantasy_positions") or []) if p}

        multi = [r for r in rows if len(eligibility(r)) > 1]
        self.assertEqual(len(multi), 1, "the multi-eligible population of this board changed")
        self.assertEqual(eligibility(multi[0]), {"WR", "DB"})
        self.assertEqual(multi[0]["displacement_adj"], 0.0,
                         "a DB eligibility reached a slot in a league that has none")

    def test_the_term_is_a_per_position_constant_at_a_board_state(self):
        te = _ranked("TE")
        rows = [r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(4)]) if r["final_score"] is not None]
        by_position: dict[str, set] = {}
        for r in rows:
            by_position.setdefault(r["position"], set()).add(r["displacement_adj"])
        self.assertEqual({p: len(v) for p, v in by_position.items() if len(v) != 1}, {})
        self.assertLess(min(by_position["TE"]), -50.0, "four tight ends owned and no deduction at TE")
        self.assertEqual(by_position["WR"], {0.0})

    def test_switching_the_term_off_reproduces_the_pre_fix_board_exactly(self):
        """The in-process A/B idiom the probe relies on (engine-measurement skill): with
        displacement_adjustments patched to return nothing, every row's final_score is the
        pre-fix four-term sum, so the two arms differ in exactly one thing."""
        te = _ranked("TE")
        picks = [_pick(te[i], "1", i + 1, i + 1) for i in range(4)]
        with mock.patch.object(dr, "displacement_adjustments", lambda *a, **k: {}):
            off = {str(r["player_id"]): r for r in _board(picks)}
        on = {str(r["player_id"]): r for r in _board(picks)}
        moved = 0
        for pid, r in on.items():
            o = off[pid]
            if r["final_score"] is None:
                continue
            self.assertEqual(o["displacement_adj"], 0.0)
            self.assertEqual(o["displacement_basis"], lo.DISPLACEMENT_NO_POINTS_ANCHOR)
            self.assertAlmostEqual(o["final_score"], r["final_score"] - r["displacement_adj"], places=2, msg=r["name"])
            moved += r["displacement_adj"] != 0.0
        self.assertGreater(moved, 50, "the term did not fire on a four-tight-end roster")

    def test_invariant_4_my_own_bench_picks_never_improve_my_signal_at_that_position(self):
        """Reviewer invariant 4. A fixed tight end (TE#7) across my roster holding TE#1..#k
        for k = 3..6: his league VOR RISES as I drain the pool (the anchor moves in the
        hoarder's favour), and his acquisition value must not -- the ledger a person reads is
        the one that must stay flat or fall."""
        te = _ranked("TE")
        finals, uvs, ledgers, depths = [], [], [], []
        for k in range(3, 7):
            rows = {str(r["player_id"]): r for r in _board([_pick(te[i], "1", i + 1, i + 1) for i in range(k)])}
            r = rows[te[6]]
            finals.append(r["final_score"])
            uvs.append(r["universal_value"])
            ledgers.append(r["universal_value"] + r["displacement_adj"])
            depths.append(r["depth_exposure"])
        self.assertGreater(uvs[-1], uvs[0], f"fixture: the league anchor did not move in the hoarder's favour: {uvs}")
        # The ledger the term controls -- universal value against MY replacement -- never rises
        # as I add tight ends: the pool drain that lifts his league VOR is cancelled exactly by
        # the deduction, because what he must displace (my third tight end) has not changed.
        for a, b in zip(ledgers, ledgers[1:]):
            self.assertLessEqual(b, a + 1e-9, f"owning more tight ends improved the ledger: {ledgers}")
        # RESIDUAL, RECORDED NOT SMOOTHED (#216 report, "what is still broken"): final_score
        # DOES rise once, by depth_exposure, at the pick where a bench first exists (k=3 -> 4):
        # #139's insurance term credits a fifth tight end for insuring the three I start,
        # measured +3.72 here, bounded by DEPTH_EXPOSURE_MAX. That is the adversary's B-class
        # observation and it survives this fix; the displacement term removes the 40-60 point
        # bias, not this <= 12 point one. So the invariant is asserted on final_score up to
        # exactly that term, and the residual is asserted to be no larger than it.
        for a, b, da, db in zip(finals, finals[1:], depths, depths[1:]):
            self.assertLessEqual(b - db, a - da + 1e-9,
                                 f"owning more tight ends made the next one worth MORE beyond depth: {finals} depth {depths}")
        self.assertLessEqual(max(finals) - finals[0], dr.DEPTH_EXPOSURE_MAX + 1e-9,
                             f"the residual rise exceeds depth_exposure's own bound: {finals}")

    def test_invariant_2_the_quarterback_is_priced_positive_while_open_and_at_or_below_zero_once_filled(self):
        """Reviewer invariant 2 on a constructed 1QB state where every other seat has a QB
        (league QB demand = my slot alone, the collapse the review measured). Stated on
        final_score, the number that ranks -- and, honestly, on bpa too: the QB's VOR is 0.00
        here by the starter-demand model's own definition (see replacement_levels' docstring),
        so the positive price is the need term. Once my slot holds a QB, the best remaining
        QB must sit at or below zero unless he out-projects my starter."""
        qb = _ranked("QB")
        others = [_pick(qb[i + 1], str(i + 2), i + 1, 1) for i in range(11)]          # seats 2..12 each hold a QB
        open_rows = [r for r in _board(others) if r["position"] == "QB" and r["final_score"] is not None]
        best_open = max(open_rows, key=lambda r: r["projected_points"])
        self.assertEqual(best_open["bpa"], 0.0, "the collapse the review measured: rank 1 is the candidate himself")
        self.assertGreater(best_open["final_score"], 0.0)
        filled = others + [_pick(qb[0], "1", 12, 1)]                                   # I take QB#1
        filled_rows = [r for r in _board(filled) if r["position"] == "QB" and r["final_score"] is not None]
        best_filled = max(filled_rows, key=lambda r: r["projected_points"])
        self.assertLessEqual(best_filled["final_score"], 0.0, best_filled)
        self.assertLess(best_filled["displacement_adj"], 0.0, "my QB#1 must be what a second QB has to displace")


# MUTATION RESULTS (evidence/roster_shape/fix_216/mutations/, one at a time, each file restored
# byte-identical after each; a SyntaxError would have been recorded as NOT TESTED, none was):
#   M1 level never exceeds the anchor (term always 0)      KILLED  14 failures (this file, B/C/D)
#   M2 term dropped from the team_acquisition_value sum     KILLED  36 failures (identity tests, D)
#   M3 displacement_adjustments never computes an entry     KILLED   8 failures (wiring, C, room)
#   M4 multi-eligible probe stripped to its primary         KILLED   1 failure  (IDP-flex wiring)
#   M5 sign flipped (the term LIFTS a surplus)              KILLED  15 failures (non-positivity, B)
#   M6 partial basis never stamped                          KILLED   1 failure  (derivation)
#   M7 the room's displacement sentence removed             KILLED   1 failure  (Chromium panel)
#   M8 a literal constant (level * 1.5) in the value path   KILLED   1 failure  (AST guard)
#   M9 term not serialized to the JS payload                KILLED   2 failures (payload test)
if __name__ == "__main__":
    unittest.main()
