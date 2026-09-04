"""#150, the final acceptance gate: reps, across formats, judged on ROSTER QUALITY.

test_draft_simulation.py already covers the MECHANICS -- determinism, no player drafted twice,
every pick is the board's real argmax, nothing mutated. Those say the simulator is honest. They
say nothing about whether the rosters it produces are any good, and that is the question this
module exists to answer:

    "make sure this thing has reps on it, and nothing wonky happens. and, more importantly,
     that it's building good, defensible, reasonable, rosters"

WHAT MAKES AN AUDIT ADMISSIBLE HERE, and it is the constraint that shaped every one below:
NO INVENTED THRESHOLDS (#56). "A reasonable roster" is a judgement, and a judgement encoded as
a constant is an assertion wearing a measurement's clothes. So every audit is one of two kinds:

  STRUCTURAL -- the league's own rules decide, and the engine either satisfied them or did not.
    "Every dedicated starting slot is filled by the end of a full-length draft" needs no number
    from me; roster_positions supplies it.

  COMPARATIVE -- two formats drafted from the SAME pool, where the direction of the difference
    is the claim and its size is nobody's opinion. "Superflex rosters hold more QBs than 1QB
    rosters" is falsifiable without anyone deciding how many QBs is right.

Anything that would need a magnitude I picked is REPORTED, not asserted -- it lands in the
report's distributions for a person to read, which is the same split roster_diagnostics already
uses between a measurement and a verdict.

DELIBERATELY NOT AUDITED, so the report is not read as covering it:
  * Whether the VALUATION is correct. Every chair uses the same engine, so a battery cannot
    detect a systematic mispricing -- it would produce twelve consistently wrong rosters and
    every structural check would pass. That is #52's job (a blind adversarial pass) and #143's
    (the forward record), and neither is replaceable by more simulation.
  * Anything behind a human decision. Chairs take the board's argmax; a real drafter reaches.
"""

from __future__ import annotations

import collections
from typing import Any, Optional

import draft_room as dr
import draft_simulation
import draft_strategy as ds
import lineup_optimizer as lo
from player_universe import FANTASY_POSITIONS

#: Slot labels that hold a player but are not a startable position.
NON_STARTING_SLOTS = {"BN", "IR", "TAXI"}


def _starting_slots(roster_positions: list[str]) -> list[str]:
    return [s for s in (roster_positions or []) if s not in NON_STARTING_SLOTS]


def league_matrix() -> list[dict]:
    """Every format the battery drafts, as {label, league, teams, rounds}.

    Chosen to span the axes a real league varies on -- size, scoring, superflex, TE premium,
    dynasty vs redraft -- plus two shapes carried deliberately because open register items
    predict something specific about them:

      4WR_TE_PREMIUM -- #153. need_bonus's own cap collapses "zero of my four WRs" and "one of
        my four" onto the same 12.0 here, measured on 18.2% of candidate rows. If that damages
        roster construction it should show up in this format's WR counts and nowhere else.
      HEAVY_IDP -- #152. The trade_value fallback's ceiling is partly a unit artifact, so IDP
        will be taken LATE relative to real roster demand. That is expected, it is #51's supply
        defect seen from the arithmetic side, and the report says so rather than rediscovering
        it as an anomaly.
    """
    out: list[dict] = []
    for teams in (8, 10, 12, 14):
        for scoring in ("standard", "half_ppr", "ppr"):
            for superflex in (False, True):
                league = dr.build_mock_league(teams=teams, superflex=superflex,
                                              scoring=scoring, te_premium=False, dynasty=True)
                out.append({
                    "label": f"{teams}T_{scoring}{'_SF' if superflex else ''}",
                    "league": league, "teams": teams,
                    "rounds": len(league["roster_positions"]),
                })
    # TE premium and redraft, on one size, so the axis is isolated rather than crossed with
    # everything above (which would quadruple runtime to re-measure the same thing).
    for te_premium, dynasty in ((True, True), (False, False), (True, False)):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                      te_premium=te_premium, dynasty=dynasty)
        out.append({
            "label": f"12T_ppr{'_TEP' if te_premium else ''}{'_dynasty' if dynasty else '_redraft'}",
            "league": league, "teams": 12, "rounds": len(league["roster_positions"]),
        })
    # The two shapes build_mock_league cannot express, both carried for a named reason above.
    custom = {
        "4WR_TE_PREMIUM": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "WR", "TE", "TE", "FLEX"]
                                + ["BN"] * 6,
            "scoring_settings": {"rec": 1.0, "bonus_rec_te": dr.MOCK_TE_PREMIUM_BONUS},
            "total_rosters": 12, "settings": {"type": 2},
        },
        "HEAVY_IDP": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                 "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
            "scoring_settings": {"rec": 1.0},
            "total_rosters": 12, "settings": {"type": 2},
        },
        "LIGHT_IDP": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "IDP_FLEX"]
                                + ["BN"] * 6,
            "scoring_settings": {"rec": 1.0},
            "total_rosters": 12, "settings": {"type": 2},
        },
    }
    for label, league in custom.items():
        out.append({"label": label, "league": league, "teams": league["total_rosters"],
                    "rounds": len(league["roster_positions"])})

    # MODE IS AN AXIS, and until this was added the battery barely varied it. Every format
    # above runs mode="auto", which switches to upside scoring only at
    # UPSIDE_MODE_DEFAULT_ROUND (15) -- and most formats here are 14 rounds, so auto never
    # reached upside at all. The battery would have reported "modes covered" while exercising
    # one. Measured on the smoke run before this was fixed: 0 picks with a growth_signal across
    # 280 picks in two formats.
    #
    # So one 12-team format is run in each mode explicitly. upside is the one that matters:
    # it is the only path that computes growth_signal, it is what every auto-drafted opponent
    # falls into late, and #115 records that a human board never reaches it -- which makes the
    # simulation the ONLY place its behaviour is observable at all.
    base = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                               te_premium=False, dynasty=True)
    for mode in ("balanced", "upside"):
        out.append({"label": f"12T_ppr_mode_{mode}", "league": base, "teams": 12,
                    "rounds": len(base["roster_positions"]), "mode": mode})
    return out


def _position_of(players_db: dict, player_id: str) -> Optional[str]:
    info = players_db.get(str(player_id)) or {}
    return info.get("position")


# --------------------------------------------------------------------------------------
# STRUCTURAL AUDITS -- the league's own rules decide, so no number here is mine.
# --------------------------------------------------------------------------------------

def unfilled_starting_slots(trajectory, league: dict, players_db: dict) -> list[dict]:
    """THE defensibility bar, and the whole reason this module exists.

    A full-length draft gives every chair exactly as many picks as it has roster slots. A roster
    that finishes unable to field a legal starting lineup did not merely draft suboptimally --
    it drafted something it cannot play, which is the failure mode #87 measured when need_bonus
    was ablated (four QBs in a one-QB league).

    Solved as the real assignment problem via lineup_optimizer rather than by counting
    positions, because counting gets FLEX chains wrong: a spare RB legitimately fills a FLEX
    and frees a WR upward, and a naive per-position tally reports a hole where the solver finds
    none. (That distinction was measured while building bye_collision -- the naive reading
    predicted a cost of 16 where the solver found 5.)
    """
    slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
    findings = []
    for roster_id, player_ids in sorted(trajectory.final_rosters().items()):
        players = []
        for pid in player_ids:
            info = players_db.get(str(pid)) or {}
            players.append({"id": str(pid), "value": 1.0,
                            "eligible": set(info.get("fantasy_positions")
                                            or ([info["position"]] if info.get("position") else []))})
        solved = lo.optimize_lineup(players, slots)
        # optimize_lineup returns only the pairs it actually made -- an unfillable slot is
        # filtered back out rather than returned empty (see its docstring), so the holes are the
        # DIFFERENCE against the slot list, never a scan of the assignments for a missing id.
        assigned = {a["slot_id"] for a in solved["assignments"] if a.get("player_id")}
        filled = len(assigned)
        if filled < len(slots):
            empty = [slot["label"] for slot in slots if slot["slot_id"] not in assigned]
            findings.append({
                "audit": "unfilled_starting_slots", "roster_id": roster_id,
                "filled": filled, "required": len(slots), "empty_slots": empty,
                "roster_size": len(player_ids),
            })
    return findings


def unpriced_picks(trajectory) -> list[dict]:
    """A chair took a player the engine could not price. Every pick is candidates[0] by
    team_acquisition_value, so an unpriced choice means the ordering fell through to a
    tiebreak with no value behind it at all -- the pathological end of #114."""
    findings = []
    for pick in trajectory.picks:
        row = next((c for c in pick.snapshot["candidates"] if c["id"] == pick.chosen_player_id), None)
        if row is None:
            findings.append({"audit": "unpriced_picks", "pick": pick.pick_label,
                             "reason": "chosen player is absent from its own retained board"})
        elif row.get("tav") is None:
            findings.append({"audit": "unpriced_picks", "pick": pick.pick_label,
                             "player": row.get("name"), "reason": "chosen with tav=None"})
    return findings


def undraftable_positions(trajectory, league: dict, players_db: dict) -> list[dict]:
    """A roster holding a position the league offers no slot for -- not even a flex share.
    Structural: the pool is supposed to be filtered to usable positions upstream, so any hit
    here is a filter that leaked, never a judgement about roster balance."""
    startable = {p for p, n in dr.starter_slot_counts(league.get("roster_positions") or []).items() if n > 0}
    findings = []
    for roster_id, player_ids in sorted(trajectory.final_rosters().items()):
        for pid in player_ids:
            position = _position_of(players_db, pid)
            if position and position not in startable:
                findings.append({"audit": "undraftable_positions", "roster_id": roster_id,
                                 "player_id": str(pid), "position": position})
    return findings


def duplicate_picks(trajectory) -> list[dict]:
    seen, findings = set(), []
    for pick in trajectory.picks:
        if pick.chosen_player_id in seen:
            findings.append({"audit": "duplicate_picks", "pick": pick.pick_label,
                             "player_id": pick.chosen_player_id})
        seen.add(pick.chosen_player_id)
    return findings


def structural_findings(trajectory, league: dict, players_db: dict) -> list[dict]:
    """Every structural audit, in one call. A finding here is a DEFECT, not an observation."""
    return (unfilled_starting_slots(trajectory, league, players_db)
            + unpriced_picks(trajectory)
            + undraftable_positions(trajectory, league, players_db)
            + duplicate_picks(trajectory))


# --------------------------------------------------------------------------------------
# REPORTED DISTRIBUTIONS -- no verdict, because a verdict would need a number I chose.
# --------------------------------------------------------------------------------------

def roster_shape(trajectory, players_db: dict) -> dict[str, dict[str, int]]:
    """roster_id -> {position: count}. The raw material for every comparative claim below."""
    out: dict[str, dict[str, int]] = {}
    for roster_id, player_ids in trajectory.final_rosters().items():
        counts: collections.Counter = collections.Counter()
        for pid in player_ids:
            position = _position_of(players_db, pid)
            if position:
                counts[position] += 1
        out[roster_id] = dict(counts)
    return out


def mean_position_count(trajectory, players_db: dict, position: str) -> float:
    shapes = roster_shape(trajectory, players_db)
    if not shapes:
        return 0.0
    return sum(s.get(position, 0) for s in shapes.values()) / len(shapes)


def first_round_taken(trajectory, players_db: dict, position: str) -> Optional[int]:
    """The round a position first comes off the board -- the comparative handle for "does this
    format pull this position earlier", which is a direction rather than a magnitude."""
    for pick in trajectory.picks:
        if _position_of(players_db, pick.chosen_player_id) == position:
            return pick.round
    return None


def tav_margin_profile(trajectory) -> dict:
    """How decisively each pick was made: the gap between the chosen candidate and the runner-up.

    #114 measured a real late-draft collapse -- 27.8% of an 18-round draft decided by a
    player-id tiebreak once every remaining candidate priced identically. Reported rather than
    asserted, because "how thin is too thin" is exactly the judgement this module refuses to
    encode. A zero margin is not automatically wrong; a HIGH RATE of them means the ordering
    stopped carrying information, and a person should see the number.
    """
    margins, zero_by_round = [], collections.Counter()
    total_by_round: collections.Counter = collections.Counter()
    for pick in trajectory.picks:
        rows = [c for c in pick.snapshot["candidates"] if c.get("tav") is not None]
        total_by_round[pick.round] += 1
        if len(rows) < 2:
            continue
        ordered = sorted((c["tav"] for c in rows), reverse=True)
        margin = round(ordered[0] - ordered[1], 4)
        margins.append(margin)
        if margin <= 0:
            zero_by_round[pick.round] += 1
    return {
        "picks_measured": len(margins),
        "zero_margin_picks": sum(zero_by_round.values()),
        "zero_margin_share": (sum(zero_by_round.values()) / len(margins)) if margins else None,
        "zero_margin_by_round": dict(sorted(zero_by_round.items())),
        "picks_by_round": dict(sorted(total_by_round.items())),
        "median_margin": (sorted(margins)[len(margins) // 2] if margins else None),
    }


def qualifier_profile(trajectory) -> dict:
    """#138's two carried qualifiers, now that picks record them: what KIND of number won.

    A pick resting on the pre-draft anchor is a weaker claim than one resting on live starter
    demand, and a report that cannot tell them apart is the exact blindness #138 repaired.
    """
    bases = collections.Counter(p.chosen_replacement_basis for p in trajectory.picks)
    # `is not None` and `> 0` are SEPARATE counts, and conflating them is the exact defect this
    # repository forbids everywhere else -- caught here in the battery's own reporting, where a
    # truthiness test read a measured growth of 0.0 as "no growth measured". Balanced-mode picks
    # have growth_signal None because the quantity is never computed; an upside pick can
    # legitimately measure 0.0, and those are different facts about the draft.
    measured = [p.chosen_growth_signal for p in trajectory.picks
                if p.chosen_growth_signal is not None]
    positive = [value for value in measured if value > 0]
    return {
        "replacement_basis": {str(k): v for k, v in sorted(bases.items(), key=lambda kv: str(kv[0]))},
        "picks_with_growth_measured": len(measured),
        "picks_with_growth_above_zero": len(positive),
        "max_growth": max(measured) if measured else None,
    }


def audit_trajectory(trajectory, league: dict, players_db: dict) -> dict:
    """One trajectory, fully judged and fully described."""
    return {
        "label": trajectory.config.get("label", ""),
        "picks": len(trajectory.picks),
        "rosters": len(trajectory.final_rosters()),
        "findings": structural_findings(trajectory, league, players_db),
        "shape": roster_shape(trajectory, players_db),
        "margins": tav_margin_profile(trajectory),
        "qualifiers": qualifier_profile(trajectory),
        "regimes": dict(collections.Counter(p.decision_regime for p in trajectory.picks)),
    }


def run_battery(merger, players_db: dict, matrix: Optional[list[dict]] = None,
                *, mode: str = "auto") -> list[dict]:
    """Draft every format in the matrix and audit each one.

    pick_order is generated per format rather than reused, since team count varies -- and it is
    a real input, not a seed: this whole battery contains no randomness, so re-running it must
    reproduce byte-identical trajectories (test_draft_simulation already pins that contract for
    one draft; here it holds across the matrix).
    """
    results = []
    for entry in matrix if matrix is not None else league_matrix():
        roster_ids = [str(i) for i in range(1, entry["teams"] + 1)]
        pick_order = ds.generate_pick_order(roster_ids, entry["rounds"], "snake")
        trajectory = draft_simulation.simulate_full_draft(
            merger, players_db, entry["league"], pick_order,
            mode=entry.get("mode", mode), config_label=entry["label"])
        audited = audit_trajectory(trajectory, entry["league"], players_db)
        audited["teams"] = entry["teams"]
        audited["rounds"] = entry["rounds"]
        results.append(audited)
    return results
