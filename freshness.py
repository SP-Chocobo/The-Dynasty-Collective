"""#300 / `#137`: the freshness manifest, lifted out of the hull so it can be READ without Streamlit.

WHY THIS ONE, AND WHY NOW. `app.py:3484` already calls this with `st.session_state.league_snapshot
or {}` -- a deliberate affordance so the Data Freshness grade renders before any league is synced,
with its own comment saying the grade is "informational only, not a gate". That makes it the one
piece of real content the app can honestly show in the EMPTY state, which is the state the front
page (`ui_explore/round2/MAIN_PAGE.md`) exists to replace. A front-page fixture cannot compute it
while it lives inside a module whose import runs `st.set_page_config`.

WHAT MOVED AND WHAT DID NOT. The function, verbatim, by AST span -- not retyped. Every comment it
carries (`#140` on the calendar-date boundary, `#118` on the players database, MANDATE 2.1(c) on
the season sums) moved with it, because each one records a measurement that is the reason a line
exists. `recency_grade`, which turns this manifest into the single letter grade, already lived in
`data_merger`; it is not duplicated here.

WHAT THIS BUYS, MEASURED. `boundary_census` counted 43 data-layer reaches in `app.py`. Two of them
-- `sleeper_client.players_freshness_entry` and `sleeper_client.season_projection_freshness_entry`
-- were inside this function, so the hull now reaches the data layer 41 times. Shrinkage is the
project working, in that file's own words.

IT IMPORTS NO UI. `league_config`, `sleeper_client` and `data_merger` all carry zero top-level
`import streamlit` (checked, not assumed), and `DataMerger` is needed only for the annotation, so
it is deferred under `TYPE_CHECKING`. `test_freshness.py`'s `ItCanBeImportedWithoutTheUI` holds
that: it imports this module in a subprocess -- this process's own `sys.modules` would decide the
answer otherwise -- and fails if `streamlit`, `app` or even `data_merger` ends up loaded.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

import league_config
import sleeper_client

if TYPE_CHECKING:  # annotation only -- importing DataMerger at runtime would pull the data layer
    from data_merger import DataMerger


def build_freshness_manifest(snapshot: dict, merger: DataMerger) -> list[tuple[str, Optional[str], Optional[int]]]:
    """(label, as-of date, days old) for every dated source in this context, freshest first."""
    entries = []
    if merger.is_loaded:
        entries.append(("Draft Sharks Dynasty Rankings", merger.freshest_date, merger.staleness_days))
    if merger.is_free_agents_loaded:
        entries.append(("Draft Sharks Free Agent Finder", merger.free_agents_freshest_date, merger.free_agents_staleness_days))
    if merger.is_trade_values_loaded:
        entries.append(("Draft Sharks Trade Value Chart", merger.trade_values_freshest_date, merger.trade_values_staleness_days))
    synced_at = snapshot.get("synced_at")
    if synced_at:
        sync_dt = datetime.fromtimestamp(synced_at)
        # #140: the DAYS column is a difference of calendar dates, which is wrong in both
        # directions at the boundary -- measured: a 9am sync read at 8pm reports "0 days" for
        # an eleven-hour-old config, and a 23:59 sync read at 00:01 reports "1 day" for a
        # two-minute-old one. League config changes on an hours timescale (a commissioner
        # edits scoring or a roster slot), so the label carries the real age at a resolution
        # that can express it. The days column keeps its existing meaning and sort order --
        # every other row in this manifest is a source with a genuine per-DAY date, and
        # changing the column's unit for one row would make the sort compare two things.
        entries.append((
            f"Sleeper league sync (rosters + native weekly projections) — "
            f"{league_config.describe_config_age(snapshot)}",
            sync_dt.date().isoformat(),
            (datetime.now().date() - sync_dt.date()).days,
        ))
    # #118: the players database decides who exists, what position they play, and whether they
    # are hurt -- an input to every board on every screen, and the one input this manifest did
    # not mention. Silence here is not neutral: get_players falls back to an arbitrarily old
    # cache when a live fetch fails, so "the app is running" never implied "the player universe
    # is current". Unconditional, ABSENT included; sleeper_client owns what each state means.
    entries.append(sleeper_client.players_freshness_entry())
    # MANDATE 2.1(c): the SUMS the board prices from, not just the sync that fetched them. This
    # manifest listed the sync as the freshest input on the page while the totals that sync
    # returned could be nine weeks of eighteen -- and a board priced from those is a different
    # board (measured: 30 of the top 40 rows move 3+ places). Unconditional, for the same reason
    # the players row above is: an input that is silently missing looks exactly like one that is
    # fine. sleeper_client owns what each state means.
    entries.append(sleeper_client.season_projection_freshness_entry(snapshot))
    entries.sort(key=lambda e: (e[2] is None, e[2]))
    return entries
