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

import json

import collections
from pathlib import Path
from typing import Any, Optional

import data_merger as dm
import draft_room as dr
import league_config as lc
import draft_simulation
import draft_strategy as ds
import lineup_optimizer as lo
from player_universe import FANTASY_POSITIONS, player_eligible_positions

#: Q1 of the slot vocabulary, imported rather than restated. This module used to carry its own
#: identical copy under this same name; league_config is the one home (#126), and it also
#: answers the SECOND question -- which slots a startup draft fills -- that this copy's
#: existence made look already-answered. See league_config.draftable_slots.
NON_STARTING_SLOTS = lc.NON_STARTING_SLOTS
_starting_slots = lc.starting_slots


def league_matrix(base_scoring: dict | None = None) -> list[dict]:
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
    # #213: EVERY ARM'S RULEBOOK IS THE REAL ONE, with rec/te-premium overlaid. A synthetic
    # one-key dict made 27 of these arms measure a league in which quarterbacks score nothing.
    base = dict(base_scoring or {})
    out: list[dict] = []
    for teams in (8, 10, 12, 14):
        for scoring in ("standard", "half_ppr", "ppr"):
            for superflex in (False, True):
                league = dr.build_mock_league(teams=teams, superflex=superflex,
                                              scoring=scoring, te_premium=False, dynasty=True,
                                              base_scoring=base)
                rounds = len(lc.draftable_slots(league["roster_positions"]))
                # The engine cannot know the round count unless the league says so (#161).
                # Carrying it here is what makes the battery measure the repaired path.
                league["draft_rounds"] = rounds
                out.append({
                    "label": f"{teams}T_{scoring}{'_SF' if superflex else ''}",
                    "league": league, "teams": teams, "rounds": rounds,
                })
    # TE premium and redraft, on one size, so the axis is isolated rather than crossed with
    # everything above (which would quadruple runtime to re-measure the same thing).
    for te_premium, dynasty in ((True, True), (False, False), (True, False)):
        league = dr.build_mock_league(teams=12, superflex=False, scoring="ppr",
                                      te_premium=te_premium, dynasty=dynasty, base_scoring=base)
        rounds = len(lc.draftable_slots(league["roster_positions"]))
        league["draft_rounds"] = rounds
        out.append({
            "label": f"12T_ppr{'_TEP' if te_premium else ''}{'_dynasty' if dynasty else '_redraft'}",
            "league": league, "teams": 12, "rounds": rounds,
        })
    # The two shapes build_mock_league cannot express, both carried for a named reason above.
    custom = {
        "4WR_TE_PREMIUM": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "WR", "WR", "TE", "TE", "FLEX"]
                                + ["BN"] * 6,
            "scoring_settings": {**base, "rec": 1.0,
                                 "bonus_rec_te": dr.MOCK_TE_PREMIUM_BONUS},
            "total_rosters": 12, "settings": {"type": 2},
        },
        "HEAVY_IDP": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX",
                                 "DL", "DL", "LB", "LB", "DB", "DB"] + ["BN"] * 5,
            # The IDP arm above all others needs the real rulebook: {"rec": 1.0} carries no
            # idp_* key at all, so every LB/DB/DL scored 0.0 and the arm's 14 findings were
            # read as an IDP SUPPLY gap (#210) when 299 IDP stat lines price under real rules.
            "scoring_settings": {**base, "rec": 1.0},
            "total_rosters": 12, "settings": {"type": 2},
        },
        "LIGHT_IDP": {
            "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "IDP_FLEX"]
                                + ["BN"] * 6,
            "scoring_settings": {**base, "rec": 1.0},
            "total_rosters": 12, "settings": {"type": 2},
        },
    }
    for label, league in custom.items():
        league["draft_rounds"] = len(league["roster_positions"])
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
    mode_base = dr.build_mock_league(base_scoring=base_scoring, teams=12, superflex=False, scoring="ppr",
                               te_premium=False, dynasty=True)
    mode_base["draft_rounds"] = len(mode_base["roster_positions"])
    for mode in ("balanced", "upside"):
        out.append({"label": f"12T_ppr_mode_{mode}", "league": mode_base, "teams": 12,
                    "rounds": len(mode_base["roster_positions"]), "mode": mode})

    # A REAL CAPTURED LEAGUE, AS A CONFIGURATION POINT -- NOT AS THE CANONICAL ONE (#251).
    #
    # Every arm above is built from `fixtures/sleeper_capture.json` with a rec/te-premium
    # overlay, so the matrix covers exactly the region its own base rulebook occupies:
    # `config_space.coverage` measures it at 16 varied axes of 91, and reports ZERO uncovered
    # coordinates for the fixture -- a tautology, since the matrix is built from it.
    #
    # Fourth and Forever carries 21 coordinates no arm here produces, including `rec_fd`,
    # `rush_fd`, `bonus_rec_te 0.25`, `pass_td 4` (every other arm scores 6) and TAXI slots.
    # `#250` measured what that costs: the same roster under the two rulebooks inverts the
    # verdict, 3/12 -0.84% against 10/12 +1.04%. A 33-arm run was never universal evidence
    # about the engine; it was evidence about one region.
    #
    # SUPPLIED DIRECTLY, never through build_mock_league. That function overwrites `rec` from
    # its own `scoring` argument, which is precisely how #248's arm B came to run at rec 1.0
    # while claiming to carry F&F's rulebook -- and `rec` selects the rankings EXPORT, so the
    # arm read a different file than it reported. A captured league enters as itself or not at
    # all.
    #
    # NEITHER LEAGUE IS CANONICAL. This is one more coordinate, and the point of adding it is
    # that the invariants must hold here too -- not that its outcomes are the right ones.
    # THE LEAGUE THIS SYSTEM IS ACTUALLY USED ON, which no arm above carries.
    #
    # Every arm above is built through build_mock_league, which emits no K, no DEF and no IDP
    # slot. `format_axes_exercised` now reports the consequence in the battery's own output --
    # `has_kicker` and `has_defense` constant False across all 34 arms -- but reporting a gap is
    # not covering it. Measured on this shape by two independent passes: 31 kickers drafted onto
    # 12 one-K rosters, 102 IDP players into 24 IDP slots, round 21 twelve consecutive DBs, and
    # `structural_findings` = 0 throughout, because every one of those rosters is LEGAL.
    #
    # Supplied directly rather than through build_mock_league, for the reason the F&F block
    # below gives: that function overwrites `rec` from its own `scoring` argument, and `rec`
    # selects the rankings export, so an arm built that way reads a different file than it
    # reports. A captured league enters as itself or not at all.
    #
    # NOT CANONICAL, same as F&F. It is one more coordinate -- the point is that the invariants
    # must hold here too, not that its outcomes are the right ones.
    owner_path = Path("data/fixtures/sleeper_capture.json")
    if owner_path.exists():
        owner_capture = json.loads(owner_path.read_text(encoding="utf-8"))
        owner_league = owner_capture.get("league_shape") or owner_capture.get("league")
        if owner_league and owner_league.get("roster_positions"):
            owner_arm = dict(owner_league)
            owner_rounds = len(lc.draftable_slots(owner_arm["roster_positions"]))
            owner_arm["draft_rounds"] = owner_rounds
            out.append({"label": "CAPTURE_owner_league", "league": owner_arm,
                        "teams": int(owner_arm.get("total_rosters") or 12),
                        "rounds": owner_rounds})

    capture_path = Path("data/league_captures/fourth_and_forever.json")
    if capture_path.exists():
        cap = json.loads(capture_path.read_text(encoding="utf-8"))
        ff = {
            "roster_positions": cap["roster_positions"],
            "scoring_settings": {k: v["value"] for k, v in cap["scoring_settings_observed"].items()},
            "total_rosters": 12,
            "settings": {"type": 2},
        }
        ff_rounds = len(lc.draftable_slots(ff["roster_positions"]))
        ff["draft_rounds"] = ff_rounds
        out.append({"label": "CAPTURE_fourth_and_forever", "league": ff, "teams": 12,
                    "rounds": ff_rounds})

    # THE ARM THAT MAKES #161 FALSIFIABLE, and the reason it did not exist before is the
    # finding. Every format above sets rounds = len(roster_positions), which is precisely the
    # equation feasibility_first was guessing -- so all 5,244 picks of #150 satisfied the
    # assumption under test and the battery was structurally incapable of contradicting it.
    # A harness that fixes a variable cannot falsify a defect in that variable.
    #
    # rounds < slots is the ORDINARY shape, not an exotic one: benches are filled from waivers
    # rather than drafted, and this repo's own real league is 33 roster positions against 29
    # draftable. Here a 20-slot roster is drafted for 12 rounds, so eight bench seats are never
    # picked and the backstop's "picks left" is wrong by eight unless it is told the truth.
    # THE ARM THAT CLOSES has_defense (#52, ruled to block v2-freeze).
    #
    # Every arm above resolves `has_defense` to False: build_mock_league emits no DEF slot, and
    # neither captured league has one -- the owner's own league carries a kicker but no team
    # defense, which is exactly why `has_kicker` varied at one arm while this axis varied at
    # none. The matrix advertised a dimension it did not cross, so no battery result was ever
    # evidence about drafting a defense, and `format_axes_exercised` said so in its own output.
    #
    # NOT AN EXOTIC COORDINATE. QB/RB/RB/WR/WR/TE/FLEX/K/DEF is the most ordinary roster in
    # fantasy football, and the battery did not have it. That is the finding, not the fix.
    #
    # EXACTLY ONE THING DIFFERS from the 12T ppr arm above: the two slots. Same base rulebook,
    # same size, same scoring, same superflex and dynasty settings -- so anything this arm shows
    # that its sibling does not is attributable to the slots and nothing else. Changing three
    # coordinates at once would have made it a new format rather than a new measurement.
    #
    # Population checked before the arm was added, because an arm with an unfillable slot is a
    # finding about the capture rather than coverage of the axis: the capture carries all 32
    # team defenses, and every one of them prices, on `live_starter_demand`.
    kdef = dr.build_mock_league(base_scoring=base_scoring, teams=12, superflex=False,
                                scoring="ppr", te_premium=False, dynasty=True)
    kdef["roster_positions"] = list(kdef["roster_positions"]) + ["K", "DEF"]
    kdef_rounds = len(lc.draftable_slots(kdef["roster_positions"]))
    kdef["draft_rounds"] = kdef_rounds
    out.append({"label": "12T_ppr_K_DEF", "league": kdef, "teams": 12, "rounds": kdef_rounds})

    short = dr.build_mock_league(base_scoring=base_scoring, teams=12, superflex=False, scoring="ppr",
                                 te_premium=False, dynasty=True)
    short_rounds = max(len(short["roster_positions"]) - 8, 8)
    short["draft_rounds"] = short_rounds
    out.append({"label": "12T_ppr_SHORT_DRAFT", "league": short, "teams": 12,
                "rounds": short_rounds, "audit_roster_fill": False})
    return out


def league_format_hint(league: dict) -> dict:
    """The {scoring, superflex, te_premium} triple set_league_format discriminates on.

    Derived from the league's own settings by the same rules sleeper_client.league_format_summary
    uses, rather than carried alongside each matrix entry -- a hint that could disagree with the
    league it describes is a second source of truth for the same fact.
    """
    scoring_settings = league.get("scoring_settings") or {}
    roster_positions = league.get("roster_positions") or []
    rec = scoring_settings.get("rec", 0)
    return {
        "scoring": "ppr" if rec >= 1 else ("half_ppr" if rec == 0.5 else "standard"),
        "superflex": roster_positions.count("SUPER_FLEX") > 0 or roster_positions.count("QB") > 1,
        "te_premium": scoring_settings.get("bonus_rec_te", 0) > 0,
    }


def _position_of(players_db: dict, player_id: str) -> Optional[str]:
    """The RAW Sleeper position, deliberately -- and that is a latent issue, recorded here
    rather than changed (#52 phase 8).

    `player_universe.player_position` buckets an IDP sub-position into the slot a league
    actually offers ("FS" -> "DB"); this returns "FS". `roster_shape` and `first_round_taken`
    both read it, so every battery report's `shape` counts sub-positions rather than roster
    buckets in IDP formats.

    NOT changed here because the five committed batteries were produced with this reading, and
    switching it would make new reports incomparable with them on exactly the axis IDP arms
    exist to measure. `undraftable_positions` no longer uses it for its verdict -- that guard
    asks `player_eligible_positions` now -- so the remaining consumers are descriptive rather
    than judgemental, which is the safe half to leave."""
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
    """A roster holding a player NO slot in this league can start -- not even a flex share.
    Structural: the pool is supposed to be filtered to usable positions upstream, so any hit
    here is a filter that leaked, never a judgement about roster balance.

    ASKED THROUGH THE SAME RULE THE POOL ADMITS ON (#126), which it was not until now. This
    read one PRIMARY position per player and flagged it if that bucket had no slot, while
    `build_available_pool` admits on `fantasy_positions` -- so the guard and the filter it
    polices were asking different questions, and the guard's was the wrong one.

    It cost a false positive on a real capture: Travis Hunter is `position: "DB"` with
    `fantasy_positions: ["DB", "WR"]`, and a 12-team league starting QB/RB/WR/TE rostered him
    legitimately as a WR. The audit called that a leaked filter. A structural audit reporting a
    DEFECT where the engine did the right thing is worse than one that stays quiet, because
    this file's own docstring says "a finding here is a DEFECT, not an observation" and a
    reader is entitled to believe it.

    A player is undraftable only when NONE of his eligible positions can be started."""
    startable = {p for p, n in dr.starter_slot_counts(league.get("roster_positions") or []).items() if n > 0}
    findings = []
    for roster_id, player_ids in sorted(trajectory.final_rosters().items()):
        for pid in player_ids:
            eligible = player_eligible_positions(players_db.get(str(pid)) or {})
            if eligible and not (eligible & startable):
                findings.append({"audit": "undraftable_positions", "roster_id": roster_id,
                                 "player_id": str(pid),
                                 "position": _position_of(players_db, pid),
                                 "eligible": sorted(eligible)})
    return findings


def duplicate_picks(trajectory) -> list[dict]:
    seen, findings = set(), []
    for pick in trajectory.picks:
        if pick.chosen_player_id in seen:
            findings.append({"audit": "duplicate_picks", "pick": pick.pick_label,
                             "player_id": pick.chosen_player_id})
        seen.add(pick.chosen_player_id)
    return findings


def unfieldable_depth(trajectory, league: dict, players_db: dict) -> list[dict]:
    """A roster carrying more of a position than it can EVER field. The audit that would have
    caught the nine-defense roster (`evidence/kdst_streaming/ROOT_CAUSE.md`).

    THE FOUR EXISTING AUDITS ALL PASS ON THAT ROSTER. Every starting slot was filled, every pick
    was priced, DEF is a draftable position, and no player was duplicated. `roster_shape` and
    `mean_position_count` recorded DEF: 9 in a one-DEF league and returned no verdict, on the
    stated grounds that a verdict would need a number somebody chose.

    IT DOES NOT, and that is the whole reason this is an audit rather than another distribution.
    The ceiling is derived from two league facts and nothing else:

      - A position that reaches only slots which admit IT ALONE can start exactly `slots(P)`
        players in any week. There is no flex chain to absorb a spare, so the surplus is not
        depth -- it is a roster spot that provably cannot be fielded.
      - Every team has exactly ONE bye week, so exactly one backup is needed to cover it.

    Ceiling = `slots(P) + 1`. Derived, not calibrated (`#56`), and a BOUND rather than a
    threshold: it is the largest count that is not provably wasted, so it can only ever be
    tripped by a roster that is demonstrably carrying an unplayable player.

    FLEX-ELIGIBLE POSITIONS ARE EXEMPT, and must be. A spare RB fills a FLEX and frees a WR
    upward; a fourth WR in a two-FLEX league is ordinary depth. Asked through the SAME slot
    eligibility the optimizer solves on (`#126`), never a hand-listed set of "bench positions" --
    a second reading of which positions have flex reach is exactly how `undraftable_positions`
    went wrong before it was repaired.
    """
    slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
    # A position is flex-reachable if ANY slot that admits it admits something else too.
    dedicated: dict[str, int] = {}
    flexible: set[str] = set()
    for slot in slots:
        eligible = set(slot.get("eligible") or ())
        if len(eligible) == 1:
            position = next(iter(eligible))
            dedicated[position] = dedicated.get(position, 0) + 1
        else:
            flexible |= eligible

    findings = []
    for roster_id, counts in sorted(roster_shape(trajectory, players_db).items()):
        for position, held in sorted(counts.items()):
            if position in flexible or position not in dedicated:
                continue
            # +1 for the bye week every team has exactly one of. Nothing else is added.
            ceiling = dedicated[position] + 1
            if held > ceiling:
                findings.append({
                    "audit": "unfieldable_depth", "roster_id": roster_id,
                    "position": position, "held": held, "startable_per_week": dedicated[position],
                    "ceiling": ceiling, "unfieldable": held - ceiling,
                })
    return findings


def structural_findings(trajectory, league: dict, players_db: dict,
                        *, audit_roster_fill: bool = True) -> list[dict]:
    """Every structural audit, in one call. A finding here is a DEFECT, not an observation.

    `audit_roster_fill=False` for a format whose draft is SHORTER than its roster. That is not
    an exemption for convenience: a 12-round draft of a 20-slot roster cannot fill 20 slots, so
    an unfilled-slot finding there would report arithmetic as an engine defect. The other four
    audits still run -- a short draft can still price nothing, draft an impossible position,
    hoard a position it cannot field, or take the same player twice, and those remain defects at
    any length."""
    findings = (unpriced_picks(trajectory)
                + undraftable_positions(trajectory, league, players_db)
                + unfieldable_depth(trajectory, league, players_db)
                + duplicate_picks(trajectory))
    if audit_roster_fill:
        findings = unfilled_starting_slots(trajectory, league, players_db) + findings
    return findings


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


def reference_values(merger, players_db: dict, league: dict,
                     sleeper_projections: Optional[dict[str, dict]] = None,
                     sleeper_basis: str = dr.SLEEPER_BASIS_WEEKLY) -> dict[str, float]:
    """player_id -> universal_value on the PRE-DRAFT board. ONE RULER for the whole format.

    Emphatically NOT each player's value at the moment he was taken. Those numbers are measured
    against different board states, and comparing them is the moving-ruler defect #75/#76 found,
    where the reference carried 94.5% of all bpa movement. #74 removed that scale, so values are
    far more stable now -- but "far more stable" is not "comparable", and a strength number that
    sums across fifteen different board states would be measuring the draft's progress as much
    as the roster.
    """
    # THE RULER AND THE DRAFT MUST BE PRICED THE SAME WAY (#204). run_battery passes whatever
    # it passed to simulate_full_draft; a ruler built off vendor-only points while the draft
    # itself ran scoring-aware would make every value-against-the-ruler number in the audit a
    # comparison between two different quantities -- worse than the consistent-but-wrong state
    # this replaced, because it would look measured.
    board = dr.compute_draft_board(merger, players_db, [], my_roster_id=None,
                                   league=league, mode="balanced",
                                   sleeper_projections=sleeper_projections,
                                   sleeper_basis=sleeper_basis)
    return {str(row["player_id"]): row["universal_value"] for row in board
            if row.get("universal_value") is not None}


#: Which quantity answers "what is this roster worth". Named rather than implied, because the
#: two candidates differ in KIND and the wrong one was reported for the life of this battery.
ROSTER_WORTH_BASIS = "total_value: universal_value is an asset LEVEL, so roster worth is what "\
                     "the chair OWNS; starter_value sums that level over a starting lineup and "\
                     "measures positional breadth instead (#211)"


def roster_strength(trajectory, league: dict, players_db: dict,
                    values: dict[str, float]) -> dict:
    """What each roster is actually WORTH, not merely whether it is legal.

    Three numbers per chair, all on the shared pre-draft ruler:
      total_value   -- what the chair OWNS. THIS IS THE ROSTER-WORTH NUMBER (see
        ROSTER_WORTH_BASIS), and saying so is a correction, not a convention.
      starter_value -- the optimal legal lineup's total, solved with REAL values (unlike
        unfilled_starting_slots, which passes 1.0 to ask a pure feasibility question). It
        answers "can this roster field a lineup, and what does doing so cost", which is a real
        question and NOT the same one.
      bench_value   -- everything else. Depth, and the price paid for it.

    #211: starter_value WAS DESCRIBED HERE AS "the roster-quality number: it is what the team
    actually fields", and that was a category error this docstring helped hide for the life of
    this battery. universal_value is an asset LEVEL -- what a player is worth to OWN -- not a
    rate that starting him realises, so summing the started subset does not measure quality.
    Worse, it does not even measure it badly-but-monotonically: 83.8% of a typical pool's
    universal_value is NEGATIVE (min -319.22, median -30.74, max +79.03) and optimize_lineup
    has no "leave the slot empty" move, so a roster thin at a position is FORCED to start deep
    negatives. Measured directly: one +50 WR and one -80 RB against a WR slot and an RB slot
    returns -30, not +50. The battery duly produced `12T_ppr_mode_upside starters -205.4`.
    What starter_value therefore ranks is POSITIONAL BREADTH -- who is forced to start the
    fewest negatives -- which is a property of how a chair spread its picks, not of how good
    they were. `forced_negative_starters` now travels with it so the contamination is visible
    at the point of reading, and total_value carries the roster-worth question instead.

    SCOPE, deliberately narrow: NO FINDING CHANGES. The battery's findings are legality checks
    (unfilled_starting_slots and friends) and none of them has ever read starter_value; this
    corrects a REPORTED LINE, not a verdict. The numbers in the committed evidence files were
    produced by the code as it stood and are not retroactively altered -- only their reading is.

    UNPRICED PLAYERS ARE COUNTED, AND -- CONTRARY TO WHAT THIS DOCSTRING USED TO CLAIM -- THEY
    ARE ALSO ENTERED AT 0.0. The count is real (`unpriced_players` travels with every roster),
    and that half was always true. The other half was not: `values.get(str(pid), 0.0)` below
    admits an unpriced player to the lineup solve valued at zero, so the zero lands in
    total_value, in bench_value, and in the optimizer's own choice of who starts.

    This is #165's OPEN question -- what an unpriced player is worth inside a lineup solve --
    answered here, silently, as 0.0. That is the option roster_diagnostics rejected on the
    record, and draft_room._team_roster_players measured what it does: "optimize_lineup
    maximises total value, so a zero-value player is always the first benched and never holds a
    slot against contention", i.e. behaviourally near-identical to dropping him while buying
    "nothing but false confidence". starter_value is therefore a floor for a DIFFERENT reason
    than this docstring gave, and the floor is not clean.

    NOT REPAIRED HERE ON PURPOSE. Choosing what an unpriced player is worth in a solve IS #165,
    which the owner has reserved pending an investigation into whether rank, tier or positional
    context can carry him without inventing a price. Fixing it here would answer a reserved
    question by implementation. The comment is corrected because a docstring asserting the
    opposite of its code is worse than none -- it is what let this survive: a reader checking
    the absence contract would have read the old sentence and moved on. Registered as #168.

    WHERE IT BITES: any roster holding unpriced players, i.e. the IDP arms -- 339 of 415 IDP
    baseline rows carry no trade value. The starter-value SPREAD this function names below as
    "the readable signal" is the number most affected by it.

    Reported, never asserted. "Is 812 a good starter_value" needs a threshold nobody has
    argued for; the SPREAD across chairs is the readable signal, and it is comparative.
    """
    slots = lo.slots_from_roster_positions(league.get("roster_positions") or [])
    per_roster, starters, totals = {}, [], []
    for roster_id, player_ids in sorted(trajectory.final_rosters().items()):
        players, unpriced = [], 0
        for pid in player_ids:
            info = players_db.get(str(pid)) or {}
            if str(pid) not in values:
                unpriced += 1
            players.append({
                "id": str(pid), "value": values.get(str(pid), 0.0),
                "eligible": set(info.get("fantasy_positions")
                                or ([info["position"]] if info.get("position") else [])),
            })
        solved = lo.optimize_lineup(players, slots)
        starter_value = round(solved["total_value"], 2)
        total = round(sum(p["value"] for p in players), 2)
        # #211's COMPANION. optimize_lineup has no "leave the slot empty" move -- it fills every
        # slot it can -- so a roster thin at a position is FORCED to start a below-replacement
        # player and his negative value lands in starter_value. Counting them is what lets a
        # reader tell a weak lineup from a lineup that was never fillable.
        forced_negative = sum(1 for a in solved["assignments"] if a["value"] < 0)
        per_roster[roster_id] = {
            "starter_value": starter_value, "total_value": total,
            "bench_value": round(total - starter_value, 2),
            "unpriced_players": unpriced,
            "forced_negative_starters": forced_negative,
            "slots_filled": len(solved["assignments"]),
            "starting_slots": len(slots),
        }
        starters.append(starter_value)
        totals.append(total)
    starters.sort()
    totals.sort()
    return {
        "per_roster": per_roster,
        # THE ROSTER-WORTH LINE (#211). universal_value is an asset LEVEL, so the quantity that
        # answers "what is this roster worth" is what the chair OWNS, not what it starts.
        "roster_worth_basis": ROSTER_WORTH_BASIS,
        "total_value_min": totals[0] if totals else None,
        "total_value_median": totals[len(totals) // 2] if totals else None,
        "total_value_max": totals[-1] if totals else None,
        "total_value_spread": round(totals[-1] - totals[0], 2) if totals else None,
        # THE LINEUP LINE. Retained because it answers a real and different question -- can this
        # roster field a legal lineup, and what does the forced assignment cost -- but it is NOT
        # the roster-worth number and the companion below is what stops it being read as one.
        "starter_value_min": starters[0] if starters else None,
        "starter_value_median": starters[len(starters) // 2] if starters else None,
        "starter_value_max": starters[-1] if starters else None,
        "starter_value_spread": round(starters[-1] - starters[0], 2) if starters else None,
        "forced_negative_starters": sum(r["forced_negative_starters"]
                                        for r in per_roster.values()),
    }


def unpriced_at_decision(trajectory) -> dict:
    """Picks whose CANDIDATE SET carried an unpriced row, and picks that TOOK one.

    #170. This exists because roster_strength's `unpriced_players` cannot answer the question
    it appears to answer. That counter measures against `reference_values`, which is built from
    the PRE-DRAFT board -- and the pre-draft board prices every row while every drafted player
    is necessarily on it, so its `values.get(pid, 0.0)` fallback is unreachable and the count is
    0 by construction across all 33 formats and ~5,000 picks. Reported as "every player priced",
    it reads as a measurement of the engine and is a property of the ruler's timing.

    This reads the board AS IT WAS AT THE PICK, off the snapshot every PickRecord already
    retains, so it can actually come out non-zero. Same idiom as chosen_replacement_basis: a
    decomposition of a decision the record already stores, read rather than re-derived.

    HONEST SCOPE, because the two are not the same question. The snapshot carries the NARROWED
    CANDIDATE SET, not the whole board, so this measures whether absence reached the DECISION
    SURFACE -- did an unpriced player contend for, or win, a pick -- and not what fraction of
    the board was unpriced. The decision surface is the question #165 and #168 are about; board
    coverage would need the board retained, which no record currently keeps.

    Absence is counted as absence: a candidate whose "uv" key is missing is NOT the same as one
    carrying None, and neither is folded into a zero. `examined` is reported so a rate is never
    quoted over an empty set."""
    examined = with_unpriced = took_unpriced = no_uv_key = 0
    for pick in trajectory.picks:
        candidates = (pick.snapshot or {}).get("candidates") or []
        if not candidates:
            continue
        examined += 1
        unpriced_ids = set()
        for cand in candidates:
            if "uv" not in cand:
                no_uv_key += 1
            elif cand.get("uv") is None:
                unpriced_ids.add(str(cand.get("id")))
        if unpriced_ids:
            with_unpriced += 1
            if str(pick.chosen_player_id) in unpriced_ids:
                took_unpriced += 1
    return {
        "picks_examined": examined,
        "picks_with_an_unpriced_candidate": with_unpriced,
        "picks_that_took_an_unpriced_candidate": took_unpriced,
        "candidate_rows_missing_the_uv_key": no_uv_key,
    }


def audit_trajectory(trajectory, league: dict, players_db: dict,
                     values: Optional[dict[str, float]] = None,
                     *, audit_roster_fill: bool = True) -> dict:
    """One trajectory, fully judged and fully described."""
    return {
        "label": trajectory.config.get("label", ""),
        "picks": len(trajectory.picks),
        "rosters": len(trajectory.final_rosters()),
        "findings": structural_findings(trajectory, league, players_db,
                                        audit_roster_fill=audit_roster_fill),
        "shape": roster_shape(trajectory, players_db),
        "margins": tav_margin_profile(trajectory),
        "qualifiers": qualifier_profile(trajectory),
        "regimes": dict(collections.Counter(p.decision_regime for p in trajectory.picks)),
        "strength": (roster_strength(trajectory, league, players_db, values)
                     if values is not None else None),
        # #170. Deliberately NOT folded into "strength": that block measures against the
        # pre-draft ruler, this one against the board at the pick, and merging two coverage
        # numbers with different references is how the first one came to be misread.
        "unpriced_at_decision": unpriced_at_decision(trajectory),
    }


#: Fields excluded from an arm's content fingerprint. `label` is the thing being compared, and
#: `seconds` is wall-clock -- including it would make every arm unique and the check vacuous.
#: Found the hard way: the first version of this comparison included `seconds` and reported 0
#: duplicates against a matrix that has 8.
_FINGERPRINT_EXCLUDES = frozenset({"label", "seconds"})


def roster_shape_axes(league: dict) -> dict:
    """The ROSTER-SHAPE dimensions of a league, derived from its own `roster_positions`.

    `league_format_hint` answers "which rankings export fits this league" -- scoring, superflex,
    te_premium. Those are the axes `format_axes_exercised` has always reported, and they are the
    right ones for FILE SELECTION. They are not the only ways a matrix can fail to cover the
    league someone actually plays.

    WHY THIS EXISTS, measured: the matrix carried 34 arms, **0 of them with a kicker slot** and
    **0 combining SUPER_FLEX with any IDP slot**, while the owner's league has both. A full
    draft on that shape put 31 kickers onto 12 rosters and 102 IDP players into 24 IDP slots, and
    the battery reported `0 structural findings` -- because `structural_findings` checks legality
    and the coverage instrument could not see slot composition as a dimension at all. Two
    independent blind passes found that behaviour; the instrument that exists to notice an
    unexercised axis reported "no constant axis" over a kicker-free matrix, truthfully, about
    the three axes it knew about.

    Derived, never hand-listed, exactly as the format axes are: these come from the league's own
    slots, so a league that adds a slot family appears here without anyone editing a list.
    """
    slots = [str(s).upper() for s in (league.get("roster_positions") or [])]
    return {
        "has_kicker": "K" in slots,
        "has_defense": "DEF" in slots or "DST" in slots,
        # dm.IDP_POSITIONS is the one home for the IDP vocabulary (#126); a league can name
        # an IDP slot either as a flex ("IDP_FLEX") or as a bare position ("LB").
        "has_idp_slot": any(s.startswith("IDP") or s in dm.IDP_POSITIONS for s in slots),
        "has_superflex_slot": "SUPER_FLEX" in slots,
        "draftable_rounds": len([s for s in slots if s not in ("BN", "IR", "TAXI")]),
    }


#: ONE HOME FOR THE AXIS VOCABULARY THE MATRIX ADVERTISES (#126, #52 phase 6).
#:
#: There are two derived vocabularies here and they answer different questions: which rankings
#: EXPORT fits a league (league_format_hint -- scoring, superflex, te_premium) and what SHAPE the
#: league is (roster_shape_axes -- kicker, defense, IDP, superflex slot, draftable rounds). Both
#: are real coverage dimensions, and format_axes_exercised unions them.
#:
#: The union used to be spelled out inside that function, which made it a SECOND home: the
#: report knew about both vocabularies and every test that checked the report knew about only
#: one, so the tests tracked league_format_hint's keys by hand and went red the moment the shape
#: axes were added. That is the hand-list defect one layer up from the one #126 names. The union
#: lives here, and the report and its tests both read it.
def advertised_format_axes(league: dict) -> dict:
    """{axis name: this league's value} across every dimension the matrix claims to cross."""
    axes = dict(league_format_hint(league))
    axes.update(roster_shape_axes(league))
    return axes


#: Axes the matrix ADVERTISES but does not currently VARY, each with why and what would close it.
#:
#: Registering a hole is not silencing it -- it is the difference between a coverage gap someone
#: decided to carry and one nobody noticed. The guard reads this both ways: an unregistered
#: constant axis fails (a gap appeared), and a registered axis that starts varying ALSO fails
#: (the registration went stale and should be deleted). Neither direction can drift quietly.
#: EMPTY IS THE HEALTHY STATE, not a reason to delete this register.
#:
#: `has_defense` lived here until #52: no arm carried a DEF slot, so the matrix advertised a
#: dimension it did not cross and no run was evidence about drafting a defense. It was closed by
#: adding `12T_ppr_K_DEF` -- a DEF-bearing arm differing from its sibling in exactly the two
#: slots -- rather than by adjusting anything, which is what its own entry said closing it would
#: take.
#:
#: The register stays because `test_every_constant_axis_is_a_REGISTERED_one` compares the
#: matrix's constant axes AGAINST it, in both directions: an unregistered constant axis is a new
#: coverage hole, and a registered axis that starts varying is a stale registration. Empty means
#: "every advertised axis is actually crossed", which is the goal state -- and the comparison
#: still catches the next hole the day it appears. Deleting the register would delete the
#: mechanism at the moment it first had nothing to report.
UNCOVERED_AXES: dict[str, str] = {}


def format_axes_exercised(matrix: list[dict], labels=None) -> dict:
    """Which value of each format axis the arms ACTUALLY exercise, and which axes are CONSTANT.

    THE SIBLING OF duplicate_arms, AND IT CATCHES WHAT duplicate_arms CANNOT. That detector
    finds arms whose measured content is byte-identical. It cannot see an axis that varies the
    arms' *scoring values* while never varying the thing those values are supposed to select --
    the arms differ, so nothing is flagged, and the matrix goes on advertising a dimension it
    stopped having.

    #241 WAS FILED AS EXACTLY THAT AND WAS WRONG, which is worth keeping here rather than
    deleting. The claim was that all 33 arms resolve `te_premium=True`, because #213 made the
    real Fourth & Forever rulebook (`bonus_rec_te = 0.25`) every arm's base and
    `build_mock_league(te_premium=False)` can add a bonus but not remove one. The measurement
    behind it built the matrix from `data/league_captures/fourth_and_forever.json` -- a
    DIFFERENT captured league from the one `run_draft_battery` actually drafts, which is
    `data/fixtures/sleeper_capture.json` (full PPR, no TE bonus). Against the battery's own
    source the axis varies: 30 arms `False`, 3 `True`, and no axis is constant. The finding is
    withdrawn; this function is kept because it is what caught it, on its first real run.

    So the hole it guards against is real in KIND even though that instance was not: an axis can
    stop varying without any arm becoming a duplicate, and nothing else in the report would say
    so. It now says so, and a witness test pins that no axis is constant TODAY.

    DERIVED, NEVER HAND-LISTED, twice over: the axis NAMES come from league_format_hint's own
    return keys, so adding an axis there makes it appear here without anyone editing a list;
    and the values come from the arms' own leagues rather than from the labels, which is the
    #126 rule and also the reason a label saying "redraft" cannot lie to this function.

    `labels` scopes the answer to the arms actually being reported (a --only run, or the arms a
    resumed report has so far), so the disclosure always describes THAT report rather than the
    matrix a fuller run would have had.
    """
    entries = [e for e in matrix
               if labels is None or e.get("label") in labels]
    axes: dict[str, dict[str, int]] = {}
    for entry in entries:
        # Both derived vocabularies, from their one home. An axis that is constant in either
        # sense is a matrix not covering something.
        axis_values = advertised_format_axes(entry["league"])
        for axis, value in axis_values.items():
            # str() because JSON object keys are strings: True would round-trip as "true"
            # anyway, and a dict keyed half by bool and half by str sorts unstably.
            seen = axes.setdefault(axis, {})
            seen[str(value)] = seen.get(str(value), 0) + 1
    return {
        "arms": len(entries),
        "axes": {a: dict(sorted(v.items())) for a, v in sorted(axes.items())},
        # An axis with one observed value across >1 arm is advertised but not exercised. With a
        # single arm every axis is trivially constant and saying so would be noise, not news.
        "constant_axes": sorted(a for a, v in axes.items() if len(v) == 1) if len(entries) > 1 else [],
    }


def duplicate_arms(results: list[dict]) -> list[dict]:
    """Arms of the matrix whose ENTIRE measured content is identical to another arm's.

    WHY THE INSTRUMENT HAS TO SAY THIS ABOUT ITSELF. league_matrix() crosses four sizes x three
    scorings x two QB modes and reports the count as though every arm were independent evidence.
    It is not: `set_league_format` resolves a league's format to the best-fitting Dynasty
    Rankings export, and no HALF-PPR export exists in the baseline -- so a half_ppr league
    legitimately draws PPR values (scored 0.5 rather than 1.0 by
    data_merger._rankings_format_match_score, and disclosed to the user in app.py). That is
    CORRECT handling of a real data limitation. What is not correct is a report claiming N
    formats of coverage when some of them reproduce another arm byte for byte, which inflates
    the denominator under every rate this battery produces and makes a duplicated finding look
    like independent corroboration.

    THE COUNT THIS PARAGRAPH USED TO CARRY IS STALE, AND ITS STALENESS COST A DECISION. It said
    "8 of them reproduce another arm byte for byte", measured when the battery was VENDOR-priced
    -- half_ppr leagues drew the PPR export and genuinely collapsed onto the PPR arms. Once
    `#213`/`#201`/`#204` made the battery scoring-aware, scoring reaches a price through the
    league's own STAT LINES rather than only through export selection, and those arms stopped
    duplicating. Measured on `BATTERY_2026-09-12_scoring_aware_full_99f9f76`: **33 formats, 32
    independent, ONE duplicate** (`12T_ppr_mode_balanced` duplicates `12T_ppr`).

    A trim of the Gate 1 matrix was proposed and ruled on the strength of the stale figure; the
    measurement showed it would remove one arm and save ~12 minutes of a 6.5-hour run, and the
    ruling was reversed (`#258`). No number belongs in this prose that the detector can report
    for itself -- which is the whole reason the detector is derived.

    DERIVED, NEVER HAND-LISTED, for the reason league_config.ambiguities() is derived: a list
    naming half_ppr would go stale the first time a half-PPR export is added, or miss a
    collapse on an axis nobody predicted. This compares what the arms actually PRODUCED, so a
    new duplicate announces itself and a resolved one disappears without anyone editing a list.
    """
    seen: dict[str, str] = {}
    dupes: list[dict] = []
    for row in results:
        body = json.dumps({k: v for k, v in row.items() if k not in _FINGERPRINT_EXCLUDES},
                          sort_keys=True, default=str)
        first = seen.get(body)
        if first is None:
            seen[body] = row.get("label")
        else:
            dupes.append({"label": row.get("label"), "duplicates": first})
    return dupes


def prefix_arms(sequences: dict[str, list]) -> list[dict]:
    """Arms whose ENTIRE pick sequence is a prefix of another arm's. The third detector.

    WHY A THIRD ONE EXISTS, and the published entry that earned it. `#276`: the depth battery's
    six-arm bench ladder (BN 6/10/14/18/22/26, 12 teams, everything else held) turned out to be
    ONE 408-pick draft sampled at six lengths -- BN6's 168 picks are a strict prefix of BN10's
    216, and so on. `#271` had already published that ladder as "the crossing fires in none of
    the six", which overstates one observation as six, and a prediction resting on those six
    arms agreeing could not have failed.

    NEITHER SIBLING CAN SEE IT, and that is the point:
      - `duplicate_arms` compares each arm's ENTIRE measured body for byte identity. Prefix-
        nested arms have different lengths and different totals, so nothing is flagged.
      - `format_axes_exercised` catches an axis that stops varying. The bench axis genuinely
        varies 6 -> 26, so nothing is flagged.
    An axis varies, no arm is a duplicate, and the arms are still not independent evidence.

    WHY PREFIX AND NOT "SHARES A LONG OPENING". Every snake draft of the same league shares its
    first pick, and most share several; a similarity threshold here would be a calibrated
    constant with no derivation behind it, which `#56` forbids (a bound is not a threshold).
    STRICT PREFIX is a structural fact, not a judgement: arm A adds no observation that arm B
    does not already contain, because B replays A exactly and then continues. That is decidable
    with no constant at all, which is the only reason this detector is allowed to exist.

    Equal-length identical sequences are NOT reported here -- that is `duplicate_arms`' job, and
    reporting the same collapse from two detectors would double-count one problem.

    Returns one row per nested arm naming its container, longest container first so the report
    reads as "this arm is contained by that one".
    """
    items = [(label, list(seq)) for label, seq in sequences.items()]
    nested: list[dict] = []
    for label, seq in items:
        container = None
        for other_label, other in items:
            # `other_label == label` is UNREACHABLE BY CONSTRUCTION and kept as a guard rather
            # than a live branch: the length test below already excludes self, because no
            # sequence is STRICTLY longer than itself. A mutation pass confirmed it -- deleting
            # this clause leaves every test passing, an EQUIVALENT MUTANT rather than a gap in
            # the tests, and it is recorded here so the next reader does not go hunting for the
            # missing case. It stays because it makes the length test's `<=` load-bearing for
            # one thing only (equal-length arms belong to duplicate_arms) instead of two.
            if other_label == label or len(other) <= len(seq):
                continue
            if other[:len(seq)] == seq:
                if container is None or len(sequences[container]) < len(other):
                    container = other_label
        if container is not None:
            nested.append({"label": label, "prefix_of": container,
                           "picks": len(seq), "container_picks": len(sequences[container])})
    return nested


def run_battery(merger, players_db: dict, matrix: Optional[list[dict]] = None,
                *, mode: str = "auto",
                sleeper_projections: Optional[dict[str, dict]] = None,
                sleeper_basis: str = dr.SLEEPER_BASIS_WEEKLY) -> list[dict]:
    """Draft every format in the matrix and audit each one.

    pick_order is generated per format rather than reused, since team count varies -- and it is
    a real input, not a seed: this whole battery contains no randomness, so re-running it must
    reproduce byte-identical trajectories (test_draft_simulation already pins that contract for
    one draft; here it holds across the matrix).
    """
    results = []
    for entry in matrix if matrix is not None else league_matrix():
        # THE FORMAT HAS TO REACH THE MERGER, and this line is why the first full run was
        # partly vacuous. `rec` and `bonus_rec_te` do NOT propagate through scoring_settings
        # into offensive valuation -- Draft Sharks' season projection is a STATIC pre-computed
        # number. They propagate by FILE SELECTION: set_league_format picks a different Dynasty
        # Rankings export (see data_merger._detect_rankings_format), which app.py calls on every
        # rerun. A battery that never calls it drafts every format from whichever export
        # happened to load, so scoring is silently held constant.
        #
        # Measured on the run before this was added: standard, half_ppr and ppr produced
        # BYTE-IDENTICAL drafts in all eight size/superflex combinations, and TE premium was
        # equally inert. The roster geometry was genuinely exercised; the scoring axis was not
        # exercised at all while appearing in every label.
        merger.set_league_format(league_format_hint(entry["league"]))
        roster_ids = [str(i) for i in range(1, entry["teams"] + 1)]
        pick_order = ds.generate_pick_order(roster_ids, entry["rounds"], "snake")
        # THE SECOND HALF OF THE SAME LESSON (#204). set_league_format above carries scoring
        # into the VENDOR export by file selection; these two carry the league's own scoring
        # into the SLEEPER points, which is the other half of what production prices from
        # (app.py passes season_projections + SLEEPER_BASIS_SEASON_SUM on every rerun). A
        # battery that omits them drafts a board where sleeper_points, sleeper_basis and
        # availability_basis are None on every row -- so the scoring-aware path and the
        # availability haircut are both absent from the final gate while appearing nowhere in
        # the report as absent.
        # upside_rule and opponent_noise are forwarded FROM THE ARM, defaulted so every arm that
        # does not carry them drafts exactly as before -- the format matrix carries neither, so
        # its trajectories are byte-identical to the runs already committed under it. They exist
        # because the VDS battery (vds_battery.py) sweeps them: the format matrix varies FORMAT
        # and holds strategy fixed at mode="auto", which is the gap #20/#22 fell through. One arm
        # loop, extended -- not a second copy, because two batteries with two copies of one audit
        # is two homes for one fact (#126) and the copy nobody watches is the one that drifts.
        trajectory = draft_simulation.simulate_full_draft(
            merger, players_db, entry["league"], pick_order,
            mode=entry.get("mode", mode), config_label=entry["label"],
            upside_rule=entry.get("upside_rule", dr.UPSIDE_RULE_ROUND),
            opponent_noise=entry.get("opponent_noise"),
            sleeper_projections=sleeper_projections, sleeper_basis=sleeper_basis)
        values = reference_values(merger, players_db, entry["league"],
                                  sleeper_projections=sleeper_projections,
                                  sleeper_basis=sleeper_basis)
        # Formats whose draft is shorter than their roster opt out of the fill audit only
        # (see structural_findings); every other audit still applies to them.
        audited = audit_trajectory(trajectory, entry["league"], players_db, values,
                                   audit_roster_fill=entry.get("audit_roster_fill", True))
        audited["teams"] = entry["teams"]
        audited["rounds"] = entry["rounds"]
        # THE PICK SEQUENCE, player ids only. Carried so a caller can derive whether two arms
        # actually drafted differently instead of assuming that a parameter it forwarded had an
        # effect. The VDS battery uses it to detect INERT arms -- measured before its first run,
        # two of its six strategies reproduced the control byte-for-byte on an 8-round format,
        # because `auto` never reaches the upside round there and the crossing rule never fires.
        # A strategy can be listed, forwarded, and exercise nothing.
        audited["pick_sequence"] = [str(p.chosen_player_id) for p in trajectory.picks]
        results.append(audited)
    return results
