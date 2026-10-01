"""The VDS battery: VARIED DRAFTING STRATEGY, crossed with format.

WHY A SECOND BATTERY RATHER THAN MORE ARMS IN THE FIRST. `draft_battery.league_matrix()` varies
the FORMAT and barely varies anything else: of its 36 arms, 34 run `mode="auto"` and the only two
that vary strategy are both `12T_ppr`. It is a format battery with a token strategy axis, and its
own comment says so of the axis it does have -- "until this was added the battery barely varied
it".

That is the gap `#20`/`#22` fell through. The `acting_now_value` ordering passed the format battery
and then under-drafted QB in superflex: a STRATEGY change, caught late, by a different instrument.
A battery that holds strategy fixed cannot see a strategy regression no matter how many formats it
runs.

THE THREE AXES, all reachable through parameters the engine already has. Nothing here invents
engine behaviour, and that is deliberate -- a battery that needs new engine code to run is testing
the code it shipped with.

  - `mode`          auto / balanced / upside. Which valuation a round uses.
  - `upside_rule`   round / crossing (`#261`). WHICH QUESTION decides upside mode -- the calendar
                    or the board.
  - `opponent_noise` (`#263b`). HOW WELL THE RIVALS DRAFT: `{"top_k", "seed", "sharp_seats"}`
                    makes every non-sharp seat choose uniformly from its own top_k instead of its
                    best. `None` means every seat takes its own top candidate, which is the
                    MAXIMALLY EFFICIENT drain and therefore a lower bound on when any
                    board-exhaustion signal can fire.

`simulate_full_draft`'s own comment already requires the sweep this battery performs: *"top_k is
NOT a derived constant and must be swept and reported across, never chosen (#56)."* Until now
nothing swept it.

THE AUDITS ARE NOT REIMPLEMENTED. `structural_findings`, `reference_values` and `audit_trajectory`
are imported from `draft_battery` and called unchanged. Two batteries with two copies of one audit
is two homes for one fact (`#126`), and the copy that drifts is the one nobody is watching.

FORMATS ARE CHOSEN FOR WHERE STRATEGY INTERACTS WITH STRUCTURE, not for coverage -- the format
battery already covers formats. Six formats x six strategies is 36 arms, the same order of work as
the format battery, which takes hours. Run it deliberately.

    python3 run_vds_battery.py [--out VDS_REPORT.json] [--only LABEL,LABEL]
"""

from __future__ import annotations

import draft_battery as db
import draft_room as dr

#: The seed for every noisy arm. FIXED AND CARRIED IN THE ARM LABEL's config, never re-rolled:
#: `draft_simulation`'s docstring forbids substituting randomness for what should vary between
#: trials, and the defence of an opponent-skill axis is precisely that it is orthogonal to format
#: and reproducible. One seed across arms also means a difference between two noisy arms is the
#: arm, not the draw.
VDS_SEED = 20260922

#: Rival skill levels to sweep. NOT chosen as "the right" values and not to be read as such
#: (#56): 1 is the sharp lower bound the engine already defaults to, and 3 and 8 bracket it by
#: roughly a half-round and a round-and-a-half of candidate spread on a 12-team board. They are
#: a SWEEP, and the report prints all of them side by side rather than picking a winner.
VDS_TOP_K = (3, 8)

#: The strategy axis. Each entry is what gets forwarded to simulate_full_draft, and the first is
#: the SHIPPED behaviour -- the control every other arm is read against. Without a control arm a
#: battery reports absolute numbers nobody can calibrate.
STRATEGIES = {
    "sharp_auto":     {"mode": "auto", "upside_rule": dr.UPSIDE_RULE_ROUND, "opponent_noise": None},
    "sharp_balanced": {"mode": "balanced", "upside_rule": dr.UPSIDE_RULE_ROUND, "opponent_noise": None},
    "sharp_upside":   {"mode": "upside", "upside_rule": dr.UPSIDE_RULE_ROUND, "opponent_noise": None},
    "crossing":       {"mode": "auto", "upside_rule": dr.UPSIDE_RULE_CROSSING, "opponent_noise": None},
    "noisy_k3":       {"mode": "auto", "upside_rule": dr.UPSIDE_RULE_ROUND,
                       "opponent_noise": {"top_k": VDS_TOP_K[0], "seed": VDS_SEED, "sharp_seats": []}},
    "noisy_k8":       {"mode": "auto", "upside_rule": dr.UPSIDE_RULE_ROUND,
                       "opponent_noise": {"top_k": VDS_TOP_K[1], "seed": VDS_SEED, "sharp_seats": []}},
}

CONTROL_STRATEGY = "sharp_auto"

#: Formats, and WHY each is here. A format battery covers formats; this one covers the places a
#: strategy change has somewhere to hide.
FORMATS = {
    "12T_ppr_K_DEF": "the K/DST concern -- the positions whose take pattern prompted this battery",
    "12T_ppr_SF": "superflex, where the #22 regression actually bit and the format battery missed it",
    "4WR_TE_PREMIUM": "the flex-share clamp (#153), where roster shape and valuation interact",
    "HEAVY_IDP": "the deepest pool, where upside mode has the most room to differ",
    "12T_ppr": "the plain control format -- a strategy effect here is not format-specific",
    "12T_ppr_SHORT_DRAFT": "8 rounds, so the round-triggered upside rule NEVER fires and the "
                           "crossing rule is the only thing that can reach upside at all",
}


def vds_matrix(base_scoring: dict | None = None) -> list[dict]:
    """strategy x format, as arms `run_vds_battery` can draft.

    Built FROM `draft_battery.league_matrix()` rather than by reconstructing leagues here. A
    hand-rebuilt capture is `#248`: `build_mock_league` overwrote `rec` from its own argument and
    an arm silently read a different rankings export than it reported.
    """
    by_label = {a["label"]: a for a in db.league_matrix(base_scoring)}
    missing = [f for f in FORMATS if f not in by_label]
    if missing:
        # REFUSED, not skipped. A VDS run that quietly dropped the superflex format would report
        # a clean strategy sweep while omitting the arm the battery exists for.
        raise ValueError(
            f"VDS formats not present in league_matrix: {missing}. The format battery's labels "
            f"have changed; fix FORMATS rather than letting the sweep run without them.")

    arms = []
    for fmt, why in FORMATS.items():
        base = by_label[fmt]
        for strategy, config in STRATEGIES.items():
            arms.append({
                "label": f"{fmt}__{strategy}",
                "format": fmt, "strategy": strategy, "why_format": why,
                "league": base["league"], "teams": base["teams"], "rounds": base["rounds"],
                "audit_roster_fill": base.get("audit_roster_fill", True),
                **config,
            })
    return arms
