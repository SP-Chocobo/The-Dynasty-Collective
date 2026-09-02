"""draft_board_ui is a translation layer, not an engine -- these tests pin the one thing
that actually matters: every field on the JSON payload is a direct, unmodified read off
CandidateSnapshot/PickSnapshot, never a recomputation. render_board_html is checked only
for basic structural validity (the payload actually lands in the document, no template
placeholder survives) -- the interaction behavior itself was validated in the browser
during the design pass, not re-tested here as JS-in-a-string.
"""

import json
import unittest

import draft_board_ui as ui
from pick_synthesis import CandidateSnapshot, PickSnapshot


def _candidate(**overrides) -> CandidateSnapshot:
    base = dict(
        player_id="123", name="J. Gibbs", position="RB", team="DET",
        bpa=88.5, bpa_source="points_vor_draftsharks", confidence=80.0,
        universal_value=88.5, need_bonus=6.0, eligibility_bonus=2.9,
        team_acquisition_value=97.4, survival_probability=0.31, intervening_picks=11,
        opportunity_cost=67.2, expected_value_of_waiting=27.4,
        denial_value=8.4, denial_team="Roster 9", rival_premium=8.4,
        positional_forfeit=77.9, position_expected_taken=2.4,
        positional_cliff={"tier": "HIGH", "gap": 22.4, "typical_gap": 6.1},
        position_run_detected=False, pick_necessity=88.0, necessity_label="STRONG ACTION",
        near_tie_with_leader=True, cliff_protection=True, block_opportunity=True,
        pure_value=False, context_elevated=False,
        consensus_rank=None, consensus_tier=None, reach_label=None, projected_points=250.0,
    )
    base.update(overrides)
    return CandidateSnapshot(**base)


def _snapshot(candidates, user_selected_player_id=None) -> PickSnapshot:
    return PickSnapshot(
        pick_label="3.04", round=3, my_roster_id="1", candidates=tuple(candidates),
        user_selected_player_id=user_selected_player_id, decision_regime="contested",
    )


class SerializeCandidateTests(unittest.TestCase):
    def test_every_field_is_a_direct_unmodified_read(self):
        c = _candidate()
        row = ui.serialize_candidate(c)
        self.assertEqual(row["name"], c.name)
        self.assertEqual(row["uv"], c.universal_value)
        self.assertEqual(row["tav"], c.team_acquisition_value)
        self.assertEqual(row["survival"], c.survival_probability)
        self.assertEqual(row["intervening"], c.intervening_picks)
        self.assertEqual(row["forfeit"], c.positional_forfeit)
        self.assertEqual(row["rivalPremium"], c.rival_premium)
        self.assertEqual(row["denialTeam"], c.denial_team)
        self.assertEqual(row["needBonus"], c.need_bonus)
        self.assertEqual(row["eligBonus"], c.eligibility_bonus)

    def test_positional_cliff_fields_unpacked_when_present(self):
        row = ui.serialize_candidate(_candidate())
        self.assertEqual(row["cliffTier"], "HIGH")
        self.assertEqual(row["cliffGap"], 22.4)
        self.assertEqual(row["cliffTypical"], 6.1)

    def test_positional_cliff_fields_none_when_absent(self):
        row = ui.serialize_candidate(_candidate(positional_cliff=None))
        self.assertIsNone(row["cliffTier"])
        self.assertIsNone(row["cliffGap"])
        self.assertIsNone(row["cliffTypical"])

    def test_forces_built_from_the_four_real_flags_only(self):
        row = ui.serialize_candidate(_candidate(
            near_tie_with_leader=True, cliff_protection=True,
            block_opportunity=False, pure_value=False,
        ))
        self.assertEqual(set(row["forces"]), {"tie", "cliff"})

    def test_no_forces_is_an_empty_list_not_none(self):
        row = ui.serialize_candidate(_candidate(
            near_tie_with_leader=False, cliff_protection=False,
            block_opportunity=False, pure_value=False,
        ))
        self.assertEqual(row["forces"], [])

    def test_context_gap_elevated(self):
        row = ui.serialize_candidate(_candidate(context_elevated=True, pure_value=False))
        self.assertEqual(row["contextGap"], "elevated")

    def test_context_gap_suppressed(self):
        row = ui.serialize_candidate(_candidate(context_elevated=False, pure_value=True))
        self.assertEqual(row["contextGap"], "suppressed")

    def test_context_gap_none_when_neither(self):
        row = ui.serialize_candidate(_candidate(context_elevated=False, pure_value=False))
        self.assertIsNone(row["contextGap"])

    def test_context_gap_prefers_elevated_when_both_somehow_true(self):
        # Not mutually exclusive by construction (see decision_path_flags' docstring) --
        # this pins which direction the UI shows when a contrived case satisfies both,
        # rather than leaving it to incidental dict-ordering.
        row = ui.serialize_candidate(_candidate(context_elevated=True, pure_value=True))
        self.assertEqual(row["contextGap"], "elevated")

    def test_necessity_class_mapping_covers_every_real_label(self):
        for label, expected_class in [
            ("MUST TAKE", "badge-necessity-must-take"),
            ("STRONG ACTION", "badge-necessity-strong"),
            ("PREFERRED", "badge-necessity-preferred"),
            ("CLOSE CALL", "badge-necessity-close-call"),
            ("LOW URGENCY", "badge-necessity-low"),
            ("DOESN'T MATTER MUCH", "badge-necessity-low"),
        ]:
            row = ui.serialize_candidate(_candidate(necessity_label=label))
            self.assertEqual(row["necClass"], expected_class)


class SerializeSnapshotTests(unittest.TestCase):
    def test_flags_the_user_selected_candidate_only(self):
        a = _candidate(player_id="1", name="A")
        b = _candidate(player_id="2", name="B")
        snap = _snapshot([a, b], user_selected_player_id="2")
        payload = ui.serialize_snapshot(snap, pick_header="ON THE CLOCK", state_tags=[])
        flagged = {c["name"]: c["flagged"] for c in payload["candidates"]}
        self.assertEqual(flagged, {"A": False, "B": True})

    def test_no_flagged_candidate_when_none_selected(self):
        snap = _snapshot([_candidate()])
        payload = ui.serialize_snapshot(snap, pick_header="x", state_tags=[])
        self.assertFalse(any(c["flagged"] for c in payload["candidates"]))

    def test_candidate_order_preserved_never_resorted(self):
        # The snapshot's own order is the engine's ranking -- this module must never
        # second-guess it, including by accident via a dict/set somewhere along the way.
        names = ["Z. Last", "A. First", "M. Middle"]
        candidates = [_candidate(player_id=str(i), name=n) for i, n in enumerate(names)]
        snap = _snapshot(candidates)
        payload = ui.serialize_snapshot(snap, pick_header="x", state_tags=[])
        self.assertEqual([c["name"] for c in payload["candidates"]], names)

    def test_decision_regime_passed_through_unchanged(self):
        snap = _snapshot([_candidate()])
        object.__setattr__(snap, "decision_regime", "decisive")
        payload = ui.serialize_snapshot(snap, pick_header="x", state_tags=[])
        self.assertEqual(payload["decisionRegime"], "decisive")

    def test_pick_header_and_tags_passed_through_verbatim(self):
        snap = _snapshot([_candidate()])
        payload = ui.serialize_snapshot(
            snap, pick_header="ON THE CLOCK — 3.04", state_tags=["3RR ACTIVE", "11 picks"],
        )
        self.assertEqual(payload["pickHeader"], "ON THE CLOCK — 3.04")
        self.assertEqual(payload["stateTags"], ["3RR ACTIVE", "11 picks"])


class RenderBoardHtmlTests(unittest.TestCase):
    def test_payload_is_embedded_and_placeholder_is_gone(self):
        snap = _snapshot([_candidate()])
        payload = ui.serialize_snapshot(snap, pick_header="x", state_tags=[])
        out = ui.render_board_html(payload)
        self.assertNotIn(ui._PAYLOAD_TOKEN, out)
        # Embedded with "<" escaped to < (see render_board_html's own docstring on
        # why raw json.dumps output is unsafe to embed verbatim) -- round-tripping the
        # escaped JSON back through json.loads must reproduce the exact original payload.
        embedded = out.split("const PAYLOAD = ", 1)[1].split(";\n", 1)[0]
        self.assertEqual(json.loads(embedded), payload)

    def test_output_is_a_complete_html_document(self):
        payload = ui.serialize_snapshot(_snapshot([_candidate()]), pick_header="x", state_tags=[])
        out = ui.render_board_html(payload)
        self.assertTrue(out.strip().startswith("<!doctype html>"))
        self.assertIn("<script>", out)
        self.assertIn("</script>", out)

    def test_player_name_with_special_characters_is_safely_json_escaped(self):
        # A name containing a literal </script> or a quote must not be able to break out
        # of the embedded JSON -- json.dumps is what's relied on for this, confirmed here
        # rather than just assumed.
        tricky = _candidate(name='D. "Air" O\'Brien </script>')
        payload = ui.serialize_snapshot(_snapshot([tricky]), pick_header="x", state_tags=[])
        out = ui.render_board_html(payload)
        # The literal closing tag must not appear unescaped inside the script body.
        script_body = out.split("<script>", 1)[1].split("</script>")[0]
        self.assertNotIn("</script>", script_body)

    def test_empty_candidate_list_renders_without_error(self):
        payload = ui.serialize_snapshot(_snapshot([]), pick_header="x", state_tags=[])
        out = ui.render_board_html(payload)
        self.assertIn('"candidates": []', json.dumps(payload))
        self.assertIsInstance(out, str)



class ForcesListOmitsWithoutAssertingTests(unittest.TestCase):
    """#61 rule 5 at the board. near_tie_with_leader is three-state, and `forces` is a list of
    what FIRED -- so both False and None are represented by omission, and that is correct only
    because nothing here renders the negative. If this module (or its JS) ever grows a "not in a
    tie" sentence, that sentence needs the three-state flag, not this list."""

    def _c(self, flag):
        return _candidate(near_tie_with_leader=flag)

    def test_a_measured_tie_appears(self):
        self.assertIn("tie", ui._forces(self._c(True)))

    def test_a_measured_non_tie_is_omitted(self):
        self.assertNotIn("tie", ui._forces(self._c(False)))

    def test_an_unmeasured_comparison_is_omitted_and_invents_no_token(self):
        forces = ui._forces(self._c(None))
        self.assertNotIn("tie", forces)
        # No "tie?" / "tie-unknown" token: the JS renders glyphs off this list by name, so a new
        # member would be an unrendered string, and the honest place for the distinction is the
        # debate briefing, which speaks in sentences. See test_pick_debate.
        self.assertEqual([f for f in forces if f.startswith("tie")], [])

    def test_the_serialized_candidate_carries_no_negative_tie_claim(self):
        """The whole reason omission is allowed to stand in for two different states."""
        payload = ui.serialize_candidate(self._c(None))
        self.assertNotIn("tie", payload["forces"])
        self.assertNotIn("nearTie", payload)


if __name__ == "__main__":
    unittest.main()


class BoardViewOptionsTests(unittest.TestCase):
    """The Draft Room's board-view selector.

    These moved out of app.py to exist at all: app.py is a Streamlit script that cannot be
    imported bare, so nothing here had ever been covered -- which is exactly how K and DEF
    reached the scored pool while remaining unselectable on the board.
    """

    OFFENSE = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "BN"]
    EVERYTHING = ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX",
                  "K", "DEF", "DL", "LB", "DB", "IDP_FLEX", "BN"]

    def test_kickers_and_defenses_are_selectable(self):
        # The regression: they enter the pool, get scored, get a horizon floor and a waiting
        # cost -- and were absent from _POSITION_VIEW_ORDER, so no view could ever show them.
        options = ui.position_view_options({"QB", "RB", "WR", "TE", "K", "DEF"}, self.EVERYTHING)
        self.assertIn("K", options)
        self.assertIn("DEF", options)

    def test_every_scoreable_position_can_be_viewed(self):
        # Guards the class of bug rather than the instance: any position the engine ranks must
        # be reachable in the selector when a league rosters it and candidates exist.
        present = {"QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"}
        options = set(ui.position_view_options(present, self.EVERYTHING))
        self.assertTrue(present <= options, f"unreachable positions: {present - options}")

    def test_a_league_without_a_position_is_not_offered_it(self):
        options = ui.position_view_options({"QB", "RB", "WR", "TE"}, self.OFFENSE)
        for absent in ("K", "DEF", "DL", "LB", "DB", "SUPER_FLEX", "IDP_FLEX"):
            self.assertNotIn(absent, options)

    def test_a_flex_slot_needs_both_the_slot_and_an_eligible_candidate(self):
        # Rosters IDP_FLEX but no IDP candidates remain -> an empty view is not offered.
        options = ui.position_view_options({"QB", "RB", "WR", "TE"}, self.EVERYTHING)
        self.assertNotIn("IDP_FLEX", options)
        self.assertIn("FLEX", options)

    def test_all_is_always_first(self):
        for present, roster in [({"QB"}, self.OFFENSE), (set(), self.EVERYTHING),
                                ({"QB", "RB", "WR", "TE", "K", "DEF"}, self.EVERYTHING)]:
            self.assertEqual(ui.position_view_options(present, roster)[0], "ALL")

    def test_options_follow_the_canonical_order(self):
        options = ui.position_view_options({"DEF", "QB", "K", "WR", "RB", "TE"}, self.EVERYTHING)
        self.assertEqual(options, ["ALL", "QB", "RB", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF"])


class BoardViewWidthTests(unittest.TestCase):
    """One row at any option count, by weighting columns to their labels.

    The control opens in place of the current-view tag, so it has to stay a single line. Of
    the thirteen views a fully rostered league offers, eleven are <=4 characters and two are
    verbose; an equal split lets the widest label set every column and runs the row out of
    space. Wrapping was tried and rejected as visually a block rather than an inline reveal.
    """

    FULL = ["ALL", "QB", "RB", "WR", "TE", "FLEX", "SUPER_FLEX",
            "K", "DEF", "DL", "LB", "DB", "IDP_FLEX"]

    def test_one_width_per_option_in_order(self):
        self.assertEqual(len(ui.view_option_widths(self.FULL)), len(self.FULL))

    def test_every_flex_slot_has_a_label(self):
        # The fallback is the raw slot key, and two of them are 8-9 characters: WRRB_FLEX and
        # REC_FLEX shipped with no label at all and would have blown out the row worse than
        # SUPER FLEX did. A new flex type must not be able to reach the UI unnamed.
        from player_universe import FLEX_SLOT_POSITIONS
        for slot in FLEX_SLOT_POSITIONS:
            label = ui.position_view_label(slot)
            self.assertNotEqual(label, slot, f"{slot} falls through to its raw key")
            self.assertLessEqual(len(label), 5, f"{slot} label {label!r} is too wide for one row")

    def test_a_flex_label_never_collides_with_a_position_label(self):
        # WRRB_FLEX rendered as "WR" would be indistinguishable from the WR position view
        # sitting beside it in the same row.
        from player_universe import FLEX_SLOT_POSITIONS
        positions = {"ALL", "QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB"}
        for slot in FLEX_SLOT_POSITIONS:
            self.assertNotIn(ui.position_view_label(slot), positions)

    def test_flex_labels_name_the_positions_they_accept(self):
        # Self-documenting: the label is the eligible set, so WRT and QWRT read as a pair.
        self.assertEqual(ui.position_view_label("FLEX"), "WRT")
        self.assertEqual(ui.position_view_label("SUPER_FLEX"), "QWRT")

    def test_a_two_position_flex_uses_full_slashed_codes(self):
        # "WR" would collide with the plain WR view; "W/R" is terser but reads as initials in
        # a row where every other entry is a real position code.
        self.assertEqual(ui.position_view_label("WRRB_FLEX"), "WR/RB")
        self.assertEqual(ui.position_view_label("REC_FLEX"), "WR/TE")

    def test_a_new_flex_type_is_labelled_without_touching_this_module(self):
        # The point of deriving: FLEX_SLOT_POSITIONS is the one list, and a slot added there
        # must not need a second edit here to avoid rendering as its raw key.
        from player_universe import FLEX_SLOT_POSITIONS
        FLEX_SLOT_POSITIONS["QBTE_FLEX"] = {"QB", "TE"}
        try:
            self.assertEqual(ui.position_view_label("QBTE_FLEX"), "QB/TE")
        finally:
            del FLEX_SLOT_POSITIONS["QBTE_FLEX"]

    def test_label_order_is_conventional_not_alphabetical(self):
        # QB, WR, RB, TE -- so QWRT and WR/RB come out consistent with one another.
        self.assertEqual(ui.position_view_label("WRRB_FLEX"), "WR/RB")   # not "RB/WR"
        self.assertEqual(ui.position_view_label("SUPER_FLEX"), "QWRT")   # not "QRTW"

    def test_super_flex_is_not_abbreviated_to_a_team_code(self):
        # This board renders team codes beside positions ("QB - SF"), so a two-letter SF
        # filter would read as San Francisco in exactly the context where it must not.
        self.assertNotEqual(ui.position_view_label("SUPER_FLEX"), "SF")

    def test_the_shortest_label_still_gets_a_tappable_floor(self):
        # "K" is one character; without the floor its column collapses to the text width.
        w = dict(zip(self.FULL, ui.view_option_widths(self.FULL)))
        self.assertGreaterEqual(w["K"], ui.VIEW_OPTION_MIN_UNITS)

    def test_every_option_fits_its_own_label_at_the_worst_case_count(self):
        # 13 options in a ~900px row. Roughly 9px per character at this control's font size,
        # plus button padding -- so the check is that no column is squeezed under its content.
        widths = ui.view_option_widths(self.FULL)
        px = [900 * x / sum(widths) for x in widths]
        for opt, got in zip(self.FULL, px):
            needed = 9 * len(ui.position_view_label(opt)) + 24
            self.assertGreater(got, needed,
                               f"{ui.position_view_label(opt)} would truncate at {got:.0f}px")

    def test_a_small_league_is_unaffected(self):
        widths = ui.view_option_widths(["ALL", "QB", "RB", "WR", "TE"])
        self.assertEqual(len(set(widths)), 1, "equal-length labels should get equal columns")


class WaitingCostProseSaysWhenTheFloorIsAssumed(unittest.TestCase):
    """#122: an imputed bench-appetite rate must not be presented as a measured one.

    horizon_floor's placement depends on a positional decay rate that is measured where the
    remaining pool is deep enough and IMPUTED -- the mean of whatever could be measured --
    where it is not. Both reach this layer as the same kind of number. Measured on a real
    12-team 1QB draft, the imputed case covers rounds 3 through 15, and four of six positions
    by round 10, so the prose was asserting an assumed floor with a measured floor's
    confidence for most of a draft.
    """

    def _with_basis(self, horizon_basis):
        return _candidate(projected_points=200.0, horizon_floor=120.0,
                          horizon_sensitivity=None, waiting_cost=80.0,
                          horizon_basis=horizon_basis)

    def test_a_measured_floor_is_stated_without_a_hedge(self):
        note = ui._waiting_note(self._with_basis("measured"))
        self.assertIsNotNone(note, "vacuous: no waiting note produced at all")
        self.assertNotIn("estimate", note["title"].lower())

    def test_an_imputed_floor_says_so(self):
        note = ui._waiting_note(self._with_basis("imputed"))
        self.assertIsNotNone(note, "vacuous: no waiting note produced at all")
        self.assertIn("estimate", note["title"].lower())
        self.assertIn("too thin to measure", note["title"])

    def test_the_two_actually_differ(self):
        # Guards the pair: if the note ignored horizon_basis entirely, both tests above could
        # still pass off one shared string that happened to contain the word.
        measured = ui._waiting_note(self._with_basis("measured"))["title"]
        imputed = ui._waiting_note(self._with_basis("imputed"))["title"]
        self.assertNotEqual(measured, imputed)
