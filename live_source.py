"""`#356`: live state -> the shape the builders consume, and the vocabulary that keeps a wiring
error from looking like good behaviour.

THE DEFECT THIS EXISTS TO PREVENT, stated first because the whole design follows from it.

`#187` says an absence renders as an em dash CARRYING ITS REASON, never as a 0. That protects a
reader from an invented number and gives them **no protection at all** from a field that should
have arrived and did not. Read the wrong Sleeper key and `league.name` comes back `None`, and the
page renders

    — (this capture carries a league CONFIG but no league name)

which is indistinguishable from the contract working perfectly. The owner loads their league, sees
a tidy labelled absence, and has no way to tell it from a bug. **The absence contract can mask a
wiring error**, and it will do so silently and forever.

So a source must say not just THAT a field is missing but WHY IT IS ENTITLED TO BE:

    MEASURED     the source supplied it
    STRUCTURAL   this source genuinely cannot supply it -- a replayed draft has no submitted
                 lineup, so `starters` is not a defect, it is the shape of the data
    READ_FAILED  the source IS expected to supply it and did not. NOT an em dash. Loud.
    NOT_COMPUTED supplied, but a claim derived from it was deliberately NOT built, with the
                 reason attached

That distinction is impossible to draw from the data alone: `None` looks the same either way. It
comes from `EXPECTS` below -- per SOURCE KIND, the fields that source owes. A snapshot owes a
league name because every Sleeper league has one; a fixture does not, because a replayed draft
never had one.

WHY `NOT_COMPUTED` IS A SEPARATE STATE FROM AN ABSENCE, and it is `#346` again.

`bye_collision` and `bye_concentration` take a priced roster and build a maximisation by negating
`value`. Hand them rows whose `value` is the neutral `0.0` that unpriced rows carry, and they
return `value_lost: 0.0` for every week -- a measured-looking zero that actually means "nothing was
priced". That is exactly the defect `#346` fixed at source, re-entering through a different door.

So `bye_profile` IS NOT COMPUTED unless every row is priced, and the refusal is in the code rather
than in my memory of it. A caller cannot opt out.

WHAT THIS MODULE DOES NOT DO (`#338`): it computes no claim the engine computes. It assembles the
engine's own inputs, calls the engine's own functions, and labels what came back. `structural_holes`
is `lineup_optimizer.slot_coverage`'s answer, not a count this file derived.
"""
from __future__ import annotations

import dataclasses
import json
import pathlib
import time
from typing import Any

import lineup_optimizer as lo
import player_universe as pu

ROOT = pathlib.Path(__file__).resolve().parent
SNAPSHOT_DIR = ROOT / "data" / "sleeper_snapshots"

MEASURED = "measured"
STRUCTURAL = "structurally_absent"
READ_FAILED = "read_failed"
NOT_COMPUTED = "not_computed"

#: Per SOURCE KIND, the fields that source OWES. A field absent from its own source's debts is
#: structurally absent and renders per `#187`; a field IN this set that did not arrive is a
#: READ_FAILED and must be loud.
#:
#: This table is the only thing that can tell the two apart, which is why it is data and not a
#: series of conditionals: a reader can check it against Sleeper's API in one sitting.
EXPECTS = {
    "snapshot": frozenset({"league_name", "current_week", "record", "starters", "team",
                           "roster", "roster_positions"}),
    "fixture": frozenset({"roster", "roster_positions"}),
}


@dataclasses.dataclass(frozen=True)
class Field:
    """One field, its value, and the state that says how to render it."""
    name: str
    value: Any
    state: str
    why: str = ""

    @property
    def loud(self) -> bool:
        """Whether this must NOT be drawn as a quiet em dash."""
        return self.state == READ_FAILED


@dataclasses.dataclass(frozen=True)
class Report:
    """What a source yielded, field by field. The owner's first diagnostic."""
    kind: str
    identifier: str
    fields: tuple[Field, ...]
    synced_at: float | None = None

    def by_name(self, name: str) -> Field | None:
        return next((f for f in self.fields if f.name == name), None)

    @property
    def failures(self) -> tuple[Field, ...]:
        """Every field the source owed and did not deliver. Non-empty means a WIRING ERROR."""
        return tuple(f for f in self.fields if f.state == READ_FAILED)

    @property
    def verdict(self) -> str:
        if self.failures:
            return f"WIRED WRONG -- {len(self.failures)} expected field(s) did not arrive"
        return "every expected field arrived"

    def as_rows(self) -> list[dict]:
        """Flat rows for the status surface. Data, never prose assembled here (`#338`)."""
        return [{"field": f.name, "state": f.state, "why": f.why,
                 "present": f.value is not None} for f in self.fields]


def _state_for(name: str, value: Any, kind: str, why_structural: str = "") -> Field:
    """The one place the three absence states are decided."""
    if value is not None and value != [] and value != {}:
        return Field(name, value, MEASURED)
    if name in EXPECTS.get(kind, frozenset()):
        return Field(name, None, READ_FAILED,
                     f"a {kind} source is expected to carry {name} and it did not arrive -- "
                     f"this is a defect in the read, not an absence in the data")
    return Field(name, None, STRUCTURAL, why_structural or f"a {kind} source has no {name}")


def roster_rows(player_ids: list[str], players_db: dict, byes: dict) -> list[dict]:
    """The row shape every solver here indexes directly, built once.

    `eligible` IS A SET, not its repr. The capture's own serializer turns a set into `"{'RB'}"`
    via `default=str` (`#351`), and `slot_coverage` does `player["eligible"] & slot["eligible"]`,
    which raises `TypeError: unsupported operand type(s) for &: 'str' and 'set'`. Built in memory
    here, so the string never exists.

    `value` is 0.0 and `priced` is False for every row: THIS FUNCTION PRICES NOTHING. The pair is
    `#346`'s companion-field shape (`#190`) -- the neutral number the solvers need, with the real
    fact beside it. Any caller that wants a priced row must price it and set both.
    """
    rows = []
    for pid in player_ids or []:
        info = (players_db or {}).get(str(pid)) or {}
        team = info.get("team")
        rows.append({
            "id": str(pid),
            # `pu.player_name` IS THE ONE HOME for this (`#126`). The first draft spelled it
            # `full_name or last_name or id` inline, which is a SECOND IMPLEMENTATION of a
            # derivation the repo already owns -- and the two disagree. Measured: against a
            # 15-player roster chosen so every member IS in the rankings, the inline spelling
            # priced 11 while `player_name` priced all 15, because `merge_player` matches on the
            # name string. Four players silently unpriced, each of them then a measured-looking
            # 0.0 the bye guard has to refuse.
            "name": pu.player_name(info, str(pid)),
            "position": pu.player_position(info),
            "team": team,
            "bye": (byes or {}).get(team),
            "value": 0.0,
            "priced": False,
            "eligible": set(pu.player_eligible_positions(info)),
        })
    return rows


def holes_from(rows: list[dict], roster_positions: list[str]) -> list[str]:
    """`structural_holes` -- the engine's answer, not a count derived here.

    `slot_coverage` takes NO `value` by design: whether a player is legal in a slot has nothing
    to do with his price, so this claim is computable from an unpriced roster. That is why it is
    the one claim this pass can supply from a snapshot.
    """
    slots = lo.slots_from_roster_positions(list(roster_positions or []))
    if not slots:
        return []
    cover = lo.slot_coverage([{"id": r["id"], "eligible": r["eligible"]} for r in rows], slots)
    occupied = {a["slot_id"] for a in cover["occupied"]}
    return sorted({s["label"] for s in slots if s["slot_id"] not in occupied})


def bye_profile_from(rows: list[dict], roster_positions: list[str]) -> tuple[dict | None, str]:
    """`bye_profile`, or a REFUSAL carrying its reason. Never a profile built from zeros.

    THE REFUSAL IS THE POINT. `bye_collision` negates `value` to build a maximisation, so an
    unpriced roster -- every row at the neutral 0.0 -- returns `value_lost: 0.0` for every week.
    That is a measured-looking zero meaning "nothing was priced", which is `#346`'s defect
    arriving through a different door. The guard is here, in the code, so a caller cannot reach
    the wrong answer by forgetting.
    """
    unpriced = [r for r in rows if not r.get("priced")]
    if unpriced:
        return None, (f"{len(unpriced)} of {len(rows)} rostered players are unpriced, and "
                      f"`bye_collision` negates `value` to build its maximisation -- an unpriced "
                      f"roster returns a loss of 0.0 for every week, which reads as a measured "
                      f"zero (`#346`). Pricing is not wired in this pass")
    if not rows:
        return None, "no rostered players"
    shape = lo.bye_concentration(rows, list(roster_positions or []))
    weeks = lo.bye_collision(rows, list(roster_positions or []))
    worst = max(weeks, key=lambda w: weeks[w]["value_lost"]) if weeks else None
    return {
        "weeks": {str(w): rec["value_lost"] for w, rec in weeks.items()},
        "worst_week": int(worst) if worst is not None else None,
        "worst_week_loss": weeks[worst]["value_lost"] if worst is not None else None,
        "worst_week_detail": weeks.get(worst) if worst is not None else None,
        "concentration": shape.get("concentration"),
        "total_loss": sum(rec["value_lost"] for rec in weeks.values()),
    }, ""


def from_snapshot(snap: dict, players_db: dict, byes: dict,
                  owner_id: str | None = None, merger=None) -> tuple[dict, Report]:
    """A snapshot `sleeper_client.sync_league` wrote -> the fixture shape, plus its report.

    The snapshot is READ, never written. This module holds no lock and performs no mutation,
    which is what makes a reader safe beside `app.py`'s single writer (`#354`).
    """
    kind = "snapshot"
    league = (snap or {}).get("league") or {}
    rosters = (snap or {}).get("rosters") or []
    users = (snap or {}).get("users") or []
    nfl = (snap or {}).get("nfl_state") or {}

    mine = next((r for r in rosters if owner_id and r.get("owner_id") == owner_id),
                rosters[0] if rosters else {})
    user = next((u for u in users if u.get("user_id") == mine.get("owner_id")), {})
    settings = mine.get("settings") or {}
    wins, losses = settings.get("wins"), settings.get("losses")

    positions = league.get("roster_positions") or []
    rows = roster_rows(mine.get("players") or [], players_db, byes)

    # WITH A MERGER, THE EXPENSIVE CLAIMS BECOME AVAILABLE. Without one the page still renders,
    # and the two claims it cannot make say so rather than reporting a measured-looking zero.
    thin: list[dict] = []
    thin_state, thin_why = NOT_COMPUTED, (
        "positional depth needs the priced universe (`depth_chart.positional_depth` over a "
        "merger-backed pool); no merger was supplied to this read")
    if merger is not None:
        # The contest is counted over EVERY player identified in this league, not over the one
        # roster being rendered -- counting over the rendered roster alone is the original
        # defect, where the contest evaporates if the other claimant sits elsewhere.
        league_rows = []
        for other in rosters:
            league_rows.extend(roster_rows(other.get("players") or [], players_db, byes))
        rows = price_rows(rows, merger, contested_keys(league_rows, merger))
        thin, _my_key, join_fail = priced_claims(snap, players_db, merger, owner_id)
        if join_fail:
            # A MISSED JOIN IS A WIRING ERROR, NOT AN ABSENCE, and this is the one place the
            # distinction is load-bearing: an empty depth row renders as "no thin positions",
            # which is a page that looks healthy and is lying.
            thin, thin_state, thin_why = [], READ_FAILED, join_fail
        else:
            thin_state, thin_why = MEASURED, ""

    holes = holes_from(rows, positions)
    profile, refusal = bye_profile_from(rows, positions)

    fields = [
        _state_for("league_name", league.get("name"), kind),
        _state_for("current_week", nfl.get("week"), kind),
        _state_for("team", user.get("display_name"), kind),
        _state_for("roster", mine.get("players") or None, kind),
        _state_for("roster_positions", positions or None, kind),
        _state_for("starters", mine.get("starters") or None, kind),
        _state_for("record", f"{wins}-{losses}" if wins is not None and losses is not None
                   else None, kind),
        Field("structural_holes", holes, MEASURED),
        (Field("bye_profile", profile, MEASURED) if profile is not None
         else Field("bye_profile", None, NOT_COMPUTED, refusal)),
        (Field("thin_positions", thin, MEASURED) if thin_state == MEASURED
         else Field("thin_positions", None, thin_state, thin_why)),
    ]
    report = Report(kind, str(league.get("league_id") or "?"), tuple(fields),
                    (snap or {}).get("synced_at"))

    fx = {
        "league": {"roster_positions": positions,
                   "starting_slots": len(lo.slots_from_roster_positions(list(positions)))},
        "league_name": league.get("name"),
        "team": user.get("display_name"),
        "record": report.by_name("record").value,
        "current_week": nfl.get("week"),
        "roster": [{k: (sorted(v) if isinstance(v, set) else v) for k, v in r.items()}
                   for r in rows],
        "structural_holes": holes,
        "_provenance": {"source": kind, "synced_at": (snap or {}).get("synced_at"),
                        "basis": {f.name: f.state for f in fields}},
    }
    # `thin_positions` AND `bye_profile` ARE OMITTED, NOT EMPTIED, and the difference is the
    # whole contract. `checks_run`'s docstring states the grammar: "`[]` is a measured empty
    # result -- holes were counted, there were none -- while a missing key or `None` never ran. A
    # caller that hands `[]` for something it did not measure has broken the absence contract AT
    # THE PRODUCER, and that is its defect to fix, not this function's to guess around."
    #
    # The first draft of this function wrote `"thin_positions": []`, and `checks_run` duly
    # reported the depth check CLEAN on a check that had never run -- which would have let a
    # league with no structural holes render as "nothing open" while two of three checks were
    # never performed. Caught by running it, and it is the producer-side half of the same defect
    # this module's own vocabulary exists to name.
    #
    # `structural_holes` stays as a list including when empty, because it WAS measured: an empty
    # list there is the honest answer.
    if profile is not None:
        fx["bye_profile"] = profile
    if thin_state == MEASURED:
        # A list, including when empty: depth WAS measured, so `[]` is the honest answer and
        # `checks_run` must see the depth check as having RUN.
        fx["thin_positions"] = thin
    return fx, report


def from_fixture(path: pathlib.Path) -> tuple[dict, Report]:
    """A committed fixture -> itself, plus a report that says so.

    Exists so the seam is verifiable WITHOUT a real league, and so the status surface can never
    be ambiguous about which it is showing. A page rendered from a fixture that does not SAY it
    came from a fixture is the `#332` stale-page defect with a live server attached.
    """
    kind = "fixture"
    fx = json.loads(path.read_text())
    basis = ((fx.get("_provenance") or {}).get("basis") or {})
    fields = [
        _state_for("league_name", fx.get("league_name"), kind,
                   basis.get("league_name", "a battery arm is not a league's name")),
        _state_for("current_week", fx.get("current_week"), kind,
                   basis.get("current_week", "a replayed draft has no point in the season")),
        _state_for("team", fx.get("team"), kind, basis.get("team", "")),
        _state_for("roster", fx.get("roster") or None, kind),
        _state_for("roster_positions", (fx.get("league") or {}).get("roster_positions") or None,
                   kind),
        _state_for("starters", fx.get("starters"), kind,
                   basis.get("starters", "a drafted roster has no submitted lineup")),
        _state_for("record", fx.get("record"), kind,
                   basis.get("record", "no capture holds a result")),
        _state_for("structural_holes", fx.get("structural_holes"), kind),
        _state_for("bye_profile", fx.get("bye_profile"), kind),
        _state_for("thin_positions", fx.get("thin_positions"), kind),
    ]
    return fx, Report(kind, path.name, tuple(fields), None)


def snapshot_path(league_id: str) -> pathlib.Path:
    return SNAPSHOT_DIR / f"{league_id}_latest.json"


def available_snapshots() -> list[str]:
    """League ids with a snapshot on disk. Empty is the normal state of a fresh checkout."""
    if not SNAPSHOT_DIR.exists():
        return []
    return sorted(p.name[: -len("_latest.json")]
                  for p in SNAPSHOT_DIR.glob("*_latest.json"))


def age_seconds(synced_at: float | None, now: float | None = None) -> float | None:
    """Freshness, or None. NOT rendered as 0 when unknown (`#187`)."""
    if synced_at is None:
        return None
    return max(0.0, (time.time() if now is None else now) - float(synced_at))


# ---------------------------------------------------------------------------------------------
# PRICING (`#359`) -- assembled in PRODUCTION'S SHAPE, because the shape is what goes wrong.
#
# The engine-measurement skill's whole subject is that every measurement error in this repo was a
# FIXTURE error, not a reasoning error: the harness silently produced a plausible number about
# something else. So this copies the production caller (`ui_explore/capture_front_fixture.py`)
# rather than assembling an input that merely looks right. Four things it insists on:
#
#   1. `build_players_db_from_capture`, never `build_players_db` -- 6,594 rows in Sleeper's id
#      space versus a 764-row VENDOR RECONSTRUCTION whose 373 colliding ids are DIFFERENT PLAYERS.
#   2. `set_league_format` BEFORE anything is priced. `rec` and `bonus_rec_te` do NOT propagate
#      through `scoring_settings` into valuation -- they propagate by FILE SELECTION. A battery
#      that skipped this drafted 32 formats from one export and returned standard / half_ppr /
#      ppr BYTE-IDENTICAL; nine of thirteen findings were artifacts.
#   3. The hint is DERIVED from the league's own settings (`league_format_hint`), never carried
#      alongside -- a hint that can disagree with its league is a second source of truth.
#   4. Season projections and the universe come from the SAME capture.
#
# A LIVE LEAGUE SUPPLIES ITS OWN SCORING. The capture reads `scoring_settings_from_capture()`
# because a battery arm has no league behind it; a snapshot carries the real
# `league["scoring_settings"]`, which is the whole point of `#341`'s currency ruling.


def contested_keys(all_rows: list[dict], merger) -> set:
    """Vendor records that MORE THAN ONE identified player resolves onto.

    THE DEFECT THIS EXISTS FOR, measured on the committed rankings. `merge_player("Bijan
    Robinson", RB, ATL)` and `merge_player("Brian Robinson", RB, ATL)` BOTH return
    `trade_value=99.0`: the vendor publishes one `B Robinson RB ATL` row between two real men,
    no name/position/team test can split it, and the board therefore refuses that number to
    both (`_drop_contested_identities`). A direct `merge_player` call does not -- which is
    exactly the historical bug the invariant registry records: "`_team_roster_players`
    re-resolves each rostered player through the MERGER, where the contested price still sits,
    so a player drafted out of a contested pair kept the very number the pool refused him."

    `price_rows` was that same shape, and shipped the same 99.0 to both Robinsons until the
    registry's census moved and said so.

    THE POPULATION IS EVERY PLAYER IDENTIFIED IN THE LEAGUE, not the one roster being rendered.
    Counting over my own fifteen rows would reproduce the original defect precisely: the contest
    would EVAPORATE whenever the other claimant sat on somebody else's roster, which is the
    common case. Counted over every rostered player in the snapshot, Bijan and Brian contest
    each other wherever either one sits.

    IT IS STILL NARROWER THAN THE POOL'S, and that is stated rather than papered over: the board
    counts over the identified universe, this counts over the league's identified players. A
    contest with a player on NO roster in this league is invisible here. That residue is
    recorded at `#360` rather than silently accepted -- it is smaller than the defect it
    replaces, and it is not zero.
    """
    seen: dict = {}
    for row in all_rows:
        got = merger.merge_player(row["name"], position=row.get("position"),
                                  team=row.get("team")) or {}
        key = got.get("match_canonical_key")
        if key is None:
            continue
        seen.setdefault(key, set()).add(row["id"])
    return {key for key, ids in seen.items() if len(ids) > 1}


def price_rows(rows: list[dict], merger, contested: set | None = None) -> list[dict]:
    """`#346`'s companion-field shape, applied to live rows. Returns NEW rows.

    `is not None`, NOT truthiness: a player genuinely valued at 0.0 IS priced, and `or 0.0` is
    exactly what erased that distinction. The numeric field keeps a number because the solvers
    negate it; `priced` travels beside it carrying what the number cannot (`#190`).

    A CONTESTED RESOLUTION IS REFUSED, not borrowed. What is declined is the PRICE, never the
    player (`#196`): the row survives, keeps its identity and its eligibility, and is simply
    unpriced -- a state the solvers already handle and the page already renders honestly.
    """
    contested = contested or set()
    out = []
    for row in rows:
        got = merger.merge_player(row["name"], position=row.get("position"),
                                  team=row.get("team")) or {}
        tv = got.get("trade_value")
        if got.get("match_canonical_key") in contested:
            tv = None          # neither claimant may keep the one record's numbers
        out.append({**row,
                    "value": float(tv) if tv is not None else 0.0,
                    "priced": tv is not None})
    return out


def thin_from_depth(depth: dict, my_key: str) -> list[dict]:
    """The thin-position claims, derived by the engine's own labeller.

    `valued_count` travels WITH `count` because they describe different sets: every rostered
    player raises count, only the priced ones raise value. `depth_label` ranks on `value` and
    never looks at `valued_count`, so a room weak only because its coverage is partial is
    labelled weak all the same -- a consumer holding both numbers can say so (`#190`/`#339`).
    """
    import depth_chart
    import depth_ratings
    thin = []
    for position in sorted(depth.get(my_key, {})):
        peers = [cells[position] for cells in depth.values() if position in cells]
        label = depth_ratings.depth_label(depth[my_key][position], peers)
        if label in depth_ratings.THIN_LABELS:
            cell = depth[my_key][position]
            thin.append({"position": position, "label": label, "count": cell["count"],
                         "valued_count": cell.get("valued_count"),
                         "value_label": depth_chart.depth_value_label(cell)})
    return thin


def depth_key(roster: dict, user: dict) -> str:
    """Whose roster the page is about, spelled the way `positional_depth` keys its chart.

    It keys on `owner_name or f"Roster {roster_id}"`. A MISSED users->owner_id JOIN therefore
    yields `{}` for this key, which reads downstream as "no thin positions and every slot
    unfillable" -- the most alarming page this surface can draw, produced by a lookup miss. The
    capture asserts loudly here; this returns the key and the CALLER checks membership, so the
    miss becomes a `read_failed` rather than a traceback or, worse, a quiet lie.
    """
    return (user or {}).get("display_name") or f"Roster {(roster or {}).get('roster_id')}"


def priced_claims(snap: dict, players_db: dict, merger, owner_id: str | None = None):
    """-> (thin_positions, my_key, failure) for one league, or a stated failure.

    THE MERGER IS MUTATED HERE (`set_league_format`), so a caller sharing one merger across
    threads must serialise this call. `server.Engine` holds it under a lock for exactly that
    reason: one process does not mean serialised writes once threads are involved.
    """
    import draft_battery as db
    import depth_chart
    import player_universe as pu_

    league = (snap or {}).get("league") or {}
    rosters = (snap or {}).get("rosters") or []
    users = (snap or {}).get("users") or []
    if not rosters:
        return [], "", "the snapshot carries no rosters"

    merger.set_league_format(db.league_format_hint(league))   # BEFORE anything is priced

    mine = next((r for r in rosters if owner_id and r.get("owner_id") == owner_id), rosters[0])
    user = next((u for u in users if u.get("user_id") == mine.get("owner_id")), {})
    my_key = depth_key(mine, user)

    universe = pu_.build_player_universe(
        players_db, rosters, users=users,
        projections=(snap or {}).get("season_projections") or None,
        scoring_settings=league.get("scoring_settings"))
    depth = depth_chart.positional_depth(universe, merger)
    if my_key not in depth:
        return [], my_key, (
            f"the depth chart has no row for {my_key!r} -- the users->owner_id join missed, and "
            f"an empty row reads downstream as 'no thin positions and every slot unfillable'. "
            f"Keys present: {sorted(depth)[:4]}")
    return thin_from_depth(depth, my_key), my_key, ""
