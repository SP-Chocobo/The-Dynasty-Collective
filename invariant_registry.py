"""Each stated invariant, and THE POPULATION IT WAS PROVEN OVER (#52 phase 6.3).

WHY THIS EXISTS. Every finding in the `#52` audit that cost real work had one shape:

    a repair expands a population
      -> an invariant proven over the OLD population silently stops holding
      -> the old test stays green, because it never enters the new domain.

It happened six times in one audit, and not once did anything announce it:

  * `displacement_adj <= 0` was proven over single-position probes. `#216` added per-slot
    alternatives, which admitted MULTI-eligible ones, and the bound stopped holding -- while the
    pinning test passed no per-slot alternatives and used single-position probes only, so it
    could not fail.
  * The board's absence contract was enforced over a HAND-LIST of 11 columns while its callers
    selected 29. Every quantity added since inherited the gap.
  * `depth_exposure`'s surplus flag was proven over rosters with no bench at all -- the one shape
    in which a roster-wide boolean and a per-position one agree.
  * The Python/JS rounding agreement held over every value that never landed on .5.
  * `context_elevated`'s reachability was a property of which rows carried a priced third term,
    and moved twice while the constant stayed put.
  * `TEAM_SPECIFIC_CAPS` bounded three terms; a fourth was added and hand-exempted on a premise
    that was false, and two shipped constants derive from the tuple.

A test suite cannot catch this on its own. A green suite means "no test entered a domain where
this fails", and that is exactly what it means when the domain has just grown.

WHAT THIS IS, AND WHAT IT IS NOT. Not a theorem prover and not a second test suite: every claim
here is already pinned by a real test, named in `pinned_by`. What it adds is the POPULATION as a
first-class, COUNTED thing. Each entry carries a callable that enumerates the population and the
size it had when the invariant was last verified against it. The guard in
test_invariant_registry.py re-counts and fails when the number moves -- which is not an error, it
is the notification this audit never got. The fix for a failure here is to re-verify the claim
over the new population and update the census, in that order.

DELIBERATELY SMALL. Seeded only with invariants this audit actually measured, because a registry
padded with claims nobody checked is a hand-list wearing a ratchet's clothes (#126), and the
entries that would rot first are the ones added for completeness.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class Invariant:
    """One claim, the population it ranges over, and who pins it."""

    name: str
    #: The claim, in one sentence, as it is stated where the code makes it.
    claim: str
    #: Why the size of this population is the thing to watch -- what growing it would admit.
    population: str
    #: Enumerates the population. Called by the guard; must be cheap and deterministic.
    members: Callable[[], list]
    #: The size when the claim was last verified against it.
    census: int
    #: Test ids that actually pin the claim. Checked for existence, not re-run here.
    pinned_by: tuple[str, ...]


# -- population enumerators ----------------------------------------------------------------
#
# Cheap, deterministic, and derived from the code rather than listed: an enumerator that hand-
# lists its own members would make the census a tautology.

def _tav_team_specific_terms() -> list[str]:
    """The team-specific terms added on top of universal_value to make team_acquisition_value.

    THE W4-02 POPULATION. `TEAM_SPECIFIC_CAPS` bounds the sum of the CAPPED ones; `#216` added a
    fourth term and hand-exempted it on the premise that it is non-positive, which is false for a
    multi-eligible candidate. Two shipped constants derive from that tuple. A fifth term arriving
    is exactly the event that must not pass unnoticed.
    """
    import draft_room as dr
    # The tuple itself, NOT an intersection with a set written here. The first version of this
    # enumerator did intersect, which made the census a tautology -- a fifth term could arrive
    # and the count could not move. That is the exact failure this module's own docstring warns
    # about, committed inside the guard against it, and a mutation found it rather than review.
    return sorted(dr.TEAM_SPECIFIC_TERMS)


def _positions_with_a_level() -> list[str]:
    """Positions a standard rulebook prices, i.e. the single-position probes `displacement_adj`'s
    non-positivity is proven over. Multi-eligible probes are NOT in this population and the bound
    is different for them -- see displacement_level's THE SIGN."""
    import lineup_optimizer as lo
    return sorted(lo.FANTASY_POSITIONS)


def _board_emitted_columns() -> list[str]:
    """Every column the board hands to a caller, in either mode. The absence contract is enforced
    over ALL of them now; it used to be enforced over a named subset while this list grew."""
    import draft_room as dr
    return sorted(dr.board_emitted_columns())


def _exposure_vocabulary() -> list[str]:
    """The depth-exposure basis tokens. `worst_loss` is priced under exactly one of them, so a new
    token is a new pricing decision whether or not anyone makes it deliberately."""
    import lineup_optimizer as lo
    return sorted(lo.EXPOSURE_BASIS_LABELS)


def _python_rendered_figure_sites() -> list[str]:
    """Streamlit render sites that put an engine figure on screen beside the Draft Room's own.
    Both surfaces must round identically; they did not, and the rule now has one home."""
    import ast
    import ui_source
    tree = ast.parse(ui_source.text())
    return sorted(
        f"{node.lineno}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "_figure"
    )


def _surfaces_consulting_the_withholding_policy() -> list[str]:
    """Call sites of `withheld_fields()` / `survival_is_presentable()` -- the surfaces that ASK
    whether a quantity may be shown.

    Counted in BOTH directions and each means something different. A DROP is a surface that
    stopped asking, which is the regression this phase repaired four times over. A RISE is a new
    surface wired correctly, and it needs a case in test_withheld_propagation.py -- the census
    is what prompts that, since a new boundary with no test is a guard that silently stops
    covering the thing it names.

    It cannot, by construction, see a surface that never asks at all. That is what the guard
    file's own boundary tests are for; this counts the wiring, they count the behaviour.
    """
    import ast
    import pathlib
    names = {"withheld_fields", "survival_is_presentable"}
    out = []
    for path in sorted(pathlib.Path(".").glob("*.py")):
        if path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in names:
                out.append(f"{path.name}:{node.lineno}:{name}")
    return out


def _take_model_consumers() -> list[str]:
    """Call sites of the take model (`_take_probability` / `_board_take_probability`).

    ONE PICK TAKES ONE PLAYER, so an opponent's take probabilities are mutually exclusive and
    must sum to <= 1.0 across their board. `#206` established that and normalised the model --
    for ONE of its two consumers. `positional_forfeits` went on summing the RAW table over each
    opponent's top five, capped per position, which conserves nothing: four positions each
    capped at 0.90 permit 3.6 players from a single pick. It returned 22.80 takes from 20 picks
    on a real board.

    A THIRD consumer is the event to catch. Each one either goes through this model or
    reimplements it, and the second took years to notice because the model's own docstring
    already claimed to be its only home.
    """
    import ast
    import pathlib
    names = {"_take_probability", "_board_take_probability"}
    out = []
    for path in sorted(pathlib.Path(".").glob("*.py")):
        if path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name in names:
                out.append(f"{path.name}:{node.lineno}:{name}")
    return sorted(out)


def _active_multi_eligible_players() -> list[str]:
    """Every ACTIVE player the current capture lists at more than one fantasy position.

    Registered because a term went inert here without anyone noticing, which is this registry's
    whole reason to exist running in the direction nobody watches: a population SHRINKING.
    `eligibility_bonus` prices what a player's multi-position eligibility unlocks, and
    draft_room's own comment names the case it was built for -- "WR/TE dual eligibility, a
    common real Sleeper listing", once measured at an 82.00 bonus.

    Measured on the capture (#52, the 6.1b ruling): 178 players carry more than one fantasy
    position, and every one that is OFFENCE-ONLY is retired -- Kelvin Benjamin, Vince Mayle,
    the Thigpens. Not one reaches a board. The live population is IDP cross-family (DL/LB 127,
    DB/LB 37) plus Travis Hunter (DB/WR), and flexibility between two IDP slots at similar
    levels rarely moves an optimal lineup: measured across 36 board states and 46,020 rows,
    the term is nonzero on FIVE, with a maximum of 0.84 against a bound of 12.00.

    So a census that moves here is the signal to re-derive. A vendor refresh that reintroduces
    an active WR/TE listing makes the retired term's population non-empty again, and the
    ruling that retired it was made against an empty one.

    Counted over the capture rather than a live board on purpose: a board filters by league
    format, and this question is about who EXISTS, not who a particular rulebook admits.
    """
    import player_universe as pu
    import run_draft_battery as rdb

    players_db, _ = rdb.build_players_db_from_capture()
    out = []
    for player_id, info in (players_db or {}).items():
        eligible = pu.player_eligible_positions(info or {})
        if len(eligible) > 1:
            out.append(f"{player_id}|{'/'.join(sorted(eligible))}")
    return sorted(out)


def _vendor_record_resolutions() -> list[str]:
    """Call sites of `_merge_across_eligibility` -- every place a player is resolved onto a
    vendor record, and therefore every place that has to decide what a CONTESTED result means.

    Two people resolving onto one record is a contested identity, and the one number neither may
    claim is withheld. That refusal was made in the pool and nowhere else: the roster path went
    back to the merger and got the price anyway, and the contest itself evaporated as soon as
    either player was drafted, because it was counted over available rows. A fourth resolution
    site is the event to catch -- each one either honours the refusal or quietly reopens it.
    """
    import ast
    import pathlib
    out = []
    for path in sorted(pathlib.Path(".").glob("*.py")):
        if path.name.startswith("test_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
            if name == "_merge_across_eligibility":
                out.append(f"{path.name}:{node.lineno}")
    return sorted(out)


REGISTRY: tuple[Invariant, ...] = (
    Invariant(
        name="team_acquisition_value is universal_value plus the team-specific terms",
        claim="sum(TEAM_SPECIFIC_CAPS) bounds the sum of the CAPPED team-specific terms -- NOT "
              "team_acquisition_value - universal_value, which the uncapped fourth term leaves "
              "unbounded in both directions.",
        population="One entry per team-specific term. A FIFTH term arriving is the event that "
                   "broke this last time: #216 added a fourth, hand-exempted it on a premise "
                   "measured false, and NECESSITY_DENIAL_SATURATION and "
                   "CONTEXT_ELEVATED_THRESHOLD still derive from the tuple.",
        members=_tav_team_specific_terms,
        census=4,
        pinned_by=("test_probability_bounds.TheCapsTupleBoundsWhatItActuallyBounds",),
    ),
    Invariant(
        name="multi-position eligibility has a population to price",
        claim="A term that prices multi-position eligibility is only meaningful while players "
              "carry more than one position. Measured across 36 board states and 46,020 rows, "
              "eligibility_bonus is nonzero on FIVE, at a maximum of 0.84 against a bound of "
              "12.00 -- and every OFFENCE-ONLY multi-eligible player in the capture is retired, "
              "so the WR/TE case the term was built for has no living members.",
        population="Every player the capture lists at more than one fantasy position. This is "
                   "the registry watching a population SHRINK, which is the direction nobody "
                   "checks: the term did not break, its subject left. A vendor refresh that "
                   "reintroduces an active offence dual-eligibility listing makes this census "
                   "move, and the 6.1b ruling that retired the term was made against the "
                   "population as it stands here.",
        members=_active_multi_eligible_players,
        census=178,
        pinned_by=("test_invariant_registry.TheRegistryIsWellFormedTests",),
    ),
    Invariant(
        name="displacement_adj is non-positive for a single-position candidate",
        claim="Every slot a one-position probe can reach is priced at or above his own anchor, "
              "because shared_slot_alternatives prices a slot at max(level) over what it admits. "
              "A MULTI-eligible probe is a different population with a different bound.",
        population="The positions a rulebook can price. Growing it adds probes; what actually "
                   "broke the older, stronger claim was not growth here but the arrival of "
                   "per-slot alternatives, which admitted multi-eligible probes that this "
                   "population does not contain.",
        members=_positions_with_a_level,
        census=9,
        pinned_by=(
            "test_216_displacement.DisplacementLevelDerivationTests"
            ".test_a_single_position_candidate_is_never_lifted",
            "test_216_displacement.DisplacementLevelDerivationTests"
            ".test_the_one_bound_that_covers_both_populations",
        ),
    ),
    Invariant(
        name="an absent quantity reaches a caller as None, never as NaN",
        claim="Every column the board emits has its missing values normalized to real None, so "
              "`is None` is a sound absence test downstream (#187).",
        population="Every emitted column. This was enforced over a HAND-LIST of 11 while the "
                   "callers selected 29 -- identity_basis, displacement_adj and time_horizon_adj "
                   "among the eighteen left out -- so the population growing was precisely how "
                   "the gap opened.",
        members=_board_emitted_columns,
        census=30,
        pinned_by=(
            "test_identity_provenance.ItReachesTheBoardInBothModesTests"
            ".test_no_emitted_value_on_the_board_is_a_nan",
        ),
    ),
    Invariant(
        name="depth_exposure numbers are depth evidence only under EXPOSURE_MEASURED",
        claim="A position is measured only when every one of its starters could actually be "
              "covered by a non-starting rostered player; draft_room prices worst_loss under "
              "that basis and no other.",
        population="The basis vocabulary. A new token is a new pricing decision at the consumer, "
                   "whether or not anyone makes it deliberately -- which is how the roster-wide "
                   "surplus flag came to stamp `measured` on positions with no backup at all.",
        members=_exposure_vocabulary,
        census=4,
        pinned_by=(
            "test_depth_exposure.TheFourStatesOfKnowingTests"
            ".test_a_real_bench_reports_measured_AT_THE_POSITIONS_THAT_HAVE_ONE",
            "test_depth_exposure.TheFourStatesOfKnowingTests"
            ".test_a_position_with_ONE_uncoverable_starter_is_not_depth_evidence",
        ),
    ),
    Invariant(
        name="one engine figure reads the same on every surface",
        claim="design_system.figure states the screen's rounding rule once, and every Python "
              "render site of a figure the Draft Room also renders goes through it.",
        population="The Python render sites. A new one added with a bare f-string is the whole "
                   "defect returning: Python rounds half-to-even and toFixed rounds half away "
                   "from zero, so the two disagree on any figure landing on .5 above an even "
                   "floor -- one player showed as 16 in one panel and 17 in the other.",
        members=_python_rendered_figure_sites,
        census=8,
        pinned_by=(
            "test_216_room_integrity.TheDisplayRoundingRuleTests"
            ".test_python_and_the_browser_round_the_boundary_class_identically",
            "test_display_contract_boundary.TheTwoUnitsAreToldApartTests"
            ".test_the_format_specs_are_still_identical_which_is_now_fine",
        ),
    ),
    Invariant(
        name="a withheld quantity does not reach a person on any surface",
        claim="pick_synthesis.withheld_fields() names what may not be presented; every "
              "presentation boundary filters through it, including deltas -- a delta of a "
              "withheld quantity gives a reader its direction and its size.",
        population="Surfaces that CONSULT the policy. Four did not and each leaked the whole "
                   "family: the diff, the chair prompt, the three system prompts (which named "
                   "it among 'real, already-computed numbers' and demonstrated citing it), and "
                   "the Prytaneum seed. A drop here is a surface that stopped asking; a rise is "
                   "a new one that needs a case in test_withheld_propagation.py.",
        members=_surfaces_consulting_the_withholding_policy,
        census=8,
        pinned_by=(
            "test_withheld_propagation.TheDiffDoesNotReportAWithheldDeltaTests",
            "test_withheld_propagation.TheChairPromptDoesNotCarryItTests",
            "test_withheld_propagation.TheSystemPromptsDoNotInviteItTests",
            "test_withheld_propagation.ThePrytaneumSeedDoesNotCarryItTests",
            "test_withheld_propagation.TheBoardPayloadShipsThePolicyWithTheValueTests",
        ),
    ),
    Invariant(
        name="expected takes cannot exceed the picks available to take them",
        claim="An opponent makes ONE pick, so their take probabilities are mutually exclusive "
              "and normalise to 1.0 across their board; summed over positions and intervening "
              "picks, expected_taken cannot exceed the pick count.",
        population="Call sites of the take model. `#206` normalised it and converted ONE of two "
                   "consumers; the other summed the raw table over a top-5 window with a "
                   "per-position cap, and returned 22.80 takes from 20 picks. A third consumer "
                   "either goes through this model or quietly reimplements it.",
        members=_take_model_consumers,
        census=4,
        pinned_by=(
            "test_draft_strategy.PositionalForfeitsTests"
            ".test_expected_taken_cannot_exceed_the_picks_available_to_take_them",
            "test_draft_strategy.PositionalForfeitsTests"
            ".test_on_a_fully_priced_board_the_takes_sum_to_EXACTLY_the_pick_count",
            "test_draft_strategy.PositionalForfeitsTests"
            ".test_both_consumers_of_the_take_table_read_it_through_one_model",
        ),
    ),
    Invariant(
        name="a contested identity's borrowed price is refused on every path",
        claim="Two players resolving onto one vendor record may neither claim its numbers. The "
              "contest is a property of WHO THEY ARE, so it is counted over the identified "
              "universe rather than the available subset, and the refusal is recorded so it can "
              "propagate past the frame it was made on.",
        population="Sites that resolve a player onto a vendor record. Each must decide what a "
                   "contested result means; the roster path decided differently from the pool "
                   "and handed a drafted player the very number the board refused him.",
        members=_vendor_record_resolutions,
        census=3,
        pinned_by=(
            "test_identity_partition_boundary.TheGuardDeclinesThePriceNotThePlayerTests"
            ".test_the_contest_survives_one_of_the_pair_being_DRAFTED",
            "test_identity_partition_boundary.TheGuardDeclinesThePriceNotThePlayerTests"
            ".test_a_player_drafted_out_of_a_contested_pair_is_not_priced_on_his_own_roster",
            "test_identity_partition_boundary.TheGuardDeclinesThePriceNotThePlayerTests"
            ".test_an_UNcontested_drafted_player_keeps_his_price",
        ),
    ),
)


def census_report() -> list[dict]:
    """Each invariant with its recorded census and the size of its population right now."""
    out = []
    for entry in REGISTRY:
        try:
            members = list(entry.members())
            observed, error = len(members), None
        except Exception as exc:                      # an enumerator that cannot run is a finding
            members, observed, error = [], None, f"{type(exc).__name__}: {exc}"
        out.append({"name": entry.name, "recorded": entry.census, "observed": observed,
                    "members": members, "error": error,
                    "moved": error is None and entry.census is not None and observed != entry.census})
    return out


def main() -> int:
    rows = census_report()
    for row in rows:
        mark = "MOVED" if row["moved"] else ("ERROR" if row["error"] else "ok")
        print(f"{mark:5s}  recorded={row['recorded']!s:>5}  observed={row['observed']!s:>5}  {row['name']}")
        if row["error"]:
            print(f"        {row['error']}")
    moved = [r for r in rows if r["moved"] or r["error"]]
    print(f"\n{len(REGISTRY)} invariants registered, {len(moved)} needing re-verification")
    return 1 if moved else 0


if __name__ == "__main__":
    raise SystemExit(main())
