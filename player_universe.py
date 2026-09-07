"""Sleeper-first player and league-ownership helpers.

Player identity comes from Sleeper's ``/players/nfl`` database.  League
rosters only describe ownership, and optional vendors can enrich these rows;
neither is allowed to decide whether a player exists in the application.
"""

from __future__ import annotations

from typing import Optional

# Sleeper's database also includes coaches, old placeholders, and retired
# players.  These positions are the player universe this football app can
# meaningfully display, while rostered/projected records are retained even if
# Sleeper has incomplete metadata for them.
FANTASY_POSITIONS = {"QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB"}


FLEX_SLOT_POSITIONS = {
    "FLEX": {"RB", "WR", "TE"},
    "SUPER_FLEX": {"QB", "RB", "WR", "TE"},
    "WRRB_FLEX": {"RB", "WR"},
    "REC_FLEX": {"WR", "TE"},
    "IDP_FLEX": {"DL", "LB", "DB"},
}


def league_usable_positions(roster_positions: list[str]) -> set[str]:
    """Which fantasy position buckets this league's roster slots actually use.

    Sleeper's roster_positions lists literal slot codes (QB, RB, ..., plus flex
    codes like SUPER_FLEX/IDP_FLEX and non-positional slots like BN/TAXI/IR).
    Expand flex slots to the positions they can hold, so a league with no K/DEF/
    IDP slots never suggests free agents in those positions — there's nowhere
    to start them. Falls back to every known position if roster_positions is
    empty/missing, so a malformed league never silently hides every free agent.
    """
    positions: set[str] = set()
    for slot in roster_positions or []:
        if slot in FANTASY_POSITIONS:
            positions.add(slot)
        elif slot in FLEX_SLOT_POSITIONS:
            positions.update(FLEX_SLOT_POSITIONS[slot])
    return positions or set(FANTASY_POSITIONS)


#: Designations this engine has ruled carry NO material information about a player (#191).
#:
#: "Questionable" is not really an injury status: anything can inspire it, and the NFL's own
#: use of it is close to strategic. The engine's own data says the same. Sleeper projects a
#: Questionable player for a FULL SEASON -- of 100 with a games-played projection, 95 carry
#: gp=17 and 5 carry gp=16, indistinguishable from healthy players (700, overwhelmingly gp=17).
#: And the penalty it used to carry, -1.5, moved 99 of 2084 board rows by at most SIX ranks and
#: never touched the top 50. So it was priced precision on a signal that is not there.
#:
#: OUT OF THE ARITHMETIC AND OUT OF THE PROSE, which is the part worth stating plainly. The
#: obvious half-measure -- stop pricing it, keep mentioning it -- was considered and ruled
#: against by the owner: a flag raised to a person is a claim that the fact matters, and
#: repeating a designation the engine has just measured as meaningless spends the reader's
#: attention on noise. Silence is the honest output for a fact that carries nothing.
#:
#: THE CONDITION FOR ITS RETURN, recorded so this is a ruling and not a deletion: historical
#: backing, applied case-specifically. If a record ever shows that THIS player's Questionable
#: designations track missed games or reduced output, that is evidence about him and may be
#: surfaced as such. What may never come back is the blanket constant -- a league-wide
#: magnitude applied to everyone carrying the word (#56: a bound is not a threshold).
#:
#: PASSIVE DISPLAY IS NOT AFFECTED, and the distinction is the whole line this constant draws.
#: A roster table showing what Sleeper says about a player is REPORTING THE FEED. This set
#: governs the places where the ENGINE ITSELF speaks -- what it prices, what it flags as a
#: problem, what it hands a chair as evidence.
IMMATERIAL_INJURY_STATUSES = ("Questionable",)


def is_material_injury_status(status: Optional[str]) -> bool:
    """Should the engine act on, or speak about, this designation at all? (#191)

    False for absence AND for a designation ruled immaterial -- deliberately one predicate, so
    a caller cannot accidentally treat "he is Questionable" as more actionable than "nothing is
    known about him", which is the state it is closest to.
    """
    return bool(status) and status not in IMMATERIAL_INJURY_STATUSES


#: Games a designation GUARANTEES the player misses, taken from the NFL's own roster rules
#: rather than chosen to fit a sample (#191, #56).
#:
#:   IR   -- a player placed on injured reserve and designated to return must miss at least
#:           four games; without the designation it is season-ending, so four is the FLOOR.
#:   PUP  -- regular-season Physically Unable to Perform requires missing at least the first
#:           four games, on the same reading.
#:   Out  -- ruled out for THIS week: one game.
#:
#: Nothing else is here, and the omissions are the disciplined part. "Questionable" and
#: "Doubtful" are game-time calls with no rule floor at all (and Questionable is out of the
#: engine entirely -- see IMMATERIAL_INJURY_STATUSES). "Sus" varies by the length of the
#: suspension, which the feed does not carry. "NA" and "DNR" are not health designations.
#: A number for any of those would be invented, and inventing one is exactly what #56 forbids.
#: The NFL regular season. A fact about the league, not a tuning constant.
SEASON_GAMES = 17

GAMES_MISSED_FLOOR = {"IR": 4, "PUP": 4, "Out": 1}

#: What the engine does with a designation it has never seen. NOT 0.0, which would silently
#: price an unknown as healthy -- the absence contract's whole point (#202). PUP reached the
#: board with no entry anywhere and was treated as fully fit for exactly that reason.
UNRECOGNISED_DESIGNATION = "unrecognised_designation"
NO_DESIGNATION = "no_designation"
RULE_FLOOR = "rule_floor"
IMMATERIAL = "immaterial_designation"
#: A RECOGNISED designation whose haircut could not be computed because the feed reported no
#: games-played for the player. Split from UNRECOGNISED_DESIGNATION deliberately: "we do not
#: know what this designation means" and "we know exactly what it means and lack the
#: denominator" are different absences with different remedies, and collapsing them is the
#: defect this whole item exists to correct.
NO_GAMES_REPORTED = "no_games_reported"


def availability_factor(status: Optional[str], projected_games: Optional[float]):
    """(factor, basis) -- what share of a full-season projection this player can still earn.

    THE COMPANION IS RETURNED WITH THE NUMBER, never separately (#166). A factor of 1.0 means
    four different things -- nobody said anything, the designation carries no information, the
    designation is unrecognised, or games-played was never reported -- and a consumer that
    cannot tell them apart will read the last two as health.

    THE FACTOR IS A BOUND, NOT AN ESTIMATE, and the basis says so. We know a man on IR misses
    AT LEAST four games; we do not know he misses only four. Applying the floor removes the
    part that is certain and fabricates nothing, which is the most that can honestly be taken
    off. Reading it as a point estimate would overstate a season-ending case -- see #188, which
    is the register item for the "bounded/partial" state this vocabulary still lacks.

    `projected_games` is Sleeper's own `gp` for the player. Absent, no factor is computable:
    a share of an unknown denominator is not a quantity.
    """
    if not status:
        return 1.0, NO_DESIGNATION
    if status in IMMATERIAL_INJURY_STATUSES:
        return 1.0, IMMATERIAL
    missed = GAMES_MISSED_FLOOR.get(status)
    if missed is None:
        return 1.0, UNRECOGNISED_DESIGNATION
    if not projected_games or projected_games <= 0:
        return 1.0, NO_GAMES_REPORTED
    # ANCHORED TO THE SEASON, NOT TO gp -- which is what makes the cut SELF-LIMITING.
    #
    # The player will play at most SEASON_GAMES - missed. Sleeper counts `gp`. Only the excess
    # is fabricated, so the factor is what he can play over what Sleeper counted, never > 1.
    #
    # WHY THAT MATTERS, from a live observation the owner made against the running app: Sleeper
    # had NOT yet zeroed James Conner's weeks 2-4, still showing ~3 points in each, and it
    # eventually will. The naive form -- (gp - missed) / gp -- keeps removing four games
    # forever, so the moment Sleeper caught up and dropped gp, the engine would charge the same
    # absence a second time. This form stops on its own:
    #
    #   gp=17 (nothing removed yet)   -> 13/17 = 0.765, the full correction
    #   gp=16 (one game already gone) -> 13/16 = 0.813, correspondingly smaller
    #   gp<=13 (the feed has caught up) -> 1.0, no cut at all
    playable = max(SEASON_GAMES - missed, 0.0)
    return min(playable / projected_games, 1.0), RULE_FLOOR


def player_position(info: dict) -> Optional[str]:
    """The fantasy-relevant position bucket for a player, Sleeper's own way.

    Sleeper's granular ``position`` field can be an IDP sub-position (DE, DT,
    OLB, ILB, CB, S, FS, SS, ...) that doesn't match any roster slot this app
    (or most leagues) actually use. ``fantasy_positions`` is Sleeper's own
    pre-bucketed list for exactly this purpose — e.g. a "FS" cornerback's
    fantasy_positions is ["DB"] — so prefer it, falling back to the raw
    position only when fantasy_positions is missing or empty.
    """
    for pos in info.get("fantasy_positions") or []:
        if pos in FANTASY_POSITIONS:
            return pos
    return info.get("position")


def player_eligible_positions(info: dict) -> set[str]:
    """The FULL set of fantasy-relevant positions this player can be started at, not just the
    single bucket player_position() picks -- needed anywhere a player's multi-position
    eligibility itself is the point (lineup_optimizer.py's assignment problem), rather than
    everywhere else in this app, which only ever needs one primary bucket for matching/
    grouping purposes. Falls back to {player_position(info)} when fantasy_positions is
    missing/empty, so a record with no real eligibility data still gets its one known
    position rather than an empty, unassignable set."""
    eligible = {pos for pos in (info.get("fantasy_positions") or []) if pos in FANTASY_POSITIONS}
    if eligible:
        return eligible
    primary = player_position(info)
    return {primary} if primary else set()


def score_projection(stats: dict, scoring_settings: dict) -> float:
    # Not module-private -- draft_room.py reuses this to score Sleeper's native weekly
    # projections under a league's real scoring rules for positions Draft Sharks doesn't
    # project at all (currently IDP), same as this module already does for roster display.
    """Score native Sleeper stat projections without coupling this data model to HTTP."""
    total = sum(
        float(value) * float(scoring_settings.get(category, 0))
        for category, value in (stats or {}).items()
        if value
    )
    return round(total, 2)


def player_name(info: dict, player_id: str) -> str:
    """Return a usable Sleeper name, including for incomplete player records."""
    return (
        info.get("full_name")
        or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
        or player_id
    )


def _roster_slots(roster: dict) -> dict[str, str]:
    starters = set(roster.get("starters") or [])
    taxi = set(roster.get("taxi") or [])
    reserve = set(roster.get("reserve") or [])
    return {
        str(pid): "TAXI" if pid in taxi else "IR" if pid in reserve else "Starter" if pid in starters else "Bench"
        for pid in (roster.get("players") or [])
    }


def build_player_universe(
    players_db: dict[str, dict],
    rosters: list[dict],
    *,
    users: Optional[list[dict]] = None,
    projections: Optional[dict[str, dict]] = None,
    scoring_settings: Optional[dict] = None,
    include_inactive: bool = False,
) -> list[dict]:
    """Build canonical Sleeper player rows with separate league ownership.

    ``players_db`` remains authoritative for player identity.  Roster and
    projection IDs are unioned in so a temporarily incomplete player database
    can never hide a player who is actually rostered or projected.  By default
    the returned view is useful for fantasy decisions (active players plus all
    rostered/projected players); pass ``include_inactive=True`` to inspect the
    entire cached Sleeper database.
    """
    projections = projections or {}
    owner_names = {
        str(user.get("user_id")): user.get("display_name") or user.get("metadata", {}).get("team_name")
        for user in (users or [])
    }
    ownership: dict[str, dict] = {}
    rostered_ids: set[str] = set()
    for roster in rosters or []:
        for pid, slot in _roster_slots(roster).items():
            rostered_ids.add(pid)
            ownership[pid] = {
                "roster_id": roster.get("roster_id"),
                "owner_id": roster.get("owner_id"),
                "owner_name": owner_names.get(str(roster.get("owner_id"))) or f"Roster {roster.get('roster_id', '?')}",
                "roster_slot": slot,
            }

    player_ids = set(map(str, players_db or {})) | rostered_ids | set(map(str, projections))
    rows: list[dict] = []
    for pid in player_ids:
        info = (players_db or {}).get(pid, {}) or {}
        position = player_position(info)
        is_rostered_or_projected = pid in rostered_ids or pid in projections
        if position not in FANTASY_POSITIONS and not is_rostered_or_projected:
            continue
        # Do not make "active" a destructive truth source on its own: some Sleeper
        # rows omit it even for currently-relevant players, and a rostered/projected
        # player always remains visible regardless. But active=None combined with no
        # current NFL team is Sleeper's tell for a long-retired player it never
        # purges (Sleeper's /players/nfl keeps essentially every player who ever
        # appeared, going back years) — that combination is what actually needs
        # filtering. A real, currently-relevant free agent (cut, unsigned, between
        # teams — Sleeper still marks these active=true even with no team) is a
        # legitimate roster target and stays visible either way.
        is_retired_or_stale = info.get("active") is False or (
            info.get("active") is None and not info.get("team")
        )
        if not include_inactive and is_retired_or_stale and not is_rostered_or_projected:
            continue
        row = {
            "player_id": pid,
            "name": player_name(info, pid),
            "position": position or "Unknown",
            "team": info.get("team") or "FA",
            "injury_status": info.get("injury_status"),
            "active": info.get("active"),
            "status": info.get("status") or "unknown",
            "ownership": "ROSTERED" if pid in ownership else "FREE AGENT",
            "available": pid not in ownership,
            # Sleeper has no public ADP or season-total-projection endpoint, but
            # search_rank (lower = more universally relevant/rosterable) is the
            # closest thing it exposes natively — good enough to order a free
            # agent list by something better than alphabetical with zero setup.
            "search_rank": info.get("search_rank"),
            **ownership.get(pid, {}),
        }
        stats = projections.get(pid)
        if stats:
            row["sleeper_proj"] = score_projection(stats, scoring_settings or {})
        rows.append(row)

    # Player names make the canonical pool searchable even when position/team
    # metadata lags during an NFL transaction.
    return sorted(rows, key=lambda row: (row["position"], row["name"].lower(), row["player_id"]))


def available_players(universe: list[dict], position: Optional[str] = None) -> list[dict]:
    """Return only unrostered Sleeper players, retaining missing enrichment.

    Retired players are already excluded upstream in build_player_universe, not
    here — a real NFL free agent (cut, unsigned, between teams) is still a
    legitimate roster target and stays in this list regardless of whether they
    currently have a team.
    """
    result = [row for row in universe if row.get("available")]
    if position:
        result = [row for row in result if row.get("position") == position]
    return result


def matching_players(universe: list[dict], query: str, limit: int = 12) -> list[dict]:
    """Find likely player mentions without requiring a vendor-name match."""
    query_words = {word.lower() for word in query.replace("'", " ").split() if len(word) > 1}
    if not query_words:
        return []
    matches = []
    for row in universe:
        name_words = set(row["name"].lower().replace("'", " ").split())
        overlap = len(query_words & name_words)
        if overlap:
            matches.append((overlap, row))
    return [row for _, row in sorted(matches, key=lambda item: (-item[0], item[1]["name"]))[:limit]]
