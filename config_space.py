"""What must hold in EVERY league, what is allowed to differ between leagues, and which
configurations we have actually exercised.

THE ARCHITECTURAL POINT, stated once. PPR, half-PPR, TE premium, first downs, completion
bonuses, roster size, flex count, superflex, dynasty-vs-redraft are CONFIGURATION DIMENSIONS.
None of them is a foundational assumption, and no single one of them is "the" league. The engine
must ingest arbitrary supported settings and reason correctly over them, so a certification run
proves two different kinds of thing and must never merge them:

  INVARIANT      A property that must hold in every supported configuration. A violation is a
                 DEFECT wherever it appears. These are what certification certifies.
  CONFIGURATION-  An outcome that is EXPECTED to move with the settings. A different number in a
  DEPENDENT      different league is the configuration layer working, not a regression. These
                 are reported, never asserted against a fixed value.

WHY THIS FILE EXISTS NOW. `#250` measured the same roster under two rulebooks and the verdict
inverted -- `3/12 -0.84%` under PPR, `10/12 +1.04%` under Fourth and Forever's rules. Before
that, the 33-arm battery was read as universal evidence about the engine. It was not: it was
evidence about ONE REGION of the configuration space. The correction is not to crown a new
canonical league. It is to say which claims were ever configuration-free.

DERIVED, NOT HAND-LISTED (#126). The split is not my opinion about which audits matter -- it is
read out of `draft_battery`'s own structure. Whatever `structural_findings` calls IS the
invariant set, because that function's contract is "a finding here is a DEFECT, not an
observation". Whatever else `audit_trajectory` emits is the dependent set, because that section
of the module says "no verdict, because a verdict would need a number I chose". Add an audit to
either half and this file follows it; declare it in neither and the test fails.
"""

from __future__ import annotations

import ast
import collections
import inspect
from typing import Optional

import draft_battery as db
import league_config as lc

#: Keys of `audit_trajectory`'s record that describe the RUN rather than the engine. Not
#: invariants and not outcomes -- they are how you find the arm again.
METADATA_KEYS = frozenset({"label", "picks", "rosters"})

#: The key under which `audit_trajectory` files the invariant violations.
FINDINGS_KEY = "findings"

#: Why each invariant is configuration-free, and the DOMAIN it is asserted over. An invariant
#: with a precondition is still an invariant; an invariant with an unstated precondition is a
#: trap. `unfilled_starting_slots` is the one with a real domain, and `structural_findings`
#: already takes `audit_roster_fill` to express it.
INVARIANT_DOMAINS = {
    "unfilled_starting_slots":
        "Every supported configuration, WHEN the draft is at least as long as the STARTING "
        "lineup -- `rounds >= len(starting_slots(roster_positions))`. Not the roster length: "
        "the audit asks whether the starters can be fielded and says nothing about the bench. "
        "A 12-round draft of a 20-slot roster whose lineup needs 9 starters is still in domain; "
        "`audit_roster_fill=False` exempts the arms that genuinely are not. The slots are read "
        "from the league's own roster_positions, so the assertion is configuration-free while "
        "its REFERENT is configuration-derived -- the shape every invariant here has. "
        "CORRECTED (#251): the precondition was written as an EQUALITY against roster length "
        "and enforced as one by test_draft_battery. That was stricter than the property needs "
        "and indistinguishable from it while every arm was a mock league with no IR; the first "
        "real captured league (29 slots, 26 draftable, 10 startable) failed the equality while "
        "satisfying the property. #242's defect, one layer up.",
    "unpriced_picks":
        "Every supported configuration, no precondition. No rulebook and no roster makes it "
        "acceptable to spend a pick on a player the engine could not price: the ordering fell "
        "through to a tiebreak with no value behind it.",
    "undraftable_positions":
        "Every supported configuration, no precondition. Holding a position the league offers no "
        "slot for -- not even a flex share -- is a pool filter that leaked. Which positions "
        "those are is read from the league; that it must be none is not.",
    "duplicate_picks":
        "Every supported configuration, and the only one that does not consult the league at "
        "all. Two chairs cannot own the same player.",
}

#: Why each reported quantity is EXPECTED to move with the settings. A number here is evidence
#: about a configuration, never about the engine in general -- which is exactly the error `#250`
#: corrected, and the reason this column exists rather than a second list of thresholds.
DEPENDENT_REASONS = {
    "shape": "Positional composition follows the rulebook and the slots. A half-PPR TE-premium "
             "league SHOULD produce different roster shapes than full PPR.",
    "margins": "TAV margins are in a bpa-anchored unit that is re-derived per board, and the "
               "board is priced from the league's own scoring.",
    "qualifiers": "Near-tie and deviation qualifiers are relative to a scale that moves with the "
                  "rulebook.",
    "regimes": "Which decision regimes fire depends on roster shape and round count.",
    "strength": "Measured against `reference_values`, which is built from the league's own "
                "scoring settings. Comparing it across configurations compares two rulers.",
    "unpriced_at_decision": "A COVERAGE report, not a verdict: how often absence reached the "
                            "decision surface. Its population depends on the pool the "
                            "configuration admits.",
}


def invariant_audits() -> list[str]:
    """The audits `structural_findings` actually calls, read from its source.

    Derived rather than listed: the invariant set is defined as "whatever that function
    aggregates", because its own contract is that a finding there is a defect."""
    tree = ast.parse(inspect.getsource(db.structural_findings))
    called = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            name = node.func.id
            if name not in called and callable(getattr(db, name, None)):
                called.append(name)
    return sorted(called)


def dependent_outcomes() -> list[str]:
    """The keys `audit_trajectory` emits that are NOT the findings list and NOT metadata."""
    tree = ast.parse(inspect.getsource(db.audit_trajectory))
    keys: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Dict):
            for key in node.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    keys.append(key.value)
            break
    return sorted(k for k in keys if k not in METADATA_KEYS and k != FINDINGS_KEY)


#: A scoring key that is ABSENT is not a key with value 0. `bonus_rec_te` missing means the
#: league has no TE premium; `bonus_rec_te: 0.0` means it declares one worth nothing. Folding
#: them together made the TE-premium axis read as CONSTANT across a matrix that varies it --
#: the absence contract (#61/#187) applied to configuration coordinates.
ABSENT = "<absent>"


def _league_axes(league: dict, key_universe: Optional[set] = None) -> dict[str, object]:
    """One league reduced to the configuration coordinates that can differ between leagues.

    Roster shape enters as its SLOT COUNTS rather than the raw list, so two rosters that differ
    only in slot order are one configuration. Scoring enters key by key, with absence carried
    as `ABSENT` rather than dropped -- see the note above."""
    positions = league.get("roster_positions") or []
    counts = collections.Counter(positions)
    axes: dict[str, object] = {
        "teams": league.get("total_rosters"),
        "dynasty": (league.get("settings") or {}).get("type"),
        "draft_rounds": league.get("draft_rounds"),
        "startable_slots": len(lc.starting_slots(positions)),
        "draftable_slots": len(lc.draftable_slots(positions)),
    }
    scoring = league.get("scoring_settings") or {}
    slots = set(positions) | {k.split(":", 1)[1] for k in (key_universe or ()) if k.startswith("slot:")}
    for slot in sorted(slots):
        axes[f"slot:{slot}"] = counts[slot]
    keys = set(scoring) | {k.split(":", 1)[1] for k in (key_universe or ()) if k.startswith("scoring:")}
    for key in sorted(keys):
        axes[f"scoring:{key}"] = scoring.get(key, ABSENT)
    return axes


def coverage(matrix: Optional[list[dict]] = None,
             reference_leagues: Optional[dict[str, dict]] = None) -> dict:
    """Which configuration axes the matrix VARIES, and which values real leagues carry that it
    never produces.

    Two different questions, deliberately separated:

      `varied`    an axis the matrix moves. Anything it holds constant is an axis the run
                  cannot say a word about, however many arms it has.
      `uncovered` a value a REAL captured league carries that no arm produces. This is the
                  `#250` gap made countable: the matrix never emitted a first-down or
                  completion-bonus key at all, so every claim it supported was about a region
                  of the space that excludes the league being played.
    """
    # THE MATRIX MUST BE BUILT THE WAY THE BATTERY BUILDS IT. `league_matrix()` with no
    # base_scoring produces arms carrying only `rec`, because #213's repair is to pass the
    # captured rulebook in. Measuring coverage against the bare matrix reported sixty scoring
    # keys as uncovered that every real arm carries -- the #241 failure mode (build the matrix
    # differently from the run, then read the difference as a finding) in a new instrument.
    if matrix is None:
        import run_draft_battery as rdb
        matrix = db.league_matrix(rdb.scoring_settings_from_capture())

    reference_leagues = reference_leagues or {}
    universe: set[str] = set()
    for league in [a["league"] for a in matrix] + list(reference_leagues.values()):
        universe |= set(_league_axes(league))

    seen: dict[str, set] = collections.defaultdict(set)
    for arm in matrix:
        for axis, value in _league_axes(arm["league"], universe).items():
            seen[axis].add(value if isinstance(value, (int, float, str, type(None))) else str(value))

    varied = sorted(a for a, v in seen.items() if len(v) > 1)
    constant = sorted(a for a, v in seen.items() if len(v) == 1)

    # TWO KINDS OF UNCOVERED, and merging them makes the report unusable.
    #
    #   value   the reference league declares a value NO ARM EVER PRODUCES. A real gap: the
    #           configuration layer is never exercised at that coordinate.
    #   absent  the reference league does not declare the key at all, while every arm does.
    #           That is the reference being a SMALLER rulebook, not the matrix failing to
    #           cover something. Worth listing, worth never confusing with the first.
    uncovered: dict[str, dict] = {}
    for name, league in reference_leagues.items():
        axes = _league_axes(league, universe)
        gaps = {axis: value for axis, value in axes.items()
                if axis.startswith(("scoring:", "slot:")) and value not in seen.get(axis, set())}
        uncovered[name] = {
            "value_never_produced": {a: v for a, v in gaps.items() if v != ABSENT},
            "key_absent_from_this_league": sorted(a for a, v in gaps.items() if v == ABSENT),
        }
    return {"arms": len(matrix), "axes": len(seen), "varied": varied, "constant": constant,
            "uncovered_by_reference_league": uncovered}


def classification() -> dict:
    """The whole split, with a reason attached to every entry."""
    return {
        "invariants": {name: INVARIANT_DOMAINS.get(name) for name in invariant_audits()},
        "configuration_dependent": {name: DEPENDENT_REASONS.get(name)
                                    for name in dependent_outcomes()},
    }


def main() -> int:
    import json
    cls = classification()
    print("INVARIANT -- must hold in every supported configuration")
    for name, why in cls["invariants"].items():
        print(f"  {name}\n      {why}")
    print("\nCONFIGURATION-DEPENDENT -- expected to move with the settings")
    for name, why in cls["configuration_dependent"].items():
        print(f"  {name}\n      {why}")
    cov = coverage(reference_leagues=reference_leagues())
    print(f"\nCOVERAGE over {cov['arms']} arms and {cov['axes']} axes")
    print(f"  varied   ({len(cov['varied'])}): {', '.join(cov['varied'])}")
    print(f"  constant ({len(cov['constant'])}): {', '.join(cov['constant'])}")
    for name, gaps in cov["uncovered_by_reference_league"].items():
        real = gaps["value_never_produced"]
        print(f"\n  {name}: {len(real)} coordinate(s) carrying a value NO ARM PRODUCES")
        for axis, value in sorted(real.items()):
            print(f"      {axis} = {value}")
        print(f"      (+ {len(gaps['key_absent_from_this_league'])} keys this league simply "
              f"does not declare, which is not a matrix gap)")
    return 0


def reference_leagues() -> dict[str, dict]:
    """The real captured leagues, as configuration points. NEITHER IS CANONICAL -- they are two
    coordinates we happen to have ground truth for, and they are here so coverage can be
    measured against something real rather than against my imagination."""
    import json
    from pathlib import Path
    import run_draft_battery as rdb
    out: dict[str, dict] = {}
    capture = Path("data/league_captures/fourth_and_forever.json")
    if capture.exists():
        cap = json.loads(capture.read_text(encoding="utf-8"))
        out["fourth_and_forever"] = {
            "roster_positions": cap["roster_positions"],
            "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
            "total_rosters": 12, "settings": {"type": 2},
        }
    try:
        out["sleeper_fixture"] = {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "FLEX"] + ["BN"] * 6,
            "scoring_settings": rdb.scoring_settings_from_capture(),
            "total_rosters": 12, "settings": {"type": 2},
        }
    except Exception:
        pass
    return out


if __name__ == "__main__":
    raise SystemExit(main())
