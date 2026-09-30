"""Whether a league's configuration can be read cleanly, and how old the copy in use is.

WHAT #140 SAID, AND WHAT IS ACTUALLY TRUE. The register item recorded that `get_rosters` was
called nowhere and that every league's config came from the bulk `/user/{id}/leagues` payload.
Both are wrong, and they were checked rather than trusted before this module was built around
them: `sleeper_client.sync_league` calls `get_league` AND `get_rosters` itself, writes both into
the snapshot, and the board reads `snapshot["league"]` -- not the bulk list. The config in use
IS fetched fresh, at sync time.

WHAT REMAINS, AND IT IS SHARPER THAN THE ORIGINAL CLAIM:

  1. `activate_league` re-syncs ONLY when there is no cached snapshot at all. An existing
     snapshot is reused however old it is, by design ("use Refresh This League when you
     actually want fresher data"). So sync at 9am, draft at 8pm, and the board rests on an
     eleven-hour-old config -- a commissioner scoring or roster-slot change in between is used
     silently.

  2. The staleness IS disclosed -- and at the wrong RESOLUTION, which is worse than not being
     disclosed at all because it reads as reassurance. `build_freshness_manifest` computes age
     as a difference of `.date()`, so it is wrong in both directions at the boundary, measured
     directly:
         synced 9am, read 8pm same day  -> reports "0 days old" for an 11-hour-old config
         synced 23:59, read 00:01       -> reports "1 day old"  for a 2-minute-old one
     League config changes on an hours timescale. A day-resolution number cannot express that.

NO STALENESS THRESHOLD IS DEFINED HERE, deliberately. Nothing in this repository measures how
often a commissioner actually changes a setting, so "older than N hours is stale" would be an
invented magnitude (#56). Age is reported at a resolution that can express the question, and
the answer is left to the reader who knows their own league.

THE CONFIRMATION STATE is the half that was right, and it stands independent of all of the
above. Three states, the same idiom as horizon_basis / identity_basis / adjudication:

  CONFIRMED  -- a person reviewed this league's config.
  INFERRED   -- it parsed cleanly and nobody looked. Does NOT block; most leagues live here.
  AMBIGUOUS  -- something did not parse cleanly. The only blocking state.

The difference from the vendor pattern this borrows: they review everything because they cannot
know what they got wrong. This app can detect its own ambiguity, so it asks only where it is
genuinely unsure -- and `ambiguities()` is DERIVED from the vocabularies the engine itself
reads, never a hand-kept list of remembered cases. A list would go stale the first time Sleeper
adds a slot code.
"""

from __future__ import annotations

import time
from typing import Optional

from player_universe import FANTASY_POSITIONS, FLEX_SLOT_POSITIONS

#: THE SLOT VOCABULARY, AND THE TWO QUESTIONS IT ANSWERS.
#:
#: A roster_positions label is asked two different questions by two different parts of this app,
#: and until this block existed only the first one had an answer -- in two places, under two
#: names ("NON_STARTING_SLOTS" in draft_battery, "NON_PLAYING_SLOTS" here) holding IDENTICAL
#: membership. Two homes for one vocabulary is exactly what #126 forbids, and the cost was not
#: the duplication: it was that the SECOND question looked answered when it had never been asked.
#:
#:   Q1  Does this slot START a player in a given week?   -> NON_STARTING_SLOTS says no.
#:   Q2  Is this slot FILLED BY THE STARTUP DRAFT?        -> UNDRAFTED_SLOTS says no.
#:
#: The two are NOT the same question. BN and TAXI never start anybody and are both drafted; IR
#: is the only label that answers no to both. Every instrument in this repository used
#: `len(roster_positions)` for the draft's round count, which is Q2 answered with Q1's silence.
#:
#: WHY {"IR"} AND NOT A LARGER SET -- this is a vocabulary observation, not a derived magnitude,
#: so the evidence is stated rather than assumed. Two captured Sleeper leagues, both with IR and
#: TAXI, and in both the recorded draftable count is exactly len(roster_positions) - IR count:
#:
#:   fourth_and_forever     29 slots - 3 IR = 26,  and the real startup ran EXACTLY 26 rounds
#:   greatest_show_on_paper 33 slots - 4 IR = 29
#:
#: The first is an exact external confirmation, not a restatement: the board's own round count
#: was observed independently of the roster shape. test_slot_vocabulary re-derives both numbers
#: from the captures themselves, so a third league that contradicts the rule FAILS rather than
#: being quietly absorbed.
NON_STARTING_SLOTS = frozenset({"BN", "TAXI", "IR"})

#: Q2's answer. Kept separate from Q1's rather than expressed as a subset relation, because the
#: two sets happen to nest today and nothing guarantees they always will.
UNDRAFTED_SLOTS = frozenset({"IR"})

#: The pre-#126 name for Q1's set, kept so existing readers do not have to move at once. It is
#: an alias, not a second definition -- there is one object here, and `is` proves it.
NON_PLAYING_SLOTS = NON_STARTING_SLOTS


def starting_slots(roster_positions: Optional[list[str]]) -> list[str]:
    """The slots that start a player, in order. Q1 applied to a whole roster shape."""
    return [s for s in (roster_positions or []) if s not in NON_STARTING_SLOTS]


def draftable_slots(roster_positions: Optional[list[str]]) -> list[str]:
    """The slots a startup draft fills, in order. Q2 applied to a whole roster shape.

    `len(draftable_slots(rp))` is the round count of a startup draft, and it is NOT
    `len(rp)` -- see the vocabulary block above for the two leagues that establish the
    difference and the one that confirms it against a real board.
    """
    return [s for s in (roster_positions or []) if s not in UNDRAFTED_SLOTS]

#: The full set of roster_positions labels this app understands, derived from the two
#: vocabularies the engine actually reads plus the non-playing slots. A label outside this set
#: is not "an unknown slot we can ignore" -- it is a slot whose players the lineup solver will
#: silently fail to place, so it makes the config AMBIGUOUS.
KNOWN_SLOTS = frozenset(FANTASY_POSITIONS) | frozenset(FLEX_SLOT_POSITIONS) | NON_PLAYING_SLOTS

#: D10, THE OWNER'S RULING: "price it, but modulate how loudly the warning is to the impact that
#: that missing data has on the decision ... telling on ourselves extra loud may be undercutting
#: our authority when an asterisk may be enough."
#:
#: The refusal machinery `league_config` described is NOT built and this module no longer claims
#: one (C-F4). The board is always priced. What changes is how loudly an unparsed slot is
#: reported, and the three kinds below are THE MEASURED IMPACT rather than a judgement about
#: severity -- which is the only way to scale a warning without inventing a threshold (`#56`).
#:
#: WHY THERE ARE EXACTLY THREE AND NOT A SPECTRUM. The consequence of dropping a slot label
#: depends on one fact: whether that slot starts a player. The engine can answer it in two cases
#: and not in the third, so the bands are what is knowable, not a scale someone chose:
#:
#:   NONPLAYING  the label normalises to BN/TAXI/IR. `slots_from_roster_positions` excludes those
#:               ANYWAY, so the starting lineup the board was priced on is exactly the one the
#:               league declares. The consequence is ZERO -- not small, zero -- and an asterisk
#:               is the honest volume.
#:   STARTER     it normalises to a position or flex slot the solver does know, so the engine can
#:               say precisely which starting slot was lost and how many of them remain. Loud,
#:               and specific about the damage.
#:   UNKNOWN     it normalises to nothing. It MAY start a player, and if it does then every
#:               replacement level and starter-demand figure is about a smaller lineup than the
#:               real league. The engine cannot bound this, so it says so -- loudly, and says
#:               that the bound is what is missing rather than implying a size.
#:
#: NEW KINDS RATHER THAN A NEW FIELD, deliberately: `config_ambiguities` crosses the snapshot
#: boundary as (kind, detail) PAIRS, and a stored board written before today keeps the bare
#: `unknown_slot` kind -- which lands in the loud set, the safe direction, and replays exactly
#: as recorded.
AMBIGUITY_UNKNOWN_SLOT = "unknown_slot"
AMBIGUITY_UNKNOWN_SLOT_NONPLAYING = "unknown_slot_nonplaying"
AMBIGUITY_UNKNOWN_SLOT_STARTER = "unknown_slot_starter"

#: The kinds whose measured consequence is ZERO. A consumer scaling its presentation reads THIS
#: rather than matching kind strings itself, so a kind added later is not silently loud-by-
#: omission in one surface and quiet in another (`#126`).
IMMATERIAL_AMBIGUITY_KINDS = frozenset({AMBIGUITY_UNKNOWN_SLOT_NONPLAYING})


def normalised_slot(label: str) -> str:
    """A slot label with case and separators removed, for asking "did they mean a known slot?".

    Case, spaces, underscores, hyphens and dots only. NOT a spelling corrector and not an alias
    table: `SUPER-FLEX` and `super_flex` are the same label as `SUPER_FLEX` typed differently,
    while `RES` is not `IR` and this function must never claim it is. Inventing that equivalence
    would be asserting knowledge about the vendor's vocabulary that nothing here measured.
    """
    out = (label or "").upper()
    for junk in (" ", "_", "-", "."):
        out = out.replace(junk, "")
    return out


#: The known vocabularies under the same normalisation, built once so a comparison cannot drift
#: from the sets it is about.
_NORMALISED_NONPLAYING = {normalised_slot(slot): slot for slot in NON_PLAYING_SLOTS}
_NORMALISED_STARTING = {normalised_slot(slot): slot
                        for slot in list(FANTASY_POSITIONS) + list(FLEX_SLOT_POSITIONS)}

#: Keys whose ABSENCE changes what the engine concludes about a league -- not every key it might
#: read. `compute_points_from_stats` iterates whatever it is given, so a missing category there is
#: a smaller projection, not a misread league. These are different: each silently resolves to a
#: DEFAULT that describes a different league.
#:
#: THIS USED TO BE ONE FLAT TUPLE, ("rec", "bonus_rec_te", "type", "num_teams"), checked against
#: `scoring` and `settings` together -- and it refused EVERY REAL LEAGUE (2.2). Measured over the
#: 53 production-shaped leagues `draft_battery.league_matrix` builds: refused 53 of 53. Two of the
#: four entries were wrong, in two different ways, and splitting them by WHERE THEY LIVE and HOW
#: THEIR ABSENCE READS is what fixes both. The third and fourth are right and stay.

#: `type` is the dynasty flag. `draft_room` reads `league["settings"]["type"] == 2` and gates BOTH
#: `time_horizon_adj` and `risk_adj`'s trajectory scaling on it, so an absent `type` prices a
#: dynasty league as a redraft and says nothing about having done so. No safe default exists,
#: which is what earns a key a place here. Absent in 2 of the 53 -- both the CAPTURE_owner_league
#: arms, whose `league_shape` carries three keys by design, and which `draft_battery` already
#: states are drafted as redraft. The gate agreeing with that comment, arm for arm, is the gate
#: working.
FORMAT_DECIDING_SETTINGS_KEYS = ("type",)

#: THE TEAM COUNT, UNDER THE NAME THE ENGINE READS (#126). This was `num_teams`, looked for in
#: `scoring` and `settings` -- and nothing on the valuation path reads that key at all. Sleeper
#: sends the count as `total_rosters` at the TOP LEVEL, and every production reader takes it from
#: there: draft_room's `compute_draft_board`, and pick_synthesis in two places. Measured over the
#: 53: `num_teams` absent in 53 of 53, `total_rosters` present in 53 of 53. So the gate refused
#: every league in the matrix for want of a key the engine does not use, while the number it
#: wanted sat one level up under its real name.
#:
#: Its absence still blocks, because the fallback is not benign: `compute_draft_board` reads
#: `league.get("total_rosters") or len({roster_id from picks}) or 1`, so an empty draft with no
#: count resolves to ONE TEAM, which puts every position's replacement level at its best player.
TEAM_COUNT_KEY = "total_rosters"

#: Scoring keys that decide FORMAT rather than points. They do not reach offensive valuation
#: through `scoring_settings` at all -- the vendor's season projection is pre-computed -- they
#: reach it by FILE SELECTION, through `league_format_hint` into `set_league_format`.
#:
#: THEIR ABSENCE IS NOT AN UNKNOWN, and treating it as one was the second false refusal. Sleeper
#: returns a COMPLETE scoring dict and omits every category the league does not score, so a key
#: missing from a POPULATED dict is a declared zero. That is also precisely how the engine reads
#: it: `league_format_hint` takes `scoring_settings.get("rec", 0)` and concludes standard, and
#: `.get("bonus_rec_te", 0) > 0` and concludes no TE premium. Both are CORRECT conclusions about a
#: league that scores neither -- not defaults standing in for an unread setting. `bonus_rec_te` is
#: absent in 47 of the 53, every one of them carrying a populated scoring dict.
#:
#: So these are reported only when the league carries NO `scoring_settings` at all, which is a
#: genuinely unread config rather than a league that declines to score a category.
FORMAT_DECIDING_SCORING_KEYS = ("rec", "bonus_rec_te")

#: The same vocabulary whole, for readers that want it that way. `num_teams` is deliberately NOT
#: in it: TEAM_COUNT_KEY names that fact now, under the name the engine reads.
FORMAT_DECIDING_KEYS = FORMAT_DECIDING_SCORING_KEYS + FORMAT_DECIDING_SETTINGS_KEYS

CONFIRMED = "confirmed"
INFERRED = "inferred"
AMBIGUOUS = "ambiguous"

#: Set on a config a person has reviewed. Underscore-prefixed so it cannot collide with a key
#: Sleeper itself returns.
CONFIRMED_KEY = "_config_confirmed"


#: The draft's own seats, carried ON the league dict so the ENGINE can reach them.
#:
#: `team_count`'s order of authority put the seats first and then could not see them: the screen
#: called it with `pick_order=` and the engine called it with `league` and `picks`, because
#: `league_for_engine` carried no seats. Same function, different inputs, different rule -- so a
#: 10-seat draft in a 12-roster league gave the caption 10 and every replacement level 12, which
#: is the exact split the consolidation names as its purpose and asserts it has closed.
#:
#: A KEY RATHER THAN A PARAMETER because the seats have to cross four call layers to reach
#: `replacement_ranks`, and every layer that has to pass them along is a layer that can forget to.
#: The league dict already travels that whole distance.
PICK_ORDER_KEY = "draft_pick_order"

#: What `team_count` actually answered from -- returned WITH the number (`#166`), because two of
#: its four rules are not team counts at all. `TEAM_BASIS_FLOOR` in particular means "nothing here
#: said how many teams there are" and a caller with its own fallback must be able to tell that
#: from a real count of one. `_round_being_decided` is such a caller: routed through a bare
#: `team_count` it would read the floor as a one-team league and answer `len(picks) + 1` instead
#: of using the round its own picks carry.
TEAM_BASIS_SEATS = "draft_seats"
TEAM_BASIS_DECLARED = "total_rosters"
TEAM_BASIS_PICKS = "distinct_roster_ids"
TEAM_BASIS_FLOOR = "no_basis_floor_of_one"


def team_count_with_basis(league: Optional[dict] = None, *, pick_order=None,
                          picks: Optional[list] = None) -> tuple[int, str]:
    """(count, basis). THE derivation; `team_count` is this function's first element.

    One body rather than two, so the count and the basis cannot disagree -- a companion computed
    beside the number instead of with it is `#166`'s own failure mode."""
    seats = pick_order
    if seats is None and league:
        seats = league.get(PICK_ORDER_KEY)
    if seats:
        distinct = {str(seat) for seat in seats if seat is not None}
        if distinct:
            return len(distinct), TEAM_BASIS_SEATS
    declared = (league or {}).get(TEAM_COUNT_KEY)
    if declared:
        return int(declared), TEAM_BASIS_DECLARED
    if picks:
        drafting = {p.get("roster_id") for p in picks if p.get("roster_id") is not None}
        if drafting:
            return len(drafting), TEAM_BASIS_PICKS
    return 1, TEAM_BASIS_FLOOR


def team_count(league: Optional[dict] = None, *, pick_order=None,
               picks: Optional[list] = None) -> int:
    """How many teams are drafting -- ONE derivation, in a stated order of authority (`#126`).

    This was spelled three times and only one of them had a fallback: `len(round_1_order)` in the
    Draft Room, `league.get("total_rosters")` beside it, and
    `league.get("total_rosters") or len({roster_id}) or 1` in the engine. They agree on every league
    in hand, and the input that splits them is a draft with fewer seats than the league has rosters
    -- at which point the screen and the engine would price the same board against different team
    counts, and every replacement level with it.

    THE ORDER IS THE ARGUMENT, not a preference:

      1. the draft's OWN seats -- the `pick_order` argument, or `PICK_ORDER_KEY` on the league
         dict. A draft in progress has a definite number of chairs and that is the number every
         per-turn quantity is about, whatever the league record says.

         THE KEY IS WHY THIS RULE NOW REACHES THE ENGINE. Until it existed, only the screen ever
         passed seats; the engine called this function with `league` and `picks` and could not
         have passed them, so the two callers ran different rules and the paragraph below -- which
         says they can no longer give two counts -- was false for exactly the input it names.
      2. `total_rosters` -- the league's own count, under the name the engine reads
         (TEAM_COUNT_KEY, MANDATE 2.2). Authoritative when no draft is in hand.
      3. the distinct roster ids among `picks` -- a floor, not a count: a roster that has not picked
         yet is invisible here. Kept because the engine's own reading had it, and dropping a fallback
         is a behaviour change dressed as a cleanup.
      4. `1`, which is not a team count but is what the arithmetic needs to not divide by zero. The
         engine's reading ended this way too; it is preserved rather than improved, because a
         one-team league puts every replacement level at its position's best player and that is a
         consequence worth leaving visible instead of papering over.
    """
    return team_count_with_basis(league, pick_order=pick_order, picks=picks)[0]


def round_of(picks_completed: int, num_teams: Optional[int]) -> Optional[int]:
    """Which round the NEXT pick belongs to -- one home for `n // teams + 1` (`#126`).

    Spelled three times: once in the Draft Room's own round label, twice in the engine (the round
    that decides `use_upside`, and the round stamped on a simulated pick). They agreed, and the
    arithmetic is the sort that is easy to get subtly wrong in one copy -- `#52` phase 6 records a
    version that lagged by one at every round boundary, which switched `mode="auto"` to upside
    scoring a pick late and made a battery report a split the trajectory did not produce.

    `None` when there is no team count, rather than a guess: a caller with another way to answer
    (a pick's own recorded round, say) should use it, and one without should not be handed a number
    derived from nothing. The one caller that HAS such a fallback keeps it at its own site, because
    reading a recorded round is a different source and not this function's business.
    """
    if not num_teams:
        return None
    return int(picks_completed) // int(num_teams) + 1


def config_age_seconds(snapshot: Optional[dict], now: Optional[float] = None) -> Optional[float]:
    """How old the config in use actually is, in seconds -- or None if nothing was ever synced.

    Reads `synced_at` off the SNAPSHOT rather than the league dict, because that is where the
    config in use comes from: sync_league fetches league + rosters together and stamps the pair,
    so one timestamp genuinely covers both.

    None, never a large number: "never synced" and "synced long ago" are different answers and
    a caller rendering the second for the first would say the opposite of the truth.
    """
    stamp = (snapshot or {}).get("synced_at")
    if stamp is None:
        return None
    return max(0.0, (now if now is not None else time.time()) - float(stamp))


def describe_config_age(snapshot: Optional[dict], now: Optional[float] = None) -> Optional[str]:
    """The age as a phrase whose resolution matches how fast the thing it describes changes.

    Minutes under an hour, hours under a day, then days. The defect this replaces reported a
    difference of calendar DATES, which is wrong in both directions at the boundary: an
    eleven-hour-old config read as "0 days old", and a two-minute-old one synced at 23:59 read
    as "1 day old".
    """
    age = config_age_seconds(snapshot, now)
    if age is None:
        return None
    minutes = int(age // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    hours = int(age // 3600)
    if hours < 24:
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    days = int(age // 86400)
    return f"{days} day{'s' if days != 1 else ''} ago"


def ambiguities(league: Optional[dict]) -> list[dict]:
    """Everything about this config the app could not read cleanly, derived not remembered.

    Each entry is {"kind", "detail"}. An empty list means every check passed, which is what
    makes INFERRED an honest state rather than an absence of checking.
    """
    league = league or {}
    slots = list(league.get("roster_positions") or [])
    settings = league.get("settings") or {}
    scoring = league.get("scoring_settings") or {}
    found = []

    if not slots:
        found.append({"kind": "no_roster_positions",
                      "detail": "the league carries no roster_positions at all"})
        return found

    unknown = sorted({slot for slot in slots if slot not in KNOWN_SLOTS})
    if unknown:
        # D10: SPLIT BY MEASURED CONSEQUENCE, not reported as one undifferentiated alarm. See the
        # three AMBIGUITY_UNKNOWN_SLOT_* constants for why these are the only three bands.
        parsed_starting = len(starting_slots(slots))
        nonplaying, starters, unresolved = [], {}, []
        for label in unknown:
            key = normalised_slot(label)
            if key in _NORMALISED_NONPLAYING:
                nonplaying.append(label)
            elif key in _NORMALISED_STARTING:
                starters[label] = _NORMALISED_STARTING[key]
            else:
                unresolved.append(label)

        if nonplaying:
            found.append({
                "kind": AMBIGUITY_UNKNOWN_SLOT_NONPLAYING,
                "detail": f"roster slot(s) {sorted(nonplaying)} are spelled in a way this app does "
                          f"not recognise, but each one normalises to a non-playing slot "
                          f"({sorted(NON_PLAYING_SLOTS)}), which the lineup solver leaves out "
                          f"anyway. The board was priced on the same {parsed_starting} starting "
                          f"slots your league declares, so this costs nothing",
            })
        if starters:
            named = ", ".join(f"{raw} (meaning {known})" for raw, known in sorted(starters.items()))
            found.append({
                "kind": AMBIGUITY_UNKNOWN_SLOT_STARTER,
                "detail": f"roster slot(s) {named} name STARTING slots, spelled in a way this app "
                          f"does not recognise, so they were dropped: the board was priced on "
                          f"{parsed_starting} starting slots where your league declares "
                          f"{parsed_starting + len(starters)}. Every replacement level and every "
                          f"starter-demand figure below is about the smaller lineup",
            })
        if unresolved:
            found.append({
                "kind": AMBIGUITY_UNKNOWN_SLOT,
                "detail": f"roster slot(s) {sorted(unresolved)} are in neither the position "
                          f"vocabulary, the flex vocabulary, nor {sorted(NON_PLAYING_SLOTS)} -- "
                          f"the lineup solver cannot place anyone in them. IF ANY OF THEM STARTS "
                          f"A PLAYER, the board was priced on {parsed_starting} starting slots "
                          f"where your league has up to {parsed_starting + len(unresolved)}, and "
                          f"every replacement level is about a different league. This app cannot "
                          f"tell which, so it cannot bound the error",
            })

    if "BN" not in slots:
        # Best-ball leagues genuinely have no bench, and so does a roster_positions list that
        # lost its BN entries in parsing. The app cannot tell those apart, which is precisely
        # what AMBIGUOUS means -- so it asks instead of guessing either way.
        found.append({
            "kind": "no_bench",
            "detail": "no BN slots. That is either a best-ball league or a parse that dropped "
                      "them, and nothing here can distinguish the two",
        })

    # Two literal QB slots is functionally superflex; every superflex consumer in this app keys
    # off the SUPER_FLEX token alone, so such a league would be scored as 1QB.
    if "SUPER_FLEX" not in slots and slots.count("QB") > 1:
        found.append({
            "kind": "superflex_disagreement",
            "detail": f"{slots.count('QB')} literal QB slots but no SUPER_FLEX token -- this "
                      f"league plays as superflex and every consumer keying off SUPER_FLEX "
                      f"will score it as 1QB",
        })

    # Each key is asked for WHERE IT LIVES, and a scoring key is asked at all only when the
    # league brought no scoring dict -- see the three constants above for why both halves of
    # that matter, and for what the flat version refused.
    missing = [key for key in FORMAT_DECIDING_SETTINGS_KEYS if key not in settings]
    if league.get(TEAM_COUNT_KEY) is None:
        missing.append(TEAM_COUNT_KEY)
    if not scoring:
        missing.extend(FORMAT_DECIDING_SCORING_KEYS)
    if missing:
        found.append({
            "kind": "missing_format_keys",
            "detail": f"{sorted(missing)} absent -- each one silently resolves to a default that "
                      f"describes a DIFFERENT league",
        })
    return found


def confirmation_state(league: Optional[dict]) -> str:
    """CONFIRMED / INFERRED / AMBIGUOUS. Only AMBIGUOUS blocks.

    A person's confirmation does NOT clear an ambiguity, deliberately: confirming is a claim
    about having looked, and the unreadable slot is still unreadable afterwards. Whatever the
    person supplies to resolve it belongs in the config, at which point the detector stops
    firing on its own.
    """
    if ambiguities(league):
        return AMBIGUOUS
    return CONFIRMED if (league or {}).get(CONFIRMED_KEY) else INFERRED


def admits_decision(league: Optional[dict]) -> tuple[bool, Optional[str]]:
    """May a board be built on this config? (ok, reason-if-not).

    Only AMBIGUOUS blocks. Age does NOT block, deliberately: nothing here measures how often a
    commissioner changes a setting, so a cutoff would be an invented magnitude, and a hard
    refusal on an hours-old config would break the ordinary case (sync in the morning, draft in
    the evening) to guard against an unmeasured one. Age is reported; ambiguity is enforced.
    """
    found = ambiguities(league)
    if found:
        return False, ("this league's configuration did not parse cleanly: "
                       + "; ".join(item["detail"] for item in found))
    return True, None


def decision_config(league: Optional[dict]) -> dict:
    """The config, or a refusal. Never a degraded fallback.

    Raises rather than returning something usable-looking, because the failure this guards has
    no symptom: an unreadable slot still yields a board, just one built on a league that is not
    the league being played.
    """
    ok, reason = admits_decision(league)
    if not ok:
        raise ValueError(f"refusing to build a decision on this league config -- {reason}")
    return league


