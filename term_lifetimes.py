"""Every term that prices a player, and how long the thing it measures stays true.

WHY THIS EXISTS. CDME_CONTRACTS' team_acquisition_value invariant 5 says a quantity may enter a
dynasty valuation only if its lifetime is at least as long as the asset's horizon. That rule
arrived from a bye-week question (#142) where it settled the case cleanly, and a rule that
settles one case and then lives only in prose will not settle the next one. This is the rule as
a registry a term has to be entered in, and a check that fails when one is not.

THE RULE IS A CATEGORY TEST, NOT A MAGNITUDE TEST, which is exactly what makes it worth
mechanising: it disqualifies a term regardless of how large its measured effect is, so it can
be applied BEFORE the expensive measurement instead of after. #142 did it in the other order
and spent three rounds of measurement on a question the category settled either way.

THE DISTINCTION THAT MAKES IT USABLE. Every team-specific term is transient in some sense, so
"transient" alone would disqualify the whole engine. What matters is transient in WHAT:

  ROSTER_STATE  -- need_bonus, eligibility_bonus, depth_exposure. These change constantly, and
                   they are admissible, because team_acquisition_value is a DECISION number
                   priced in the state the decision is made in. The decision is made now; the
                   state is now.
  MULTI_YEAR    -- time_horizon_adj, built from a three-year outlook. Matches the horizon.
  SEASON        -- expires when the season does, on the calendar, regardless of the roster.
  WEEK          -- a current-status fact (this player is Questionable today).

SEASON and WEEK terms are the ones that need a declared mitigation in a dynasty valuation. This
module does not decide what a mitigation must be; it records which terms have one and refuses
to let a term be added without an entry either way.
"""

from __future__ import annotations

from typing import Optional

#: Spans the dynasty horizon -- admissible without qualification.
MULTI_YEAR = "multi_year"
#: Valid for the decision being made in the state it was measured in. Admissible: TAV prices a
#: decision, and the decision is contemporaneous with the state.
ROSTER_STATE = "roster_state"
#: Expires with the season, on the calendar. Needs a mitigation in a dynasty valuation.
SEASON = "season"
#: A current-status fact, shorter still. Needs a mitigation.
WEEK = "week"

#: Lifetimes that price a dynasty asset without further argument.
ADMISSIBLE = (MULTI_YEAR, ROSTER_STATE)


#: Every term summed into universal_value or team_acquisition_value, with the lifetime of the
#: thing it measures and -- where that lifetime is shorter than the dynasty horizon -- what is
#: done about it. `mitigation=None` on a SEASON or WEEK term is a live finding, not an omission.
TERMS: dict[str, dict] = {
    "bpa": {
        "lifetime": SEASON,
        "mitigation": None,
        "register": "#50 / #81",
        "what": (
            "Value Over Replacement in raw projected POINTS for the CURRENT season, scaled "
            "linearly against the pool's largest VOR gap."
        ),
        "why": (
            "A season projection expires when the season does. It is evidence about multi-year "
            "value, not a claim scoped to one -- but it is the same number for a 23-year-old "
            "and a 32-year-old projected alike, and the dynasty market is not: holding current "
            "production fixed, r(age, trade_value) is -0.50 to -0.68 within position "
            "(run_age_signal_measurement.py). THIS IS THE LARGEST OPEN ITEM ON THE VALUATION "
            "PATH, not a footnote: #76 measured the anchor carrying 94.5% of universal_value's "
            "movement, so a one-season quantity dominates a multi-year price. time_horizon_adj "
            "is the only multi-year correction and is clamped to +/-10 on a scale spanning "
            "~500, which the same measurement shows is far too small -- the engine agrees with "
            "the market on 63.2% of near-equal pairs overall and 51.5% at age gaps of 9+, a "
            "coin flip exactly where the market is most certain.\n\n"
            "The inversion worth noticing: bpa's own FALLBACK path "
            "(position_relative_trade_value_vor) is built from trade_value, which IS a dynasty "
            "price carrying that aging discount. The fallback is lifetime-correct and the "
            "primary path is not."
        ),
    },
    "time_horizon_adj": {
        "lifetime": MULTI_YEAR,
        "mitigation": None,
        "register": None,
        "what": "Three-year outlook percentile minus current-season percentile, dynasty-gated.",
        "why": "Built from proj_3yr, so its lifetime matches the horizon it prices.",
    },
    "risk_adj": {
        "lifetime": WEEK,
        "mitigation": (
            "Dynasty-softened per-player (#35, Experiment D): the same four RISK_ADJ magnitudes "
            "scaled by the player's own time_horizon_adj, so a current-week health flag matters "
            "less for a player whose value is genuinely forward-looking. Gated on is_dynasty."
        ),
        "register": "#35",
        "what": "Current injury status (IR / Out / Doubtful / Questionable).",
        "why": (
            "A status is true this week and often false in three. It was applied "
            "UNCONDITIONALLY -- identical in dynasty and redraft -- until #35, which is the "
            "same defect this rule names, caught before the rule existed."
        ),
    },
    "need_bonus": {
        "lifetime": ROSTER_STATE,
        "mitigation": None,
        "register": "#87",
        "what": "A positional gate: does this roster still need a starter here.",
        "why": "Transient in roster state, which TAV prices by construction.",
    },
    "eligibility_bonus": {
        "lifetime": ROSTER_STATE,
        "mitigation": None,
        "register": None,
        "what": "What this candidate's multi-position flexibility unlocks for THIS lineup.",
        "why": "Transient in roster state, which TAV prices by construction.",
    },
    "depth_exposure": {
        "lifetime": ROSTER_STATE,
        "mitigation": None,
        "register": "#139",
        "what": "What a hole at this position would cost THIS roster.",
        "why": "Transient in roster state, which TAV prices by construction.",
    },
}

#: Quantities deliberately kept OUT of the valuation by this rule, recorded so the exclusion
#: reads as a ruling rather than an oversight -- and so a later reader does not re-derive the
#: measurement that the category question makes irrelevant.
EXCLUDED: dict[str, dict] = {
    "bye_collision": {
        "lifetime": SEASON,
        "register": "#142 / #146",
        "why": (
            "The NFL reassigns bye weeks annually, so a collision belongs to the (player, "
            "season) pair and dissolves in months while the asset does not. Inadmissible at ANY "
            "magnitude -- and the magnitude is real (worst-week losses 41-127 trade_value, a "
            "reachable tail near 7 bpa), which is the point: the category settles it either "
            "way. Admissible in REDRAFT, where the asset horizon IS one season (#146). Lives on "
            "a single-season surface instead: roster_diagnostics."
        ),
    },
}


#: THE SECOND AXIS, and for source-provided fields it usually binds first: can this field
#: REACH CDME at all? merger.external_values carries every external source, but CDME touches it
#: in exactly two places -- pick_synthesis._consensus_lookup and draft_room._rookie_lookup --
#: and both hard-filter to `source_name == "keeptradecut"` before reading a row. That filter IS
#: the ingestion boundary (test_cdme_ingestion_boundary.py's adversarial injection tests), and
#: composite_player_score, which does read every source, was deliberately removed from CDME's
#: math after an earlier audit found it corrupting the scarcity signal.
#:
#: So a field on any other source is unreachable by construction. Not "unused" -- UNREACHABLE,
#: which is a different finding and a different remedy: wiring it means loosening the filter,
#: which is the one thing the boundary forbids.
CDME_READABLE_SOURCE = "keeptradecut"

#: Every source-provided field with no production reader (#142's audit, #145's remainder),
#: scored on BOTH axes. Recorded because eight of the nine were being carried as "promising
#: orphans" when they are structurally blocked, and the ninth was not singled out.
CANDIDATE_INPUTS: dict[str, dict] = {
    "std_dev": {"source": "fantasypros", "file": "dynasty_ppr_rankings.csv",
                "lifetime": MULTI_YEAR, "what": "expert-panel disagreement about a dynasty rank"},
    "best": {"source": "fantasypros", "file": "dynasty_ppr_rankings.csv",
             "lifetime": MULTI_YEAR, "what": "most optimistic panel rank"},
    "worst": {"source": "fantasypros", "file": "dynasty_ppr_rankings.csv",
              "lifetime": MULTI_YEAR, "what": "most pessimistic panel rank"},
    "avg": {"source": "fantasypros", "file": "dynasty_ppr_rankings.csv",
            "lifetime": MULTI_YEAR, "what": "mean panel rank"},
    "analyst_avg": {"source": "espn", "file": "idp_redraft_rankings.csv",
                    "lifetime": SEASON, "what": "mean analyst rank, REDRAFT scope"},
    "injury_flag": {"source": "espn", "file": "idp_redraft_rankings.csv",
                    "lifetime": WEEK, "what": "current injury note; reaches 2.2% of the frame"},
    "ecr_1qb": {"source": "dynastyprocess", "file": "players.csv",
                "lifetime": MULTI_YEAR, "what": "expert consensus rank, 1QB"},
    "ecr_2qb": {"source": "dynastyprocess", "file": "players.csv",
                "lifetime": MULTI_YEAR, "what": "expert consensus rank, superflex"},
    "trend_30d": {"source": "keeptradecut", "file": "dynasty_superflex_halfppr.csv",
                  "lifetime": None,
                  "what": "30-day movement in the dynasty market price",
                  # The ONLY candidate on the source CDME can read, so neither the ingestion
                  # boundary nor the lifetime rule blocks it -- and it is blocked anyway, by
                  # the data. See UNSIGNED_TREND below.
                  "data_defect": "unsigned"},
    "source_format": {"source": "keeptradecut", "file": "dynasty_superflex_halfppr.csv",
                      "lifetime": None, "what": "plumbing: which format the export was for"},
}


#: #148. `trend_30d` survives both gates and fails on its own contents: across all 499 rows of
#: the committed KTC export there is not a single negative value. Direction is the entire
#: information content of a trend -- at +401 a player is either breaking out or collapsing, and
#: the column cannot say which -- so it is unusable as ingested.
#:
#: MOST LIKELY CAUSE, stated as a hypothesis because it cannot be confirmed from here: the
#: export is PDF text extraction of KTC's paginated web view (see that source's ATTRIBUTION.md),
#: and the site renders direction as a coloured arrow glyph rather than a "-" character, so the
#: magnitude survives extraction and the sign does not. That is the same failure family as the
#: value/rank concatenation the same attribution already documents. KTC's API is blocked from
#: this environment (403), so it cannot be checked against the live source.
#:
#: EITHER WAY IT IS AN INPUT DEFECT, NOT A PRINCIPLE -- which makes it the one #145 candidate
#: that is fixable rather than ruled out. A re-scrape that preserves sign makes the field
#: immediately admissible on both axes.
#:
#: Worth recording alongside: run_asset_character_measurement.py already wrote trend_30d off as
#: "always NaN, not usable today" -- but it checked the FANTASYPROS file, where the column is
#: absent. Nobody checked the keeptradecut file, where it is present and unsigned. A field
#: dismissed on the wrong source stays dismissed.
UNSIGNED_TREND = "unsigned"


def reachable(field: str) -> bool:
    """Could this field reach CDME without loosening the ingestion filter?"""
    entry = CANDIDATE_INPUTS.get(field)
    return bool(entry) and entry["source"] == CDME_READABLE_SOURCE


def candidate_verdicts() -> list[dict]:
    """Both axes per candidate field, most actionable first.

    A field can be blocked twice, and saying so matters: `analyst_avg` is on an unreachable
    source AND is redraft-scoped, so neither fixing the boundary nor finding a big effect would
    make it admissible. Reporting only the first blocker invites someone to remove it and think
    the field is now available.
    """
    out = []
    for field, entry in sorted(CANDIDATE_INPUTS.items()):
        blockers = []
        if not reachable(field):
            blockers.append(f"unreachable: on `{entry['source']}`, CDME reads only "
                            f"`{CDME_READABLE_SOURCE}`")
        if entry["lifetime"] in (SEASON, WEEK):
            blockers.append(f"lifetime `{entry['lifetime']}` is shorter than the dynasty horizon")
        if entry.get("data_defect") == UNSIGNED_TREND:
            blockers.append("DATA DEFECT: the ingested column is unsigned, so direction -- the "
                            "whole signal -- is missing (#148, fixable at the input)")
        out.append({"field": field, **entry, "blockers": blockers})
    return sorted(out, key=lambda row: len(row["blockers"]))


def violations() -> list[dict]:
    """Terms whose lifetime is shorter than the dynasty horizon with nothing done about it.

    Not an error list to be silenced -- an entry here is a finding with a register item, and
    the honest states are "mitigated" and "recorded as open", never "absent".
    """
    return [
        {"term": name, **entry}
        for name, entry in sorted(TERMS.items())
        if entry["lifetime"] not in ADMISSIBLE and not entry["mitigation"]
    ]


def describe(term: str) -> Optional[dict]:
    return TERMS.get(term) or EXCLUDED.get(term)


def main() -> int:
    print("TERMS PRICING A DYNASTY ASSET\n")
    print(f"  {'term':22} {'lifetime':14} {'status'}")
    for name, entry in sorted(TERMS.items()):
        if entry["lifetime"] in ADMISSIBLE:
            status = "admissible"
        elif entry["mitigation"]:
            status = f"mitigated ({entry['register']})"
        else:
            status = f"OPEN -- shorter than the horizon ({entry['register']})"
        print(f"  {name:22} {entry['lifetime']:14} {status}")

    print("\nEXCLUDED BY THIS RULE\n")
    for name, entry in sorted(EXCLUDED.items()):
        print(f"  {name:22} {entry['lifetime']:14} excluded ({entry['register']})")

    print("\n\nCANDIDATE INPUTS -- source fields with no production reader (#145)\n")
    print(f"  {'field':16} {'source':16} {'lifetime':12} verdict")
    for row in candidate_verdicts():
        verdict = "; ".join(row["blockers"]) if row["blockers"] else "REACHABLE -- open question"
        print(f"  {row['field']:16} {row['source']:16} {str(row['lifetime']):12} {verdict}")

    open_items = violations()
    print(f"\n{len(open_items)} open item(s).")
    for item in open_items:
        print(f"\n--- {item['term']} ({item['register']})")
        print(f"    {item['what']}")
        for line in item["why"].split("\n"):
            print(f"    {line}" if line else "")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
