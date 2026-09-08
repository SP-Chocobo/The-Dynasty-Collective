"""#216 -- the Draft Room must not collapse while the valuation underneath it is repaired.

The room is the product surface; the simulation is not. A valuation change can silently break
what the live board SHOWS and CLAIMS in four ways this file guards, each an instance of a
defect the register already records:

  #116  the display contract -- the numbers' scale and the sentences built on it.
  #186  the Python/JS boundary -- a replacement_basis token the JS has no words for.
  #187  the absence contract at the point a person reads it -- an unmeasured quantity
        rendered as a confident zero.
  #173/#180 the room still RUNS -- settled by executing the board in Chromium, not by reading it.

Written by the #216 adversary, blind to any fix, on f580c11. Two of these FAIL on today's code
and are findings in their own right, not predictions about a fix:

  - The scale prose is stale NOW. `_scale_vor_to_bpa` is the identity ("bpa IS vor ... no
    reference, no rescale, no clip") and has been since the bpa-unit repair; the metric-card
    help (design_system.DISPLAY_CONTRACT["universal_value"]) and the board's legend tooltip
    still tell the reader the number is "scaled against the largest gap left in the pool".
    #116 counted unqualified units; this is a qualified unit that is wrong.
  - The third roster term never reaches the board. team_acquisition_value = universal_value +
    need_bonus + eligibility_bonus + depth_exposure, the snapshot carries all three, and
    serialize_candidate emits needBonus and eligBonus only. On the #216 state where a fifth
    tight end is credited +3.72 of depth_exposure (basis `measured`), the room shows ACQ 72 over
    UV 68 with no sentence accounting for the difference. A fix that adds or changes a roster
    term lands in exactly this gap.

The executed tests need a Chromium binary (playwright's bundled one is found under
/opt/pw-browsers or on PATH); they skip, loudly named, where none exists. Every board rendered
here goes through draft_board_ui.serialize_snapshot -> render_board_html -> a real page load,
and reads the DOM back, so a template that throws, interpolates `null`, or prints a raw token
is caught by the same path a user hits.
"""

from __future__ import annotations

import ast
import glob
import inspect
import re
import shutil
import unittest
from pathlib import Path

import data_merger as dm
import design_system
import draft_battery as db
import draft_board_ui as ui
import draft_room as dr
import draft_strategy as ds
import pick_synthesis as ps
import run_draft_battery as rdb
import run_roster_proof as rp
from pick_synthesis import CandidateSnapshot, PickSnapshot

CAPTURE = Path("data/fixtures/sleeper_capture.json")


def _find_chrome():
    for pattern in ("/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                    str(Path.home() / ".cache/ms-playwright/chromium-*/chrome-linux/chrome")):
        hits = sorted(glob.glob(pattern))
        if hits:
            return hits[-1]
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


CHROME = _find_chrome()
try:
    from playwright.sync_api import sync_playwright  # noqa: F401
    HAVE_PLAYWRIGHT = True
except Exception:  # pragma: no cover -- environment without playwright
    HAVE_PLAYWRIGHT = False

_EXECUTABLE = unittest.skipUnless(CHROME and HAVE_PLAYWRIGHT,
                                  "needs playwright and a Chromium binary to EXECUTE the board")

_ROW_READER = """els => els.map(e => ({
  name: e.querySelector('.name').textContent,
  tav: e.querySelector('.tav').textContent.trim(),
  tavTitle: e.querySelector('.tav').getAttribute('title') || '',
  basis: [...e.querySelectorAll('.basis-note')].map(b => b.textContent),
  metrics: e.querySelector('.focus-metrics').textContent,
  focus: e.querySelector('.focus-body').textContent,
  required: !!e.querySelector('.required-slot'),
}))"""


def _execute(payload: dict) -> dict:
    """Render the payload through the shipped template, load it in headless Chromium, and read
    back what a person would see. Console errors and uncaught exceptions are collected, never
    swallowed: a board that throws half-way renders a half board."""
    from playwright.sync_api import sync_playwright
    html = ui.render_board_html(payload)
    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
        page = browser.new_page()
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        page.set_content(html, wait_until="load")
        rows = page.eval_on_selector_all(".row", _ROW_READER)
        # Everything a person could read, INCLUDING collapsed focus panels, EXCLUDING the
        # <script> whose JSON payload legitimately spells `null` for every absent field.
        body = page.evaluate(
            "[...document.body.children].filter(e => e.tagName !== 'SCRIPT')"
            ".map(e => e.textContent).join('\\n')")
        legend = page.evaluate("document.getElementById('legend').textContent")
        legend_titles = page.eval_on_selector_all("#legend span", "els => els.map(e => e.getAttribute('title') || '')")
        browser.close()
    return {"rows": rows, "body": body, "legend": legend, "legend_titles": legend_titles, "errors": errors}


def _candidate(**overrides) -> CandidateSnapshot:
    base = dict(
        player_id="123", name="J. Gibbs", position="RB", team="DET",
        bpa=88.5, bpa_source="points_vor_draftsharks", confidence=80.0,
        universal_value=88.5, need_bonus=6.0, eligibility_bonus=2.9,
        team_acquisition_value=97.4, survival_probability=0.31, intervening_picks=11,
        opportunity_cost=67.2, expected_value_of_waiting=27.4,
        denial_value=8.4, rival_premium_basis=None, denial_basis="measured", denial_team="Roster 9",
        rival_premium=8.4, positional_forfeit=77.9, position_expected_taken=2.4,
        positional_cliff={"tier": "HIGH", "gap": 22.4, "typical_gap": 6.1},
        position_run_detected=False, pick_necessity=88.0, necessity_label="STRONG ACTION",
        near_tie_with_leader=False, cliff_protection=False, block_opportunity=False,
        pure_value=False, context_elevated=False,
        consensus_rank=None, consensus_tier=None, reach_label=None, projected_points=250.0,
        replacement_basis=dr.REPLACEMENT_BASIS_LIVE_DEMAND,
    )
    base.update(overrides)
    return CandidateSnapshot(**base)


def _payload(candidates, **kw) -> dict:
    snap = PickSnapshot(pick_label="3.04", round=3, my_roster_id="1", candidates=tuple(candidates),
                        decision_regime=kw.get("regime", "contested"))
    return ui.serialize_snapshot(snap, pick_header="ON THE CLOCK", state_tags=[])


_ABSENT_MARKERS = ("null", "NaN", "undefined")


# ---------------------------------------------------------------------------------------
# #116 -- the display contract
# ---------------------------------------------------------------------------------------

def _scale_function_rescales() -> bool:
    """Does _scale_vor_to_bpa perform ANY arithmetic on its input? Read off the AST, not the
    docstring (which is prose about what it no longer does)."""
    tree = ast.parse(inspect.getsource(dr._scale_vor_to_bpa).lstrip())
    for node in ast.walk(tree):
        if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mult, ast.Div, ast.Sub, ast.Add)):
            return True
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) in ("clip", "rank"):
            return True
    return False


class TheScaleProseDescribesWhatTheCodeDoesTests(unittest.TestCase):
    """FAILS on f580c11. The two sentences that qualify the unit describe a rescale the pricing
    layer removed. A reader told the number is "scaled against the largest gap left in the
    pool" will read 71.86 as a fraction of something; it is projected points over a
    replacement anchor, and if a #216 fix moves that anchor the sentence is wrong twice."""

    _CLAIM = re.compile(r"scaled(?: linearly)? against the largest gap", re.I)

    def test_the_pricing_layer_is_the_identity_today(self):
        # The precondition, stated as a measurement of the code rather than assumed.
        self.assertFalse(_scale_function_rescales(), "_scale_vor_to_bpa rescales again -- the "
                         "two prose checks below are then WRONG in the other direction; re-derive")

    def test_the_metric_card_help_does_not_claim_a_rescale_the_code_does_not_perform(self):
        text = design_system.DISPLAY_CONTRACT["universal_value"]["help"]
        self.assertEqual(bool(self._CLAIM.search(text)), _scale_function_rescales(),
                         f"help text claims a pool-gap rescale: {text!r}")

    def test_the_board_legend_does_not_claim_a_rescale_the_code_does_not_perform(self):
        legend = ui._TEMPLATE_SOURCE.split('id="legend"', 1)[1]
        legend = legend.split("</script>", 1)[0]
        self.assertEqual(bool(self._CLAIM.search(legend)), _scale_function_rescales(),
                         "the legend tooltip claims a pool-gap rescale the pricing layer does not do")


def _identity_terms() -> dict[str, str]:
    """The roster terms of team_acquisition_value, READ OFF compute_draft_board's AST, mapped
    to the board-row field each is emitted under: {local name: emitted key}."""
    tree = ast.parse(inspect.getsource(dr.compute_draft_board).lstrip())
    operands: list[str] = []
    emitted: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "team_acquisition_value" for t in node.targets):
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Name) and sub.id not in operands:
                    operands.append(sub.id)
        if isinstance(node, ast.Dict):
            for k, v in zip(node.keys, node.values):
                if isinstance(k, ast.Constant) and isinstance(v, ast.Name):
                    emitted[v.id] = k.value
    names = [n for n in operands if n not in ("round",)]
    return {n: emitted.get(n, n) for n in names if n != "universal_value"}


class EveryTermOfTheIdentityReachesTheRoomTests(unittest.TestCase):
    """The room states the decomposition ("Fills a real roster gap: +x for need and +y for
    flexibility"; "about z acquisition-value points of context lift"). Those sentences are only
    true if every term that moved the number is available to the sentence. Derived from the
    engine's own AST so that a FOURTH term -- the shape a #216 fix is likely to take -- is
    caught the day it enters the identity, wherever it is dropped on the way to the screen."""

    def test_the_identity_has_the_three_named_roster_terms_today(self):
        # A PIN, so an addition is NOTICED (the schema-pin precedent in
        # test_display_contract_boundary). A fourth term must be carried to CandidateSnapshot,
        # serialize_candidate, the JS roster-gap sentence and DISPLAY_CONTRACT's acquisition
        # help TOGETHER, and then this set updated -- never bumped alone.
        self.assertEqual(set(_identity_terms().values()), {"need_bonus", "eligibility_bonus", "depth_exposure"},
                         f"identity terms now: {_identity_terms()}")

    def test_the_snapshot_carries_every_term(self):
        import dataclasses
        fields = {f.name for f in dataclasses.fields(CandidateSnapshot)}
        missing = [k for k in _identity_terms().values() if k not in fields]
        self.assertEqual(missing, [], f"CandidateSnapshot lacks identity terms {missing}")

    def test_the_payload_carries_every_term(self):
        """FAILS on f580c11: depth_exposure (and its basis) never reach the JS. Distinct,
        recognisable magnitudes per term so each can be found by VALUE in the serialized row,
        whatever key it travels under."""
        magnitudes = {"need_bonus": 1.25, "eligibility_bonus": 2.5, "depth_exposure": 5.0}
        c = _candidate(universal_value=50.0, need_bonus=1.25, eligibility_bonus=2.5,
                       depth_exposure=5.0, depth_basis="measured", team_acquisition_value=58.75)
        row = ui.serialize_candidate(c)
        carried = {v for v in row.values() if isinstance(v, (int, float)) and not isinstance(v, bool)}
        missing = [f"{term}={mag}" for term, mag in magnitudes.items()
                   if term in _identity_terms().values() and mag not in carried]
        self.assertEqual(missing, [], f"serialize_candidate drops identity terms: {missing}; "
                                      f"payload keys {sorted(row)}")

    def test_the_payload_carries_the_depth_basis_beside_the_number(self):
        """#174/#187 shape: a 0.0 whose basis is not `measured` is an absence wearing a number.
        The number may not cross the boundary without its companion."""
        row = ui.serialize_candidate(_candidate(depth_exposure=0.0, depth_basis="vacant"))
        self.assertIn("vacant", [v for v in row.values() if isinstance(v, str)],
                      f"depth_basis is not in the payload: {sorted(row)}")

    @_EXECUTABLE
    def test_the_rendered_panel_accounts_for_a_depth_driven_lift(self):
        """Executed. A candidate whose whole context lift is depth_exposure. The rendered
        focus panel must state that magnitude somewhere; on f580c11 it shows ACQ 55 over UV 50
        and says nothing about the 5."""
        c = _candidate(universal_value=50.0, need_bonus=0.0, eligibility_bonus=0.0,
                       depth_exposure=5.0, depth_basis="measured", team_acquisition_value=55.0)
        out = _execute(_payload([c]))
        self.assertEqual(out["errors"], [])
        focus = out["rows"][0]["focus"]
        self.assertIn("5.0", focus, f"the panel does not account for the depth term: {focus!r}")


# ---------------------------------------------------------------------------------------
# #186 -- the Python/JS boundary
# ---------------------------------------------------------------------------------------

def _basis_store_values() -> list[tuple[int, str]]:
    """Every assignment in draft_room whose target is a `...["replacement_basis"]` subscript
    (plain or .loc), as (line, source of the assigned value)."""
    source = Path("draft_room.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    stores = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue
            strings = [n.value for n in ast.walk(target.slice) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            if "replacement_basis" in strings:
                stores.append((node.lineno, ast.get_source_segment(source, node.value) or ast.dump(node.value)))
    return stores


class TheEngineOnlyStampsTokensTheTableKnowsTests(unittest.TestCase):
    """#186 recurs the moment a fix writes a NEW basis token as a literal: the JS renders it as
    itself (by #186's design) and the existing vocabulary test only knows the four names. This
    is the AST guard the existing string-based test could not be: every store into the
    replacement_basis column must assign a NAME bound to a key of REPLACEMENT_BASIS_LABELS, or
    None. PASSES on f580c11 (5 stores); mutation-checked by rewriting one as a literal."""

    def test_every_replacement_basis_store_assigns_a_named_vocabulary_token_or_absence(self):
        vocabulary = {name for name, value in vars(dr).items()
                      if isinstance(value, str) and value in dr.REPLACEMENT_BASIS_LABELS}
        stores = _basis_store_values()
        self.assertGreaterEqual(len(stores), 4, f"population: {stores}")
        offenders = [(line, value) for line, value in stores
                     if value not in vocabulary and value != "None"]
        self.assertEqual(offenders, [], f"stores that are neither a vocabulary name nor None: {offenders}")

    def test_every_vocabulary_name_is_a_key_of_the_label_table(self):
        # The converse: a constant added without a label is a token the JS will print raw.
        names = {name: value for name, value in vars(dr).items()
                 if name.startswith("REPLACEMENT_BASIS_") and isinstance(value, str)}
        unlabelled = {n: v for n, v in names.items() if v not in dr.REPLACEMENT_BASIS_LABELS}
        self.assertEqual(unlabelled, {}, f"tokens with no words: {unlabelled}")

    @_EXECUTABLE
    def test_an_unknown_token_renders_as_itself_never_as_the_strongest_claim(self):
        """Executed, not grepped. A candidate stamped with a token the table does not know --
        the exact shape of a fix adding `roster_surplus_anchor` on the Python side only."""
        token = "roster_surplus_anchor"
        out = _execute(_payload([_candidate(replacement_basis=token)]))
        self.assertEqual(out["errors"], [])
        basis = " ".join(out["rows"][0]["basis"])
        self.assertIn(token, basis, f"the raw token did not reach the screen: {basis!r}")
        for words in dr.REPLACEMENT_BASIS_LABELS.values():
            self.assertNotIn(words, basis, f"an unknown token was rendered as {words!r}")


# ---------------------------------------------------------------------------------------
# #187 -- absence at the point a person reads it
# ---------------------------------------------------------------------------------------

class TheAbsenceContractAtTheScreenTests(unittest.TestCase):

    @_EXECUTABLE
    def test_absent_numbers_render_as_a_mark_and_never_as_a_word_for_nothing(self):
        """Executed. Every Optional number nulled at once, including need_bonus, which a #216
        fix may well make conditional. The DOM may show the absence mark; it may not show
        `null`, `NaN` or `undefined`, and the template may not throw."""
        c = _candidate(universal_value=None, team_acquisition_value=None, bpa=None,
                       need_bonus=None, eligibility_bonus=None, projected_points=None,
                       survival_probability=None, intervening_picks=None, positional_forfeit=None,
                       rival_premium=None, positional_cliff=None, denial_value=None,
                       replacement_basis=None, near_tie_with_leader=None)
        out = _execute(_payload([c, _candidate(player_id="9", name="B. Robinson")]))
        self.assertEqual(out["errors"], [], f"the board threw: {out['errors']}")
        for marker in _ABSENT_MARKERS:
            self.assertNotIn(marker, out["body"], f"{marker!r} reached the screen")
        row = out["rows"][0]
        self.assertEqual(row["tav"], "—", f"absent acquisition value rendered as {row['tav']!r}")
        self.assertIn("Unpriced", row["tavTitle"])
        self.assertNotIn("roster gap", row["focus"], "a null need_bonus produced a roster-gap sentence")

    @_EXECUTABLE
    def test_a_measured_zero_need_is_not_described_as_a_gap_and_a_positive_one_is(self):
        """The sentence must follow the data in both directions."""
        zero = _candidate(player_id="1", need_bonus=0.0, eligibility_bonus=0.0)
        some = _candidate(player_id="2", name="T. McBride", need_bonus=4.0, eligibility_bonus=0.0)
        out = _execute(_payload([zero, some]))
        self.assertEqual(out["errors"], [])
        self.assertNotIn("roster gap", out["rows"][0]["focus"])
        self.assertIn("+4.0", out["rows"][1]["focus"])
        self.assertIn("unfilled roster need", out["rows"][1]["focus"])

    @_EXECUTABLE
    def test_a_deduction_from_roster_context_is_stated_not_silent(self):
        """LATENT on f580c11 and FAILS there on the synthetic row. Today every roster term is
        non-negative by construction (the paired test below proves it on the real board), so
        the room's silence about a DEDUCTION costs nothing. A #216 fix that lets roster context
        subtract -- a surplus penalty, a slot-aware anchor -- puts ACQ below UV with no sentence
        explaining why, which is #187's shape: a number a person reads with no companion. The
        contract is fix-agnostic: the magnitude of the deduction must appear in the panel."""
        c = _candidate(universal_value=50.0, need_bonus=-20.0, eligibility_bonus=0.0,
                       team_acquisition_value=30.0)
        out = _execute(_payload([c]))
        self.assertEqual(out["errors"], [])
        focus = out["rows"][0]["focus"]
        self.assertNotIn("Fills a real roster gap", focus)
        self.assertIn("20.0", focus, f"a 20-point roster deduction is rendered without a word: {focus!r}")


# ---------------------------------------------------------------------------------------
# #173 / #180 -- the room still runs, on the real board, at the #216 state
# ---------------------------------------------------------------------------------------

_REAL: dict = {}


def _real_snapshot() -> PickSnapshot:
    """build_snapshot at the #216 state B (I own TE#1..#4, rival "2" owns TE#5), the production
    pricing path, real rulebook, format set before the board."""
    if not _REAL:
        merger = dm.DataMerger()
        players_db, _ = rdb.build_players_db_from_capture()
        season = rdb.season_projections_from_capture()
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr", te_premium=False,
                                      dynasty=True, base_scoring=rdb.scoring_settings_from_capture())
        merger.set_league_format(db.league_format_hint(league))
        points = rp.scoreable_pool(merger, players_db, league, season)
        pos = lambda p: (players_db.get(str(p)) or {}).get("position")
        te = sorted((p for p in points if pos(p) == "TE"), key=lambda p: (-points[p], p))
        picks = [{"pick_no": 1, "round": 1, "roster_id": "1", "player_id": te[0]},
                 {"pick_no": 2, "round": 1, "roster_id": "2", "player_id": te[4]}]
        picks += [{"pick_no": 3 + i, "round": 2, "roster_id": "1", "player_id": p} for i, p in enumerate(te[1:4])]
        seats = [str(i) for i in range(1, 13)]
        order = ds.generate_pick_order(seats, len(league["roster_positions"]), "snake")
        _REAL["snap"] = ps.build_snapshot(
            merger, players_db, picks, order, len(picks), "1", league, pick_label="2.06",
            sleeper_projections=season, sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    return _REAL["snap"]


@unittest.skipUnless(CAPTURE.exists(), "needs the real capture")
class TheRealBoardStillRunsTests(unittest.TestCase):

    def test_the_snapshot_identity_includes_the_depth_term_where_it_is_measured(self):
        """Non-vacuous where test_pick_synthesis's identity check is not: at round 1 depth is
        0.0 everywhere. Here at least one candidate carries a measured depth term and the
        identity must still close with it."""
        snap = _real_snapshot()
        with_depth = [c for c in snap.candidates if c.depth_exposure]
        self.assertTrue(with_depth, f"no candidate of {len(snap.candidates)} carries depth_exposure")
        for c in snap.candidates:
            if c.team_acquisition_value is None:
                continue
            self.assertAlmostEqual(
                c.team_acquisition_value,
                c.universal_value + c.need_bonus + c.eligibility_bonus + (c.depth_exposure or 0.0),
                places=2, msg=c.name)

    def test_no_roster_term_is_negative_on_todays_board(self):
        """The non-vacuity partner of the deduction test above: today the room's silence about
        deductions is harmless because none exist. When this fails, that test stops being
        latent."""
        snap = _real_snapshot()
        negative = [f"{c.name} uv {c.universal_value} tav {c.team_acquisition_value}"
                    for c in snap.candidates
                    if c.team_acquisition_value is not None and c.team_acquisition_value < c.universal_value - 1e-9]
        self.assertGreater(len(snap.candidates), 10)
        self.assertEqual(negative, [])

    @_EXECUTABLE
    def test_the_real_board_renders_every_candidate_with_words_for_its_basis(self):
        """Executed on the real snapshot. No throw, no `null`, one row per candidate, every
        PRICED VS phrase from the vocabulary (a raw token here means the Python side emitted
        something the table cannot name), and every ACQ figure the number the engine produced."""
        snap = _real_snapshot()
        payload = ui.serialize_snapshot(snap, pick_header="ON THE CLOCK — 2.06", state_tags=["12-team PPR"])
        out = _execute(payload)
        self.assertEqual(out["errors"], [], f"the real board threw: {out['errors']}")
        for marker in _ABSENT_MARKERS:
            self.assertNotIn(marker, out["body"])
        self.assertEqual(len(out["rows"]), len(snap.candidates))
        words = set(dr.REPLACEMENT_BASIS_LABELS.values())
        for row, c in zip(out["rows"], snap.candidates):
            with self.subTest(candidate=c.name):
                expected = "—" if c.team_acquisition_value is None else f"{c.team_acquisition_value:.0f}"
                self.assertEqual(row["tav"], expected)
                priced_vs = [b for b in row["basis"] if b.startswith("PRICED VS")]
                if c.replacement_basis is None:
                    self.assertEqual(priced_vs, [])
                else:
                    self.assertEqual(len(priced_vs), 1)
                    self.assertTrue(any(w in priced_vs[0] for w in words), f"raw basis on screen: {priced_vs[0]!r}")
                # Two sentence sets in the template: the decisive-regime LEADER gets "it fills
                # a genuine roster gap" (need only); everyone else gets "Fills a real roster
                # gap: +x ... +y" (need or eligibility). Mirrored exactly, so the claim on
                # screen is checked against the number that justifies it.
                need = bool(c.need_bonus and c.need_bonus > 0)
                elig = bool(c.eligibility_bonus and c.eligibility_bonus > 0)
                leader = c is snap.candidates[0]
                expected = need if (leader and snap.decision_regime == "decisive") else (need or elig)
                self.assertEqual("roster gap" in row["focus"], expected,
                                 f"roster-gap sentence disagrees with need {c.need_bonus} elig "
                                 f"{c.eligibility_bonus} (leader={leader}, regime={snap.decision_regime})")

    @_EXECUTABLE
    def test_the_legend_states_the_unit_from_the_contract(self):
        out = _execute(ui.serialize_snapshot(_real_snapshot(), pick_header="x", state_tags=[]))
        self.assertIn(design_system.VALUE_UNIT_SHORT, out["legend"])
        self.assertIn("not fantasy points", out["legend"])


# MEASURED STATUS ON UNFIXED CODE (f580c11) and MUTATION RESULTS -- recorded at the bottom of
# the committed file after the adversary ran it.
if __name__ == "__main__":
    unittest.main()
