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

#: Slot codes that are real and hold nobody startable. Sleeper's own vocabulary.
NON_PLAYING_SLOTS = frozenset({"BN", "TAXI", "IR"})

#: The full set of roster_positions labels this app understands, derived from the two
#: vocabularies the engine actually reads plus the non-playing slots. A label outside this set
#: is not "an unknown slot we can ignore" -- it is a slot whose players the lineup solver will
#: silently fail to place, so it makes the config AMBIGUOUS.
KNOWN_SLOTS = frozenset(FANTASY_POSITIONS) | frozenset(FLEX_SLOT_POSITIONS) | NON_PLAYING_SLOTS

#: Scoring/settings keys whose ABSENCE changes what the engine concludes about a league -- not
#: every key it might read. `compute_points_from_stats` iterates whatever it is given, so a
#: missing category there is a smaller projection, not a misread league. These four are
#: different: each one silently resolves to a DEFAULT that describes a different league.
#: Kept in step with sleeper_client.league_format_summary by test_league_config.
FORMAT_DECIDING_KEYS = ("rec", "bonus_rec_te", "type", "num_teams")

CONFIRMED = "confirmed"
INFERRED = "inferred"
AMBIGUOUS = "ambiguous"

#: Set on a config a person has reviewed. Underscore-prefixed so it cannot collide with a key
#: Sleeper itself returns.
CONFIRMED_KEY = "_config_confirmed"


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
        found.append({
            "kind": "unknown_slot",
            "detail": f"roster slot(s) {unknown} are in neither the position vocabulary, the "
                      f"flex vocabulary, nor {sorted(NON_PLAYING_SLOTS)} -- the lineup solver "
                      f"cannot place anyone in them",
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

    missing = [key for key in FORMAT_DECIDING_KEYS
               if key not in scoring and key not in settings]
    if missing:
        found.append({
            "kind": "missing_format_keys",
            "detail": f"{missing} absent -- each one silently resolves to a default that "
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


