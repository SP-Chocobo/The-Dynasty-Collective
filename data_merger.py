"""
Draft Sharks / War Room projection parser and merger.

Reads locally-saved premium exports (Draft Sharks 3D projections, War Room
tiers, FantasyPros, Dynasty Process, etc.) and fuzzy-matches them onto
Sleeper player records by name. Nothing here ever calls out to a paid
vendor's API — the files stay local, satisfying each vendor's terms of
service.

Draft Sharks' tools split cleanly into three categories, and DataMerger
stores them accordingly:

  * The "Dynasty Rankings" tool -> parse_draftsharks_pdf(): a format-based
    overall ranking (1yr proj, 3yr proj, 3D Value) — computed from PPR/
    standard, superflex/1QB, TE-premium assumptions, not from any specific
    league's roster. The *same* export is correct for every league sharing
    that format, so it lives in a shared pool (GLOBAL_PROJECTIONS_DIR,
    data/projections/_global/) rather than being re-uploaded per league.
  * The "Trade Value Chart" tool -> parse_draftsharks_trade_value_chart_pdf():
    also format-based (same sharing rule as Dynasty Rankings) but a
    different shape — it prices players, this year's rookie pick slots
    (1.01-4.12), and generic future picks ("2027 Random Rd 1") all on one
    comparable 0-100 scale, stored separately as DataMerger.trade_values
    rather than merged into .projections. A rookie pick slot's own value
    already reflects that year's class strength -- there's no separate
    "how good is this rookie class" tool to parse. This is PRICE ONLY: pick
    *ownership* is Sleeper's traded-picks data to say, never Draft Sharks',
    whose pick imports can be unreliable.
  * The "Free Agent Finder" tool -> parse_draftsharks_free_agents_pdf(): a
    rest-of-season, this-league-contextual view (3D Proj, 3D ROS, Ceiling,
    3D Value+) that also tags each row Mine/Add/Drop/Lock, i.e. whether
    Draft Sharks considers the player already on *your* roster in *this*
    league. This can never be shared — DataMerger only ever loads it from
    one league's own folder (data/projections/<league_id>/).

All three are auto-detected from a PDF's own text, not its filename or
where it was dropped, so app.py can route an upload to the right pool
automatically. (Draft Sharks' League Analyzer — team-vs-team power
rankings, standings — is also league-specific but has no parser here yet;
it's detected and rejected with a clear message rather than silently
mis-parsed by another tool's parser.)

For matching purposes DataMerger.projections is the *merged* view: the
shared/global rankings pool plus the current league's own rankings files,
if any (a league-specific ranking file, should the user ever add one,
takes priority over the global pool for the same player). trade_values
merges the same way; free_agents comes only from the current league's own
folder.

The Dynasty Rankings and Free Agent Finder PDFs share a two-column page
layout (a numbers column, then a names column) which scrambles naive
text-extraction order — both parsers reconstruct rows on a *per-page*
basis rather than assuming the whole document reads top-to-bottom in one
pass. The Trade Value Chart PDF has no such scrambling (one record per
line), so its parser is a straight line-by-line regex match instead. CSV/
JSON exports from other vendors are still supported via the normal
column-alias path.
"""

from __future__ import annotations

import difflib
import json
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECTIONS_DIR = Path("data/projections")
GLOBAL_PROJECTIONS_DIR = PROJECTIONS_DIR / "_global"  # Dynasty Rankings: format-based, shared across leagues
# Facts-only (name/team/position/rank/trade_value) CSVs extracted from format-based Draft
# Sharks exports, committed to the repo as a starting baseline so the app isn't empty on a
# fresh clone. Never the vendor's own PDFs/prose -- just the numbers our schema already
# stores -- and always the lowest-priority source: any live upload to GLOBAL_PROJECTIONS_DIR
# or a league's own folder supersedes it per-player, same "newest wins" rule load_all()
# already applies within a single pool.
BASELINE_DIR = Path("data/baseline")
# Secondary valuation sources, kept deliberately separate from Draft Sharks' data rather than
# blended into it -- Draft Sharks shouldn't be the only source of value opinions this app can
# draw on. Each immediate subdirectory is one source (e.g. "dynastyprocess"), and every row
# from every source survives together (no cross-source dedup -- the whole point is comparing
# opinions, not picking a winner). See DataMerger.external_player_values().
EXTERNAL_VALUES_DIR = BASELINE_DIR / "external"
STALE_AFTER_DAYS = 7  # how old loaded projections can get before the UI nudges you to refresh
ALIASES_PATH = Path("data/player_aliases.json")  # manual overrides for names that fail to auto-match

# -- composite score -------------------------------------------------------------------------
#
# This app's own single blended read on a player, per the user's explicit request: weigh
# Draft Sharks a bit higher (its own model, closest thing here to a curated grade), weigh
# KeepTradeCut a bit lower (a crowd-vote average, "more easily influenced by the masses" per
# that request), leave DynastyProcess/FantasyPros neutral, and have a fresher-dated source
# count for more than a stale one. This NEVER replaces the raw per-source numbers anywhere --
# every bot-facing context still gets every source's own value exactly as before (see
# build_context/_price_trade_side in app.py) -- it's an additional, clearly-labeled field,
# not a substitute for seeing where sources actually agree or disagree.
#
# Relative weight per source before recency decay -- deliberately named/adjustable constants,
# not a formula derived from anything external, since "a bit higher"/"a bit less" is a
# judgment call the user made, not a fact to calculate.
COMPOSITE_SOURCE_WEIGHTS: dict[str, float] = {
    "draftsharks": 1.3,
    "dynastyprocess": 1.0,
    "fantasypros": 1.0,
    "keeptradecut": 0.7,
    # A panel-vetted live-search/reference-material finding (see bot_research.py) still an
    # LLM's own read, never a deterministic parser's -- weighted below even KeepTradeCut's
    # crowd-vote average to reflect that extra layer of uncertainty, despite having already
    # cleared a real bar (survived scrutiny from the whole panel, Contrarian included).
    "bot_research": 0.5,
}
# Every COMPOSITE_RECENCY_HALFLIFE_DAYS a source's weight halves -- a source dated today counts
# fully, one dated 60 days ago counts half as much, 120 days ago a quarter, and so on. Applies
# equally to Draft Sharks and every external source, so "newer sourced items add weight" holds
# regardless of which source got refreshed most recently.
COMPOSITE_RECENCY_HALFLIFE_DAYS = 60
# {"Fresh"/"Recent"/"Aging"/"Stale": max avg age in days for that grade} -- an at-a-glance read
# on how current the sources feeding one player's composite actually are, separate from the
# recency weighting above (that decays the score's math; this just reports the input freshness).
COMPOSITE_RECENCY_GRADES: list[tuple[str, float]] = [("Fresh", 7), ("Recent", 30), ("Aging", 90)]
# A percentile is only as meaningful as the pool it's ranked against -- confirmed the hard way:
# with a single bot_research finding on the books, EVERY finding read as the 100th percentile
# regardless of its actual rank (1 or 15, didn't matter -- a pool of one always ranks its only
# member first). Below this pool size, a source's weight scales down proportionally
# (pool_size / this), so a source still building up its sample size can't swing the composite
# as if its percentile were fully earned. Every structured source (Draft Sharks, DynastyProcess,
# FantasyPros, KTC) already has hundreds of rows and is never affected by this in practice --
# it only really bites bot_research early on, before enough findings have accumulated.
COMPOSITE_MIN_TRUSTED_POOL_SIZE = 20

# Which raw field to rank on, and whether a HIGHER value is better, for computing each
# secondary source's own percentile against its own player pool -- these are the exact columns
# those sources' baseline CSVs carry today (see each source's ATTRIBUTION.md under
# data/baseline/external/), not a generic convention every future source will automatically
# satisfy, so a new source needs its own entry here rather than being silently mis-percentiled.
# FantasyPros' best_ball_rankings.csv and DynastyProcess's picks.csv are deliberately absent --
# a season-long list and a picks-only list have no business feeding a PLAYER dynasty composite.
_EXTERNAL_PERCENTILE_RULES: dict[tuple[str, str], tuple[str, bool]] = {
    ("dynastyprocess", "players.csv"): ("value_1qb", True),
    ("fantasypros", "dynasty_ppr_rankings.csv"): ("rank", False),
    ("keeptradecut", "dynasty_superflex_halfppr.csv"): ("value", True),
    # One fixed (source, file) pair covers every bot_research.json finding regardless of which
    # real-world source it actually cites (ESPN, FantasyPros, ...) -- see
    # load_bot_research_as_external's own docstring for why.
    ("bot_research", "findings"): ("rank", False),
}


def external_upload_targets() -> dict[str, str]:
    """{source_name: expected_filename} for every external source the composite actually
    reads from a file (see _EXTERNAL_PERCENTILE_RULES) -- derived from that single source of
    truth rather than a second, driftable copy, so app.py's "refresh an external source"
    upload UI can overwrite the EXACT tracked filename for a source. That matters: a fresh
    upload saved under any other filename would sit alongside the old baseline file as an
    untracked, separately-percentiled (source, file) pair (load_external_values never dedupes
    within a source), silently double-counting that source's opinion in the composite instead
    of just refreshing it. bot_research is excluded -- it's not a file upload; see
    bot_research.py's add_finding/add_comparison for how it gets new data instead."""
    return {source: filename for (source, filename) in _EXTERNAL_PERCENTILE_RULES if source != "bot_research"}


def _recency_weight(source_date: Optional[str]) -> float:
    """1.0 for a source dated today, halving every COMPOSITE_RECENCY_HALFLIFE_DAYS. An
    unparsable/missing date gets a fixed middling weight (neither trusted as fresh nor
    discarded as worthless) rather than crashing or silently dropping that source."""
    if not source_date:
        return 0.5
    try:
        age_days = (datetime.now().date() - datetime.fromisoformat(str(source_date)).date()).days
    except ValueError:
        return 0.5
    return 0.5 ** (max(age_days, 0) / COMPOSITE_RECENCY_HALFLIFE_DAYS)


def recency_grade(avg_age_days: Optional[float]) -> str:
    # Not module-private -- app.py's sidebar reuses this same Fresh/Recent/Aging/Stale scale
    # for a site-wide freshness grade across every loaded source, not just a composite score's
    # own per-player average age.
    if avg_age_days is None:
        return "Unknown"
    for grade, max_days in COMPOSITE_RECENCY_GRADES:
        if avg_age_days <= max_days:
            return grade
    return "Stale"

# Header aliases -> canonical column names. Vendor exports are inconsistent
# about naming, so we normalize whatever shows up in the header row.
COLUMN_ALIASES = {
    "name": "name", "player": "name", "player_name": "name", "full_name": "name",
    "pos": "position", "position": "position",
    "team": "team", "tm": "team", "nfl_team": "team",
    "proj": "projection", "projection": "projection", "pts": "projection",
    "fantasy_pts": "projection", "fpts": "projection", "3d_projection": "projection",
    "vorp": "vorp", "value_over_replacement": "vorp",
    "tier": "tier", "ds_tier": "tier", "war_room_tier": "tier",
    "value": "trade_value", "trade_value": "trade_value", "dynasty_value": "trade_value",
    "rank": "rank", "ecr": "rank", "overall_rank": "rank",
}

SUFFIXES = re.compile(r"\b(jr|sr|ii|iii|iv|v)\.?\b", re.IGNORECASE)
NON_ALNUM = re.compile(r"[^a-z0-9 ]+")


def normalize_name(name: str) -> str:
    """Lowercase, strip suffixes/punctuation so 'A.J. Brown Jr.' == 'aj brown'.

    NFKD first so PDF-extracted ligatures and accents match cleanly -- "Mayﬁeld" (a
    single ligature glyph, common in Draft Sharks' PDF exports) decomposes to "fi"
    instead of silently vanishing under NON_ALNUM and producing "mayeld", which would
    never match Sleeper's "mayfield". Accented names (e.g. "Ju'Wuan James") get the
    same benefit for free.
    """
    if not name:
        return ""
    name = unicodedata.normalize("NFKD", name)
    name = name.lower()
    name = SUFFIXES.sub("", name)
    name = NON_ALNUM.sub("", name)
    return re.sub(r"\s+", " ", name).strip()


def name_key(norm_name: str) -> tuple[str, str]:
    """(first-initial, full remaining name) -- the shared fuzzy-match key for bridging Draft
    Sharks' first-initial-only PDF names ("J Chase") against vendors that export full names
    ("Ja'Marr Chase"). Keys on everything AFTER the first token, not just the last token: a
    multi-word last name breaks a last-token-only key, since two different people can share a
    last TOKEN while having different full last names -- confirmed live, "A.J. Brown"
    ("aj brown") and "Amon-Ra St. Brown" ("amonra st brown") both end in "brown" and collided
    under a (first-initial, last-token) key, silently pricing one player as the other. Used
    identically everywhere this app needs to bridge that abbreviation (_find_match's own
    matching, _compute_percentiles' bot_research position lookup, app.py's trade-calculator
    ambiguity check) rather than three separate, driftable copies of the same logic."""
    tokens = norm_name.split() if isinstance(norm_name, str) else []
    if not tokens:
        return ("", "")
    if len(tokens) == 1:
        return (tokens[0][0], tokens[0])
    return (tokens[0][0], " ".join(tokens[1:]))


def _normalize_columns(df: pd.DataFrame, default_kind: str = "rankings") -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
        # Trade Value Chart rows use "value" as their own canonical column (see pick_value()
        # and _price_trade_side()'s comments in app.py) -- never rename it to "trade_value"
        # like a rankings file's would be, or a reloaded baseline/trade_value CSV would break
        # pick_value()'s direct ["value"] lookup.
        if default_kind == "trade_value_chart" and key == "value":
            continue
        if key in COLUMN_ALIASES:
            rename[col] = COLUMN_ALIASES[key]
    df = df.rename(columns=rename)
    if "name" not in df.columns:
        raise ValueError("Projection file has no recognizable player name column")
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df


# -- Draft Sharks PDF parsing (shared bits) -----------------------------------

NFL_TEAM_CODES = (
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAC", "KC", "LAC", "LAR", "LVR", "MIA", "MIN", "NE",
    "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "UNS", "WAS",
)
# Draft Sharks' team codes vs. Sleeper's: JAC->JAX, LVR->LV, UNS (unsigned) -> FA.
TEAM_ALIASES = {"UNS": "FA", "JAC": "JAX", "LVR": "LV"}

# Offense + kicker/defense + IDP — which of these actually show up depends on
# the league (standard leagues get K/DEF, IDP leagues also get LB/DL/DB). Draft Sharks only
# ever uses the three broad codes; other vendors (FantasyPros' IDP export, e.g.) split them
# more finely (DE/DT for DL, S/CB for DB) -- both schemes are real IDP positions, so both need
# to register as "idp" in _position_group below, not just the three Draft Sharks happens to use.
POSITION_CODES = ("QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB")
IDP_POSITIONS = {"LB", "DL", "DB", "DE", "DT", "S", "CB", "EDGE", "SS", "FS"}


# Position families a single real person can never span at once. Each is its own IDENTITY
# namespace for dedup -- two rows in different families with the same normalized name are two
# different people, never a re-upload of one.
#
# The offensive skill positions deliberately share ONE namespace rather than getting four:
# a genuine same-player re-upload really can list him RB in one file and WR in another
# (real reclassification), and those rows must still collapse onto the newest. Nobody is
# reclassified from tight end to kicker, and a team defense is not a person at all, so those
# get namespaces of their own.
_KICKER_POSITIONS = {"K", "PK"}
_TEAM_DEFENSE_POSITIONS = {"DEF", "DST", "D/ST"}


# Vendor synonyms for the SAME on-field role. Draft Sharks exports the three broad IDP codes
# (LB/DL/DB) where FantasyPros and ESPN split them finer (S/CB for DB, DE/DT/EDGE for DL), and
# Sleeper writes DST where Draft Sharks writes DEF -- none of which is a different player.
#
# Deliberately NOT _position_group. That one is the dedup IDENTITY namespace and is coarse on
# purpose: every offensive skill position shares it, so a genuine RB->WR reclassification still
# collapses onto one row. This is the COMPARISON key a resolution uses to ask "is the row I
# matched even the same kind of player as the query", where QB/RB/WR/TE must stay four
# different answers. Using either one for the other's job is a real defect in both directions.
_POSITION_SYNONYMS = {
    "DST": "DEF", "D/ST": "DEF", "PK": "K",
    "S": "DB", "SS": "DB", "FS": "DB", "CB": "DB",
    "DE": "DL", "DT": "DL", "EDGE": "DL", "NT": "DL",
    "OLB": "LB", "ILB": "LB", "MLB": "LB",
}


def position_family(position) -> Optional[str]:
    """The role a position names, with vendor synonyms collapsed -- or None when the position
    is unknown. None means "no opinion", never "no match": an absent position is not evidence
    that two rows describe different people."""
    if position is None:
        return None
    try:
        if pd.isna(position):
            return None
    except (TypeError, ValueError):
        pass
    text = str(position).strip().upper()
    if not text:
        return None
    return _POSITION_SYNONYMS.get(text, text)


def _position_group(position) -> str:
    """Identity namespace for the dedup key, so two same-named players from different
    position families never silently shadow each other in _dedup_by_name_and_position below.

    The original bucket was offense-vs-IDP, added for a real collision found merging baseline
    data ("Josh Allen" the Bills QB vs. "Josh Allen" a DL). It left K and DST inside the
    offense bucket, which was harmless only while the kicker pool was 13 vendor rows. Seeding
    K and DST from league-scored Sleeper projections took that pool to 37 kickers and 32
    defenses and made the gap reachable: J Sanders (TE, CAR) and J Sanders (K, NYJ) are two
    different people, collided on "j sanders|offense", and the tight end was dropped from the
    merged projections entirely -- not mispriced, absent, and therefore undraftable.

    Same fix shape as the original, applied to the families it missed. Note this is an
    IDENTITY rule, not a scoring one: it decides who is the same person, and nothing here
    touches how any position is valued."""
    if not isinstance(position, str) or not position:
        return ""
    upper = position.upper()
    if upper in IDP_POSITIONS:
        return "idp"
    if upper in _KICKER_POSITIONS:
        return "k"
    if upper in _TEAM_DEFENSE_POSITIONS:
        return "def"
    return "offense"


_REVIEWED_DATE_RE = re.compile(r"Reviewed By[^|]*\|([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})")


def _extract_reviewed_date(full_text: str) -> Optional[str]:
    match = _REVIEWED_DATE_RE.search(full_text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def _sniff_pdf_kind_from_text(text: str) -> Optional[str]:
    """Which Draft Sharks tool this page text came from, or None when nothing recognises it.

    None is the important return. This used to fall through to "rankings" for anything it did
    not recognise -- including an unreadable file -- so a mis-sniff silently handed the wrong
    document to parse_draftsharks_pdf, which would then read whatever regex-shaped lines it
    happened to contain. No parser is a default.

    Rankings is identified POSITIVELY, by the structure of its own table (a stat row in either
    published layout, plus a TEAM/POSITION/rank line), rather than by being the last option
    left. That is a stronger test than the old fallthrough, not a weaker one.
    """
    upper = (text or "").upper()
    if "TRADE VALUE CHART" in upper:
        return "trade_value_chart"
    if "FREE AGENT FINDER" in upper or "3D ROS" in upper:
        return "free_agents"
    if "LEAGUE ANALYZER" in upper or "LEAGUE POWER RANKINGS" in upper:
        return "league_analyzer"
    lines = [line.strip() for line in (text or "").split("\n")]
    has_stat = any(_RANKINGS_STAT_RE.match(line) or _RANKINGS_ADP_STAT_RE.match(line)
                   for line in lines)
    has_team_pos = any(_RANKINGS_TEAM_POS_RE.match(line) for line in lines)
    if has_stat and has_team_pos:
        return "rankings"
    return None


def _sniff_pdf_kind(path: Path) -> Optional[str]:
    """Which Draft Sharks tool a PDF came from, sniffed from its own text (not the filename).

    'rankings' -> format-based, shareable across leagues. 'trade_value_chart' -> also
    format-based (a standalone price list, not tied to any league's roster). 'free_agents'
    -> this-league-roster-specific. 'league_analyzer' -> also league-specific (team-vs-team
    power rankings/standings) but has no parser yet, so callers should reject it with a
    clear message rather than silently feeding it to the rankings parser, which would
    misread its text.
    """
    import pypdf

    try:
        reader = pypdf.PdfReader(str(path))
        text = (reader.pages[0].extract_text() or "") if reader.pages else ""
    except Exception:
        # An unreadable file is an unknown file. It used to become "rankings".
        return None
    return _sniff_pdf_kind_from_text(text)


# -- Dynasty Rankings tool -----------------------------------------------------

# Draft Sharks publishes these rankings pages in two different table layouts, and the
# numbers alone don't distinguish them -- both are "rank plus three figures":
#
#   dynasty tables : RK | 1yr Proj | 3yr Proj | 3D Value    ->  "1 177 406 18"
#   redraft DST    : RK | ADP      | DS Proj  | 3D Value    ->  "1 22.11 125 9"
#
# ADP is a decimal round.pick figure, which is what makes the two separable at all, but
# keying off "is the second number a float" would be inference. The layout is read from the
# page HEADER instead, which states it outright. Nothing here is position-specific: it is a
# fact about the source's table formats, and any future DS page in either layout parses.
_RANKINGS_STAT_RE = re.compile(r"^(\d+) ([\d,]+) ([\d,]+) (\d+)$")
_RANKINGS_ADP_STAT_RE = re.compile(r"^(\d+) (\d+\.\d+) ([\d,]+) (\d+)$")
_RANKINGS_ADP_HEADER_RE = re.compile(r"\bRK\b.*\bADP\b")
_RANKINGS_TEAM_POS_RE = re.compile(rf"^({'|'.join(NFL_TEAM_CODES)})\s*({'|'.join(POSITION_CODES)})(\d+)$")


def _verify_block_alignment(source: str, page_number: int, stat_rows: list, name_rows: list,
                            rank_index: int) -> None:
    """Both Draft Sharks PDF tools publish a page as two independent blocks -- the stats and
    the names -- and both parsers join them by POSITIONAL INDEX. That join asserts an ordering
    invariant about the source document, and until this existed nothing checked it.

    Two checks, and deliberately only two:

    * more stat rows than name rows means a NAME line went undetected, so every later stat on
      the page belongs to the player above it. This is the dangerous direction: it leaves a
      superficially perfect record -- valid name, team, position, contiguous rank, plausible
      numbers -- with nothing anywhere marking it. The reverse (more names than stats) is the
      one shortfall the parser documents, "just missed the cut" names with no stat row, and
      stays a legitimate parse with null numerics.
    * ranks must strictly increase down the page. A stray line matching the stat shape (a
      footer, a page number block) lands in the middle of the block and breaks it.

    Strictly increasing, NOT contiguous: real exports skip ranks -- the committed
    te_premium_dynasty_rankings.csv carries 7 gaps over 250 rows -- so requiring contiguity
    would reject good documents. Checking the weaker property that actually holds is the
    difference between a check and a guess.

    Raising is the point. parse_keeptradecut_pdf already refuses to emit a row it cannot place
    (its expected_rank check truncates rather than mis-assigns), and this gives the other two
    the same ability to know they are lost.
    """
    if len(stat_rows) > len(name_rows):
        raise ValueError(
            f"{source}: page {page_number} does not align -- {len(stat_rows)} stat rows against "
            f"{len(name_rows)} names, so a name line went undetected and every stat after it "
            "would be attributed to the wrong player. Refusing to emit the page."
        )
    ranks = [row[rank_index] for row in stat_rows]
    for earlier, later in zip(ranks, ranks[1:]):
        if later <= earlier:
            raise ValueError(
                f"{source}: page {page_number} does not align -- rank {later} follows {earlier}, "
                "so the stat block contains a line that is not a player row. Refusing to emit "
                "the page."
            )


def parse_draftsharks_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a Draft Sharks Dynasty Rankings page saved/printed as PDF.

    Returns (dataframe, source_date_iso). Each PDF page lists a block of
    "RK 1yr-proj 3yr-proj 3D-value" number rows followed by a block of
    "Name" / "TEAMPOSn" name rows; both blocks preserve the same top-to-
    bottom order as each other *within a page*, even though pypdf's flat
    text extraction interleaves the two page columns. Some pages append a
    few extra "just missed the cut" names with no stat row — those are
    kept with null numeric fields rather than mismatched to the wrong stats.
    """
    import pypdf

    reader = pypdf.PdfReader(str(path))
    full_text_parts: list[str] = []
    records: list[dict] = []

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text()
        full_text_parts.append(text)
        lines = [l.strip() for l in text.split("\n")]

        # Which of the two DS table layouts is this page? Read from its own header rather
        # than inferred from the numbers -- see _RANKINGS_ADP_STAT_RE.
        adp_layout = any(_RANKINGS_ADP_HEADER_RE.search(l) for l in lines)
        stat_re = _RANKINGS_ADP_STAT_RE if adp_layout else _RANKINGS_STAT_RE

        # (rank, season projection, 3yr projection or None, 3D value). The ADP layout has no
        # multi-year column at all, so proj_3yr stays None there rather than being filled
        # with a stand-in -- a defense has no career arc to project, and inventing one would
        # feed a fabricated number straight into dynasty scoring. compute_draft_board treats
        # a missing proj_3yr as "no opinion" (neutral), not as a bad outlook.
        stat_rows: list[tuple[int, int, Optional[int], int]] = []
        name_rows: list[dict] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stat_match = stat_re.match(line)
            if stat_match:
                if adp_layout:
                    rank, _adp, projection, value_3d = stat_match.groups()
                    proj_3yr_value = None
                else:
                    rank, projection, proj_3yr, value_3d = stat_match.groups()
                    proj_3yr_value = int(proj_3yr.replace(",", ""))
                stat_rows.append((int(rank), int(projection.replace(",", "")),
                                   proj_3yr_value, int(value_3d)))
                i += 1
                continue

            team_pos_match = _RANKINGS_TEAM_POS_RE.match(line)
            if team_pos_match and name_rows and "team" not in name_rows[-1]:
                team, position, pos_rank = team_pos_match.groups()
                name_rows[-1].update(
                    team=TEAM_ALIASES.get(team, team), position=position, pos_rank=int(pos_rank)
                )
                i += 1
                continue

            # A name line is any line immediately followed by a TEAMPOSn line.
            if i + 1 < len(lines) and _RANKINGS_TEAM_POS_RE.match(lines[i + 1]):
                name_rows.append({"name": line})
                i += 1
                continue

            i += 1

        _verify_block_alignment(getattr(path, "name", str(path)), page_number,
                                 stat_rows, name_rows, rank_index=0)
        for idx, entry in enumerate(name_rows):
            if idx < len(stat_rows):
                rank, proj_1yr, proj_3yr, value_3d = stat_rows[idx]
                entry.update(rank=rank, projection=proj_1yr, proj_3yr=proj_3yr, trade_value=value_3d)
            records.append(entry)

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    source_date = _extract_reviewed_date("\n".join(full_text_parts))
    return df, source_date


# -- Free Agent Finder tool -----------------------------------------------------

# Rows look like "Mine 1 25.2 25.4 29.2 100" or "Add233 2.9 4.5 9.2 5.6" or, for
# a plain (unowned, unrecommended) free agent, no status word at all: "209 9 11
# 14.5 7.5". Whether there's a literal space between the status word and the
# rank number is inconsistent (PDF text-extraction kerning artifact), so it's
# optional in the regex either way.
_FA_STAT_RE = re.compile(r"^(Mine|Add|Drop|Lock)?\s*(\d+) ([\d.]+) ([\d.]+) ([\d.]+) ([\d.]+)$")
_FA_TEAM_POS_RE = re.compile(rf"^({'|'.join(NFL_TEAM_CODES)})\s*({'|'.join(POSITION_CODES)})$")


def parse_draftsharks_free_agents_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a Draft Sharks Free Agent Finder page saved/printed as PDF.

    Same per-page interleaved-column reconstruction as parse_draftsharks_pdf,
    but a different table: RK / 3D Proj / 3D ROS / Ceiling / 3D Value+, each
    row optionally tagged Mine (already on your roster), Add/Drop (a
    suggested waiver move), or untagged (an ordinary free agent). This export
    has no reliable absolute date on the page itself (just a relative "Synced
    X minutes ago"), so the caller falls back to the file's save date.
    """
    import pypdf

    reader = pypdf.PdfReader(str(path))
    records: list[dict] = []

    for page_number, page in enumerate(reader.pages, start=1):
        lines = [l.strip() for l in page.extract_text().split("\n")]

        stat_rows: list[tuple[Optional[str], int, float, float, float, float]] = []
        name_rows: list[dict] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stat_match = _FA_STAT_RE.match(line)
            if stat_match:
                status, rank, proj, ros, ceiling, value = stat_match.groups()
                stat_rows.append((status, int(rank), float(proj), float(ros), float(ceiling), float(value)))
                i += 1
                continue

            team_pos_match = _FA_TEAM_POS_RE.match(line)
            if team_pos_match and name_rows and "team" not in name_rows[-1]:
                team, position = team_pos_match.groups()
                name_rows[-1].update(team=TEAM_ALIASES.get(team, team), position=position)
                i += 1
                continue

            if i + 1 < len(lines) and _FA_TEAM_POS_RE.match(lines[i + 1]):
                name_rows.append({"name": line})
                i += 1
                continue

            i += 1

        _verify_block_alignment(getattr(path, "name", str(path)), page_number,
                                 stat_rows, name_rows, rank_index=1)
        for idx, entry in enumerate(name_rows):
            if idx < len(stat_rows):
                status, rank, proj, ros, ceiling, value = stat_rows[idx]
                entry.update(roster_status=status, rank=rank, proj_3d=proj,
                             ros_3d=ros, ceiling=ceiling, value_3d=value)
            records.append(entry)

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


# -- Trade Value Chart tool -----------------------------------------------------
#
# Unlike Dynasty Rankings/Free Agent Finder, this one prices three different asset
# kinds on a single comparable scale: named players, exact rookie pick slots for the
# upcoming rookie draft (1.01-4.12), and generic future picks by round+year ("2027
# Random Rd 1"). The future-pick labels are the same strings Draft Sharks' League
# Analyzer roster export uses for picks a team owns -- but ownership is Sleeper's to
# say, not Draft Sharks' (its pick imports can be wonky); this parser only extracts
# VALUES, keyed by label, never any claim about who owns a pick. A rookie pick slot's
# own value already IS this draft class's strength signal -- Draft Sharks prices a
# strong class's 1.01 higher than a weak class's, same 0-100 scale as a named player
# -- so there's no separate "class grade" table to look for.
_TVC_PLAYER_RE = re.compile(r"^(.+?) (\d+)\s*Trend\xa0»\s*$")
_TVC_ROOKIE_SLOT_RE = re.compile(r"^(\d\.\d{2}) (\d+)$")
_TVC_FUTURE_PICK_RE = re.compile(r"^(\d{4} Random Rd \d) (\d+)$")
_TVC_POSITION_HEADERS = {"QUARTERBACK": "QB", "RUNNING BACK": "RB", "WIDE RECEIVER": "WR", "TIGHT END": "TE"}
# The page's own H1 states which of Draft Sharks' several format toggles (Dynasty/
# Redraft x PPR/Half-PPR/Non-PPR x TEP) was active for this particular export --
# e.g. "DYNASTY PPR TRADE VALUE CHART 2026". It does NOT state 1QB vs Superflex,
# which materially changes QB (and therefore pick) value -- that has to stay an
# unverified caveat rather than something this parser can check.
_TVC_TITLE_RE = re.compile(r"^(DYNASTY|REDRAFT)\s+(.+?)\s+TRADE VALUE CHART", re.IGNORECASE)


def parse_draftsharks_trade_value_chart_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse Draft Sharks' standalone Dynasty Trade Value Chart.

    Format-based like Dynasty Rankings (not tied to any league's roster), and unlike
    the other two PDF tools its rows are already one-per-line -- no interleaved-column
    reconstruction needed. Returns one row per asset with an `asset_type` column
    ('player', 'rookie_pick_slot', or 'future_pick') so callers can filter to just the
    picks, just the players, or both. Every row also carries `source_league_type`/
    `source_scoring` (e.g. "Dynasty"/"PPR") read off the page's own title, so a caller
    can flag a mismatch against the league actually being asked about instead of
    silently treating these numbers as universally correct.
    """
    import pypdf

    reader = pypdf.PdfReader(str(path))
    records: list[dict] = []
    current_position: Optional[str] = None
    source_league_type: Optional[str] = None
    source_scoring: Optional[str] = None

    for page in reader.pages:
        for raw_line in (page.extract_text() or "").split("\n"):
            line = raw_line.strip()
            if source_league_type is None:
                title_match = _TVC_TITLE_RE.match(line)
                if title_match:
                    source_league_type = title_match.group(1).title()
                    source_scoring = title_match.group(2).strip()
            if line in _TVC_POSITION_HEADERS:
                current_position = _TVC_POSITION_HEADERS[line]
                continue
            player_match = _TVC_PLAYER_RE.match(line)
            if player_match and current_position:
                name, value = player_match.groups()
                records.append({
                    "asset_type": "player", "name": name.strip(),
                    "position": current_position, "value": int(value),
                })
                continue
            slot_match = _TVC_ROOKIE_SLOT_RE.match(line)
            if slot_match:
                slot, value = slot_match.groups()
                records.append({"asset_type": "rookie_pick_slot", "name": slot, "value": int(value)})
                continue
            future_match = _TVC_FUTURE_PICK_RE.match(line)
            if future_match:
                label, value = future_match.groups()
                records.append({"asset_type": "future_pick", "name": label, "value": int(value)})

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    df["source_league_type"] = source_league_type
    df["source_scoring"] = source_scoring
    return df, None


# -- FantasyPros Expert Consensus Rankings (ECR) exports -----------------------
#
# Unlike Draft Sharks' PDFs, these are already one-clean-record-per-line -- no
# interleaved-column reconstruction needed. Two shapes seen so far, told apart by their
# header row: a Dynasty export adds AGE/BEST/WORST/AVG/STD.DEV (the spread of individual
# experts' ranks behind the consensus number); a seasonal export (Best Ball, Redraft, ...)
# instead has just BYE WEEK. Both interleave "Tier N" section lines between rows, captured
# here as each row's own tier rather than discarded. FantasyPros' rank/tier/ECR numbers
# aren't on Draft Sharks' 0-100 trade_value scale, so these are kept as their own
# non-blended source (see DataMerger.external_player_values) rather than merged into
# projections/trade_value.
_FP_TIER_RE = re.compile(r"^Tier (\d+)\s*$")
_FP_DYNASTY_ROW_RE = re.compile(
    r"^(\d+) (.+) \(([A-Z]{2,3})\) ([A-Z]+)(\d+) (\d+|NA|-) (\d+|NA) (\d+|NA) ([\d.]+|NA) ([\d.]+|NA)$"
)
_FP_SEASONAL_ROW_RE = re.compile(r"^(\d+) (.+) \(([A-Z]{2,3})\) ([A-Z]+)(\d+) (\d+|-)$")
# FantasyPros' IDP export has an extra SOS (strength-of-schedule) column after bye week --
# always "-" in practice (confirmed against a real 204-row export, 0 non-dash values), but the
# row shape still has to consume it to match at all.
_FP_IDP_ROW_RE = re.compile(r"^(\d+) (.+) \(([A-Z]{2,3})\) ([A-Z]+)(\d+) (\d+|-) (-|[\d.]+)$")


def _fp_num(raw: str) -> Optional[float]:
    return None if raw in ("NA", "-") else float(raw)


def parse_fantasypros_dynasty_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a FantasyPros Dynasty (Keeper) Rankings export -- ECR plus each expert panel's
    spread (best/worst/std.dev) behind that consensus number. No per-row date on the page
    itself (see values-players.csv precedent elsewhere in this file); caller falls back to
    the PDF's own save/creation date, same as Draft Sharks exports with no printed date."""
    import pypdf

    reader = pypdf.PdfReader(str(path))
    records: list[dict] = []
    tier = None
    for page in reader.pages:
        for raw_line in (page.extract_text() or "").split("\n"):
            line = raw_line.strip()
            tier_match = _FP_TIER_RE.match(line)
            if tier_match:
                tier = int(tier_match.group(1))
                continue
            row_match = _FP_DYNASTY_ROW_RE.match(line)
            if not row_match:
                continue
            rank, name, team, position, pos_rank, age, best, worst, avg, stddev = row_match.groups()
            records.append({
                "rank": int(rank), "name": name.strip(),
                "team": TEAM_ALIASES.get(team, team), "position": position, "pos_rank": int(pos_rank),
                "age": _fp_num(age), "best": _fp_num(best), "worst": _fp_num(worst),
                "avg": _fp_num(avg), "std_dev": _fp_num(stddev), "tier": tier,
            })

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


def parse_fantasypros_bestball_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a FantasyPros seasonal (Best Ball/Redraft-shaped) Rankings export -- rank/tier/bye
    only, no dynasty-relevant spread columns. Deliberately a different parser (and a different
    external-source subfolder, never dynasty rankings) from parse_fantasypros_dynasty_pdf --
    this app already treats "single-season export mislabeled as dynasty" as a real, previously-
    hit failure mode (see app.py's upload handler's Redraft/Dynasty check), so a seasonal
    FantasyPros list gets the same firm separation rather than a shared, ambiguous parser."""
    import pypdf

    reader = pypdf.PdfReader(str(path))
    records: list[dict] = []
    tier = None
    for page in reader.pages:
        for raw_line in (page.extract_text() or "").split("\n"):
            line = raw_line.strip()
            tier_match = _FP_TIER_RE.match(line)
            if tier_match:
                tier = int(tier_match.group(1))
                continue
            row_match = _FP_SEASONAL_ROW_RE.match(line)
            if not row_match:
                continue
            rank, name, team, position, pos_rank, bye = row_match.groups()
            records.append({
                "rank": int(rank), "name": name.strip(),
                "team": TEAM_ALIASES.get(team, team), "position": position, "pos_rank": int(pos_rank),
                "bye_week": _fp_num(bye), "tier": tier,
            })

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


def parse_fantasypros_idp_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a FantasyPros IDP (Individual Defensive Player) Rankings export -- a SEASON-LONG
    draft-prep list ("SOS SEASON ECR" in its own header, no dynasty-relevant spread columns),
    not dynasty, same posture as parse_fantasypros_bestball_pdf and for the same reason: never
    silently read a redraft list as a long-term value opinion.

    Data-preparation tooling, not part of the live app's own data flow: this produced the
    committed data/baseline/external/fantasypros/idp_redraft_rankings.csv baseline from a raw
    PDF export once, and the app only ever reads that already-converted CSV afterward (via the
    generic load_external_values(), which needs no PDF parsing) -- and since it's redraft-scope,
    _EXTERNAL_PERCENTILE_RULES deliberately never feeds it to the composite either way, same as
    FantasyPros' best_ball_rankings.csv. Kept here to regenerate that CSV from a fresher PDF
    export if FantasyPros' own IDP tool output ever changes shape, not dead by accident.

    Position codes here are more granular than Draft Sharks' three broad IDP buckets (DE/DT
    instead of one DL, S/CB instead
    of one DB) -- kept as-is rather than collapsed, since the extra detail is real information,
    not noise; see IDP_POSITIONS for why _position_group needs to recognize them too."""
    import pypdf

    reader = pypdf.PdfReader(str(path))
    records: list[dict] = []
    tier = None
    for page in reader.pages:
        for raw_line in (page.extract_text() or "").split("\n"):
            line = raw_line.strip()
            tier_match = _FP_TIER_RE.match(line)
            if tier_match:
                tier = int(tier_match.group(1))
                continue
            row_match = _FP_IDP_ROW_RE.match(line)
            if not row_match:
                continue
            rank, name, team, position, pos_rank, bye, _sos = row_match.groups()
            records.append({
                "rank": int(rank), "name": name.strip(),
                "team": TEAM_ALIASES.get(team, team), "position": position, "pos_rank": int(pos_rank),
                "bye_week": _fp_num(bye), "tier": tier,
            })

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


# -- ESPN IDP (Individual Defensive Player) Rankings ----------------------------
#
# ESPN's page is a scraped article, not a clean export -- huge blocks of unrelated nav/ad/
# related-article text get interleaved between table rows in pypdf's flat text extraction, and
# the table itself re-prints its own header every ~4 rows (looks like the live page paginates
# in small chunks). Position section headers ("2026 Linebacker Rankings") are unreliable as
# anchors -- confirmed on a real export: they show up mid-clutter *after* their table's last
# row, not before its first, and the DL section's own header is missing/never appears at all.
# What IS reliable: the DL/LB/DB sections appear in that fixed order (matches the page's own
# "Top 40 DLs, LBs and DBs" nav text), and each new section's own row-1 resets the rank counter
# back to 1 -- so position is assigned by counting resets, never by matching caption text.
_ESPN_IDP_TEAM_CODES = (
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAX", "KC", "LAC", "LAR", "LV", "MIA", "MIN", "NE",
    "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "WSH",
)
_ESPN_IDP_TEAM_ALT = "|".join(sorted(_ESPN_IDP_TEAM_CODES, key=len, reverse=True))
# Team and the injury-status flag (Q/O/etc) are usually glued with no space ("LARQ") but not
# always (confirmed: 2 of 120 real rows print "PHI O" with a space) -- \s? tolerates both.
_ESPN_IDP_ROW_RE = re.compile(
    rf"^(\d+)\.\xa0(.+?), ({_ESPN_IDP_TEAM_ALT})\s?([A-Z]?) (NR|\d+) (NR|\d+) (NR|\d+) ([\d.]+|NR)$"
)
_ESPN_IDP_POSITIONS = ("DL", "LB", "DB")


def parse_espn_idp_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse ESPN's Individual Defensive Player draft rankings (3 analysts' individual ranks
    plus their average) saved/printed as PDF -- see the module comment above for why position
    is assigned by counting rank-resets rather than trusting the page's own section captions.
    A season-long draft-prep list, not dynasty (no dynasty framing anywhere on the page).

    Data-preparation tooling, not part of the live app's own data flow, same as
    parse_fantasypros_idp_pdf right above (see its own docstring for the full reasoning): this
    produced the committed data/baseline/external/espn/idp_redraft_rankings.csv baseline once,
    and there's no live upload path for ESPN at all -- that source isn't in the composite's
    _EXTERNAL_PERCENTILE_RULES (redraft-scope, deliberately excluded) or app.py's "refresh an
    external source" upload UI, so nothing in the running app currently calls this. Kept to
    regenerate the baseline CSV from a fresher PDF if ESPN's own export ever changes shape."""
    import pypdf

    reader = pypdf.PdfReader(str(path))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages)

    records: list[dict] = []
    section_idx = -1
    for line in full_text.split("\n"):
        line = line.strip()
        row_match = _ESPN_IDP_ROW_RE.match(line)
        if not row_match:
            continue
        rank, name, team, status_flag, a1, a2, a3, avg = row_match.groups()
        rank = int(rank)
        if rank == 1:
            section_idx += 1
        position = _ESPN_IDP_POSITIONS[section_idx] if 0 <= section_idx < len(_ESPN_IDP_POSITIONS) else None
        records.append({
            "rank": rank, "name": name.strip(), "team": team, "position": position,
            "injury_flag": status_flag or None,
            "analyst_avg": None if avg == "NR" else float(avg),
        })

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


# -- KeepTradeCut Dynasty Rankings ----------------------------------------------
#
# KTC's page prints one asset per line, but its VALUE and RANK columns render back-to-back
# with no separating whitespace in pypdf's flat text extraction (e.g. "9998" + "1" -> "99981"
# for the #1 overall asset valued 9998) -- a different, glued-digits flavor of the column-
# ordering problems Draft Sharks' and FantasyPros' PDFs each have their own version of. Rank
# is reconstructible without guessing, though: the list is strictly sequential (each row is
# exactly one more than the last), so the true split is whichever one makes the trailing
# digits equal the rank this row has to be -- confirmed exactly (0 ambiguous rows, every rank
# 1-250 accounted for) against 5 real 50-row exports of this list.
_KTC_ROW_RE = re.compile(r"^(.+?) ([A-Z]{1,3}\d+|PICK) (T\d+) (\d+)( R)? (-?\d+)$")
_KTC_POS_RE = re.compile(r"^([A-Z]{1,3})(\d+)$")
_KTC_RANGE_RE = re.compile(r"\b(\d+)\s*-\s*(\d+)\b")
_KTC_FORMAT_RE = re.compile(r"^(.+?) Values updated", re.MULTILINE)


def parse_keeptradecut_pdf(path: Path, start_rank: Optional[int] = None) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a KeepTradeCut Dynasty Rankings page saved/printed as PDF. KTC's own list is
    crowdsourced (26M+ data points per its own header line) and, unlike Draft Sharks' or
    FantasyPros' exports, prices players and picks together on one list and one 0-9999ish
    scale (asset_type distinguishes them, same shape as Draft Sharks' Trade Value Chart).

    start_rank is the rank of this PDF's first row -- required to seed the digit-splitting
    described above. If not given, it's read off the page's own "X - Y" pagination footer
    (e.g. "51 - 100" for the second 50-row chunk of a longer list); pass it explicitly only
    if a future export ever omits that footer. No per-row or page date is printed (just a
    relative "updated N minutes ago"), so source_date falls back to the file's own date same
    as every other vendor export with nothing more precise printed on the page.
    """
    import pypdf

    reader = pypdf.PdfReader(str(path))
    full_text = "\n".join(p.extract_text() or "" for p in reader.pages)

    if start_rank is None:
        range_match = _KTC_RANGE_RE.search(full_text)
        start_rank = int(range_match.group(1)) if range_match else 1

    format_match = _KTC_FORMAT_RE.search(full_text)
    source_format = format_match.group(1).strip() if format_match else None

    records: list[dict] = []
    expected_rank = start_rank
    for line in full_text.split("\n"):
        line = line.strip()
        row_match = _KTC_ROW_RE.match(line)
        if not row_match:
            continue
        name, pos_raw, tier, blob, rookie_flag, trend = row_match.groups()
        rank_str = str(expected_rank)
        if not blob.endswith(rank_str) or blob == rank_str:
            continue  # doesn't fit the expected next rank -- not a real row (e.g. sidebar noise)
        value = int(blob[: -len(rank_str)])
        if pos_raw == "PICK":
            asset_type, position, pos_rank = "pick", None, None
        else:
            pos_match = _KTC_POS_RE.match(pos_raw)
            asset_type = "player"
            position, pos_rank = pos_match.group(1), int(pos_match.group(2))
        records.append({
            "rank": expected_rank, "name": name.strip(), "asset_type": asset_type,
            "position": position, "pos_rank": pos_rank, "tier": int(tier[1:]), "value": value,
            "rookie": bool(rookie_flag), "trend_30d": int(trend), "source_format": source_format,
        })
        expected_rank += 1

    df = pd.DataFrame(records)
    if df.empty:
        return df, None
    df["norm_name"] = df["name"].astype(str).map(normalize_name)
    return df, None


def load_projection_file(path: Path, default_kind: str = "rankings") -> tuple[pd.DataFrame, str]:
    """Returns (dataframe, kind) where kind is 'rankings', 'free_agents', or 'trade_value_chart'.

    default_kind only applies to CSV/JSON, which (unlike PDFs) carry no text to sniff a kind
    from -- callers that keep trade-value-chart facts in their own CSV pool (see DataMerger's
    baseline_dir) pass default_kind="trade_value_chart" so those rows land in the right bucket.
    """
    suffix = path.suffix.lower()
    kind = default_kind
    if suffix == ".csv":
        df = pd.read_csv(path)
        df = _normalize_columns(df, default_kind=default_kind)
        # A CSV that already states its own source_date (e.g. a baseline snapshot extracted
        # on a specific day) keeps that date rather than being stamped with today's read-time
        # mtime, which on a fresh clone is just the checkout time, not when the data is from.
        source_date = df["source_date"].iloc[0] if "source_date" in df.columns and not df.empty else None
    elif suffix == ".json":
        df = pd.read_json(path)
        df = _normalize_columns(df, default_kind=default_kind)
        source_date = None
    elif suffix == ".pdf":
        kind = _sniff_pdf_kind(path)
        if kind is None:
            raise ValueError(
                f"{path.name} does not match any supported export format — refusing to guess. "
                "A PDF that no sniffer recognises used to be handed to the Dynasty Rankings "
                "parser by default, which would read whatever regex-shaped lines it contained."
            )
        if kind == "league_analyzer":
            raise ValueError(f"{path.name} looks like a Draft Sharks League Analyzer export — not supported yet")
        if kind == "trade_value_chart":
            parser = parse_draftsharks_trade_value_chart_pdf
        elif kind == "free_agents":
            parser = parse_draftsharks_free_agents_pdf
        else:
            parser = parse_draftsharks_pdf
        df, source_date = parser(path)
        if df.empty:
            raise ValueError(f"No table found in {path.name}")
    else:
        raise ValueError(f"Unsupported projection file type: {path.suffix}")

    df["source_file"] = path.name
    df["source_date"] = source_date or datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return df, kind


def _detect_rankings_format(filename: str) -> dict:
    """Best-effort (scoring/superflex/te_premium) tags for a Dynasty Rankings export, from its
    filename. Draft Sharks ships this "same tool, different format assumptions" export as
    several distinct files (see data/baseline/rankings/) that all cover the SAME players with
    DIFFERENT values -- confirmed empirically (compared one player's trade_value AND its own
    projection column across every baseline file): Brock Bowers' trade_value ranged 36-96 (a
    ~2.7x swing) purely depending on which format file happened to win an arbitrary dedup
    tiebreak, regardless of any real league's actual settings. TE-premium exports don't repeat
    "ppr" in their own filename despite being built on a PPR base (their PROJECTION column
    matches PPR's scale plus the TE bonus, not standard's lower scale) -- that's why te_premium
    alone implies ppr scoring below, rather than defaulting to standard when "ppr" is absent."""
    name = filename.lower()
    te_premium = "te_premium" in name or "te-premium" in name
    superflex = "superflex" in name or "super_flex" in name
    if te_premium:
        scoring = "ppr"
    elif "half_ppr" in name or "halfppr" in name or "half-ppr" in name:
        scoring = "half_ppr"
    elif "ppr" in name:
        scoring = "ppr"
    else:
        scoring = "standard"
    return {"scoring": scoring, "superflex": superflex, "te_premium": te_premium}


def _rankings_format_match_score(tags: dict, league_format: dict) -> float:
    """How well one rankings file's own format assumptions match a league's actual format --
    higher is better. Used to prefer the best-fitting file when the same player appears in
    more than one (see load_all's format_hint and DataMerger.set_league_format). Weighted by
    how much each axis actually swings a player's value: superflex most (it can roughly double
    a startable QB's price), TE premium next (a real but position-scoped swing), scoring last
    (PPR vs standard moves everyone a little, never as dramatically as the other two)."""
    if not league_format:
        return 0.0
    score = 0.0
    if tags.get("superflex") == bool(league_format.get("superflex")):
        score += 3.0
    if tags.get("te_premium") == bool(league_format.get("te_premium")):
        score += 2.0
    wants_scoring = league_format.get("scoring") or "ppr"
    file_scoring = tags.get("scoring", "standard")
    if file_scoring == wants_scoring:
        score += 1.0
    elif wants_scoring == "half_ppr" and file_scoring == "ppr":
        # No half-PPR-specific export exists in the baseline today -- PPR is the closer
        # approximation of the two available, not a real match, so it still scores lower
        # than an exact hit above.
        score += 0.5
    return score


def load_all(
    projections_dir: Path = PROJECTIONS_DIR, default_kind: str = "rankings",
    format_hint: Optional[dict] = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parse every CSV/JSON/PDF once, bucketed into (rankings_df, free_agents_df, trade_values_df).

    default_kind is forwarded to load_projection_file for CSV/JSON files -- see its docstring.

    format_hint (a league's {"scoring", "superflex", "te_premium"}), when given, reorders the
    RANKINGS frames (never free agents or trade values -- neither has multiple format variants
    today) from worst- to best-matching before the dedup below, so the best-fitting file wins
    the same-player tiebreak instead of whichever file happened to sort last. See
    _detect_rankings_format/_rankings_format_match_score for how that match is scored. Offense
    and IDP rows never contend for the same tiebreak (Draft Sharks' offense and IDP exports
    cover disjoint position sets entirely), so this reordering is safe to apply as one global
    sort rather than needing a separate pass per position group.
    """
    projections_dir = Path(projections_dir)
    empty = pd.DataFrame(columns=["name", "norm_name"])
    if not projections_dir.exists():
        return empty, empty.copy(), empty.copy()

    # Load order here doesn't matter -- sorted by name only so this loop itself is
    # deterministic and doesn't depend on iterdir()'s filesystem order. What decides the
    # dedup tiebreak is assigned AFTER loading, below.
    files = sorted(
        [p for p in projections_dir.iterdir() if p.suffix.lower() in (".csv", ".json", ".pdf")],
        key=lambda p: p.name,
    )
    rankings_entries: list[tuple[str, str, "pd.DataFrame", float]] = []
    fa_entries: list[tuple[str, str, "pd.DataFrame"]] = []
    tvc_entries: list[tuple[str, str, "pd.DataFrame"]] = []
    for f in files:
        try:
            df, kind = load_projection_file(f, default_kind=default_kind)
        except Exception:
            continue  # skip unparsable/misformatted files rather than crashing the app

        # Suffix-stripping (Jr./Sr./III/...) can collapse two *different* real
        # players onto the same norm_name within one file (e.g. a Draft Sharks
        # page listing both "B Robinson" ATL RB1 and an unrelated "B Robinson
        # Jr." far down the board). Within a single file, prefer the better
        # (lower) rank rather than an arbitrary row-order tiebreak.
        if "rank" in df.columns:
            df = df.sort_values("rank", na_position="last").drop_duplicates(subset="norm_name", keep="first")
        else:
            df = df.drop_duplicates(subset="norm_name", keep="first")

        # The dedup tiebreak below is decided by (source_date, filename), NOT filesystem
        # mtime as this used to read. Every loaded file already carries a source_date -- real,
        # if the file declares one, or an mtime-derived fallback otherwise (see
        # load_projection_file) -- and that value is part of the file's own committed content,
        # not the filesystem's, so it survives a fresh checkout unchanged where mtime does not.
        #
        # mtime broke this twice, confirmed on real data both times. (1) The M13 backtest:
        # two checkouts of byte-identical baseline data produced different row orders under
        # mtime sorting, which flipped a real 13-point value swing on one player with zero
        # code difference. (2) The pre-freeze audit: simulating a reversed-order checkout
        # (plausible mtime assignment, nothing exotic) turned a single-source kicker pool into
        # an unintended MIXTURE of two differently-scored sources -- vendor Draft Sharks rows
        # sitting beside league-scored Sleeper rows in the same position, invisible in output.
        #
        # Filename remains the tiebreak for files sharing a date (four K/DST files in the
        # committed baseline all declare 2026-08-25) -- that has NOT become a semantic
        # precedence rule, it is still an arbitrary string comparison. What changed is that it
        # is now the ONLY thing left to depend on for that tie, and a filename is fixed and
        # checkout-order-independent where an mtime is not: the exact same tie resolves the
        # exact same way on every clone, forever, instead of accidentally doing so today.
        source_date = str(df["source_date"].iloc[0]) if "source_date" in df.columns and not df.empty else ""
        if kind == "free_agents":
            fa_entries.append((source_date, f.name, df))
        elif kind == "trade_value_chart":
            tvc_entries.append((source_date, f.name, df))
        else:
            score = _rankings_format_match_score(_detect_rankings_format(f.name), format_hint)
            rankings_entries.append((source_date, f.name, df, score))

    # trade_value_chart rows (asset_type/value, no rank/team/position-rank) have a
    # different shape than rankings rows -- a separate bucket, not folded into
    # rankings, so DataMerger.projections never mixes player rankings with rookie
    # pick slot/future pick rows that would never sensibly match a roster player.
    fa_entries.sort(key=lambda e: (e[0], e[1]))
    tvc_entries.sort(key=lambda e: (e[0], e[1]))
    rankings_entries.sort(key=lambda e: (e[0], e[1]))
    fa_frames = [df for _, _, df in fa_entries]
    tvc_frames = [df for _, _, df in tvc_entries]
    rankings_frames = [df for _, _, df, _ in rankings_entries]
    rankings_scores = [score for _, _, _, score in rankings_entries]

    if format_hint and len(rankings_frames) > 1:
        # Stable sort: among files tied on match score (e.g. two that both mismatch, or
        # multiple with no scoring opinion at all), the (source_date, filename) order above
        # still decides -- this only re-prioritizes real format matches, it doesn't invent a
        # new tiebreak for files a hint can't distinguish between.
        rankings_frames = [df for _, df in sorted(zip(rankings_scores, rankings_frames), key=lambda pair: pair[0])]

    return (
        _dedup_by_name_and_position(rankings_frames, empty),
        _dedup_by_name_and_position(fa_frames, empty),
        _dedup_by_name_and_position(tvc_frames, empty),
    )


def _dedup_by_name_and_position(frames: list[pd.DataFrame], empty: pd.DataFrame) -> pd.DataFrame:
    """Concat frames and drop to one row per player, the last frame's row winning ties --
    callers should order frames oldest/least-authoritative first, so a more specific or more
    recent source (a league's own file, a fresher upload) overrides an older/broader one for
    the same player. Keyed on (name, offense/IDP) rather than name alone, since two different
    real people can share a name across an offense file and an IDP file (a real example that
    surfaced merging baseline data: "Josh Allen" the Bills QB vs. "Josh Allen" a DL) --
    _position_group keeps those from silently shadowing each other while still letting a
    genuine same-player re-upload collapse onto its newest row as before.

    Deliberately NOT keyed on team too, despite that also disambiguating some same-name
    collisions (two real same-named same-position players, e.g. two different NFL WRs both
    named Mike Williams -- rarer, but real): unlike position, team legitimately changes for
    the *same* real person (a trade), so partitioning on it would make an older baseline row
    and a newer post-trade upload look like two different people and both survive as
    "duplicates" -- exactly the false-ambiguous outcome the newest-wins collapse exists to
    avoid, and the opposite of the "readjust as newer info comes in" baseline behavior. Team
    still rides along as a data field on the surviving row either way.
    """
    if not frames:
        return empty.copy()
    combined = pd.concat(frames, ignore_index=True, sort=False)
    if "position" in combined.columns:
        dedup_key = combined["norm_name"] + "|" + combined["position"].map(_position_group)
    else:
        dedup_key = combined["norm_name"]
    return combined.assign(_dedup_key=dedup_key).drop_duplicates(
        subset="_dedup_key", keep="last"
    ).drop(columns="_dedup_key")


def _merge_rankings(*frames: pd.DataFrame) -> pd.DataFrame:
    """Combine rankings frames from multiple pools (e.g. baseline + global + league-specific).

    Frames passed later win ties for the same player — callers should pass
    the more-specific/more-authoritative source last (a league's own
    rankings override should beat the shared global pool for that player).
    """
    non_empty = [f for f in frames if not f.empty]
    return _dedup_by_name_and_position(non_empty, pd.DataFrame(columns=["name", "norm_name"]))


def _compute_freshness(df: pd.DataFrame) -> tuple[Optional[str], Optional[int], bool]:
    if df.empty or "source_date" not in df.columns:
        return None, None, False
    dates = pd.to_datetime(df["source_date"], errors="coerce").dropna()
    if dates.empty:
        return None, None, False
    freshest = dates.max().date().isoformat()
    days = (datetime.now().date() - datetime.fromisoformat(freshest).date()).days
    return freshest, days, days >= STALE_AFTER_DAYS


def load_external_values(base_dir: Path = EXTERNAL_VALUES_DIR) -> pd.DataFrame:
    """Load every secondary valuation source under base_dir (one immediate subdirectory per
    source, e.g. data/baseline/external/dynastyprocess/) into a single frame tagged by which
    source each row came from. Unlike load_all's Draft Sharks pools, rows are never deduped
    across (or within) sources here -- the whole point of a secondary source is to show a
    second opinion alongside Draft Sharks', not to silently pick one number, so every source
    that has an opinion on a player survives. Column shape is whatever that source's own CSV
    has (see each source's ATTRIBUTION.md); only name -> norm_name is assumed universal.
    """
    base_dir = Path(base_dir)
    empty = pd.DataFrame(columns=["name", "norm_name", "source_name"])
    if not base_dir.exists():
        return empty

    frames = []
    for source_dir in sorted(p for p in base_dir.iterdir() if p.is_dir()):
        for f in sorted(source_dir.glob("*.csv")):
            try:
                df = pd.read_csv(f)
            except Exception:
                continue  # skip unparsable files rather than crashing the app
            if "name" not in df.columns:
                continue
            df["norm_name"] = df["name"].astype(str).map(normalize_name)
            df["source_name"] = source_dir.name
            df["source_file"] = f.name
            frames.append(df)

    if not frames:
        return empty
    return pd.concat(frames, ignore_index=True, sort=False)


def load_bot_research_as_external() -> pd.DataFrame:
    """Panel-vetted findings from bot_research.py (only the ones that carry a real rank
    number -- a qualitative claim has nothing to percentile-rank) reshaped into the same
    (name/norm_name/source_name/source_file) shape load_external_values' other sources
    produce, so they ride the exact same percentile/composite pipeline as every structured
    export -- weighted low (see COMPOSITE_SOURCE_WEIGHTS["bot_research"]) since this is an
    LLM's own read of a live search or a user's captioned reference item, not a deterministic
    parser's. Grouped under one synthetic (source_name="bot_research", source_file="findings")
    pair regardless of which real-world source each finding actually cites (ESPN, FantasyPros,
    whatever the panel turned up) -- the cited source rides along as its own "cited_source"
    field for display, but a fixed pair keeps the composite's percentile rules static rather
    than growing a new rule per citation.

    Only the newest finding per (player, cited source) is kept -- bot_research.json itself
    never deletes anything (a real record of everything the panel has ever found), but an
    outdated finding on the same player/source shouldn't keep pulling composite weight once a
    fresher one supersedes it, same "newest wins" rule every other baseline source follows.
    """
    import bot_research

    findings = [f for f in bot_research.load_findings() if f.get("rank") is not None]
    empty = pd.DataFrame(columns=["name", "norm_name", "source_name", "source_file"])
    if not findings:
        return empty

    latest: dict[tuple[str, str], dict] = {}
    for f in sorted(findings, key=lambda e: e.get("ts", 0)):
        key = (normalize_name(f.get("player_name", "")), f.get("source", ""))
        latest[key] = f

    rows = [
        {
            "name": f["player_name"], "norm_name": normalize_name(f["player_name"]),
            "source_name": "bot_research", "source_file": "findings",
            "cited_source": f.get("source"), "claim": f.get("claim"),
            "rank": f["rank"], "source_date": f.get("date"),
        }
        for f in latest.values()
    ]
    return pd.DataFrame(rows) if rows else empty


# -- manual name-matching overrides -------------------------------------------
#
# Automatic matching (key + fuzzy) mostly works, but a handful of players will
# always slip through — an unusual name shape, a mid-season team change that
# outpaces the loaded file, WR/RB dual eligibility, etc. Rather than requiring
# a code change, a Sleeper player's full name can be mapped directly to the
# exact name string Draft Sharks printed for them, bypassing automatic
# matching for just that player.

def load_aliases() -> dict[str, str]:
    """{sleeper_full_name: draft_sharks_printed_name} manual overrides."""
    if ALIASES_PATH.exists():
        try:
            return json.loads(ALIASES_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def save_alias(sleeper_full_name: str, draft_sharks_name: str) -> None:
    aliases = load_aliases()
    aliases[sleeper_full_name] = draft_sharks_name
    ALIASES_PATH.parent.mkdir(parents=True, exist_ok=True)
    ALIASES_PATH.write_text(json.dumps(aliases, indent=2))


def remove_alias(sleeper_full_name: str) -> None:
    aliases = load_aliases()
    if aliases.pop(sleeper_full_name, None) is not None:
        ALIASES_PATH.write_text(json.dumps(aliases, indent=2))


class DataMerger:
    """Fuzzy-matches Sleeper player records onto locally loaded Draft Sharks data.

    Loads from two pools: a shared global pool (format-based Dynasty Rankings and
    the Trade Value Chart -- same data correct for any league sharing that format)
    and, if league_dir is given, that one league's own folder (Free Agent Finder,
    always league-specific; a league-specific rankings/trade-value override, if
    ever added, takes priority over the global pool for the same player/asset).
    """

    def __init__(self, league_dir: Optional[Path] = None, global_dir: Path = GLOBAL_PROJECTIONS_DIR,
                 baseline_dir: Path = BASELINE_DIR, external_dir: Path = EXTERNAL_VALUES_DIR,
                 match_cutoff: float = 0.82, league_format: Optional[dict] = None):
        self.league_dir = Path(league_dir) if league_dir else None
        self.global_dir = Path(global_dir)
        self.baseline_dir = Path(baseline_dir)
        self.external_dir = Path(external_dir)
        self.match_cutoff = match_cutoff
        # {"scoring", "superflex", "te_premium"} -- which of the several format-specific
        # Dynasty Rankings exports to prefer when the same player appears in more than one
        # (see load_all's format_hint). None means no opinion: whichever file sorts last by
        # mtime keeps winning, same as before this existed. Set via set_league_format once the
        # active league's real format is known, not required at construction time.
        self.league_format = league_format
        self._load()

    def _load(self) -> None:
        empty = pd.DataFrame(columns=["name", "norm_name"])
        baseline_rankings, _, _ = load_all(self.baseline_dir / "rankings", format_hint=self.league_format)
        _, _, baseline_tvc = load_all(self.baseline_dir / "trade_value", default_kind="trade_value_chart")
        global_rankings, _, global_tvc = load_all(self.global_dir, format_hint=self.league_format)
        if self.league_dir:
            league_rankings, league_fa, league_tvc = load_all(self.league_dir, format_hint=self.league_format)
        else:
            league_rankings, league_fa, league_tvc = empty.copy(), empty.copy(), empty.copy()
        self.projections = _merge_rankings(baseline_rankings, global_rankings, league_rankings)
        self.free_agents = league_fa
        self.trade_values = _merge_rankings(baseline_tvc, global_tvc, league_tvc)
        # Precomputed once per _load()/reload(), not per lookup -- _find_match's fuzzy key
        # match used to recompute name_key() over every row of whichever table it was searching
        # on EVERY call (measured: ~11ms per composite_player_score call, ~330ms for a 30-player
        # roster table, every single rerun). A column survives normal pandas filtering (e.g.
        # app.py's own `trade_values[trade_values["asset_type"] == "player"]`), so any view
        # derived from one of these three tables still carries it.
        external_values = load_external_values(self.external_dir)
        bot_research_rows = load_bot_research_as_external()
        self.external_values = (
            pd.concat([external_values, bot_research_rows], ignore_index=True, sort=False)
            if not bot_research_rows.empty else external_values
        )
        for _df in (self.projections, self.free_agents, self.trade_values, self.external_values):
            if not _df.empty and "norm_name" in _df.columns:
                _df["_name_key"] = _df["norm_name"].map(name_key)
        self._compute_percentiles()
        self.aliases = load_aliases()

    def _compute_percentiles(self) -> None:
        """Populate "_pct" (0-100, higher always better) and "_pool_n" (how many rows that
        percentile was actually computed against -- see composite_player_score's pool-size
        dampening) on projections and on each (source, file) pair external_player_values/
        composite_player_score know how to read -- see _EXTERNAL_PERCENTILE_RULES. Computed
        once per _load() rather than per lookup since a percentile is only meaningful against
        the *whole* pool it's ranked within, and recomputing that per player would be wasteful
        for what's the same number every time until the next reload()."""
        if "trade_value" in self.projections.columns:
            # Draft Sharks' trade_value is already a 0-100 scale, and -- unlike every external
            # source here -- already scarcity-adjusted by position: elite offense reaches 100
            # while even elite IDP tops out around 35-45 by Draft Sharks' own judgment. A
            # percentile-of-trade_value transform used to run here, ranking each row against
            # the WHOLE pool (offense and IDP mixed) -- but that pool is heavily bottom-loaded
            # with bench/depth players at every position, so almost anyone with a real starting
            # role clears the 80th percentile regardless of how good they actually are.
            # Confirmed live: Joe Burrow (trade_value 32, a clear QB1) and Zack Baun (trade_value
            # 28, a solid but unspectacular LB) came out at 83.3 and 81.1 respectively -- nearly
            # identical, even though Draft Sharks' own raw scale already says they aren't
            # remotely comparable assets. Segmenting the percentile by position (the fix that
            # correctly solved this same class of problem for bot_research's position-relative
            # rank claims) would make this WORSE here, not better: it would rank Baun against
            # only the shallow, low-ceiling IDP pool, pushing his percentile even higher. Using
            # trade_value directly (already on the composite's own 0-100 scale, no transform
            # needed) is what actually preserves Draft Sharks' own real scarcity signal instead
            # of erasing it with a distribution-shape artifact.
            self.projections["_pct"] = self.projections["trade_value"].clip(0, 100)
            self.projections["_pool_n"] = int(self.projections["trade_value"].notna().sum())

        if self.external_values.empty:
            return
        self.external_values["_pct"] = float("nan")
        self.external_values["_pool_n"] = float("nan")

        # Draft Sharks' own norm_name is first-initial-only ("m crosby", not "maxx crosby" --
        # see _find_match's docstring), so a plain norm_name-to-norm_name join against it would
        # silently miss almost everyone. Key on name_key(), the same shared key _find_match
        # uses to bridge that abbreviation, rather than exact-string equality.
        position_by_key: dict[tuple[str, str], str] = {}
        if "position" in self.projections.columns:
            for norm, pos in zip(self.projections["norm_name"], self.projections["position"]):
                if pd.isna(pos):
                    continue
                position_by_key.setdefault(name_key(norm), pos)
        for (source, source_file), (field, higher_is_better) in _EXTERNAL_PERCENTILE_RULES.items():
            mask = (
                (self.external_values["source_name"] == source)
                & (self.external_values["source_file"] == source_file)
            )
            if field not in self.external_values.columns:
                continue
            # KTC's one CSV holds both players and picks on the same list -- a player's
            # percentile should be computed against other PLAYERS only, not diluted by picks.
            # Sources with no asset_type column at all (everything except KTC) get NaN here,
            # which fillna("player") treats as "doesn't apply, don't filter" rather than
            # excluding every row from a source that was never picks/players split to begin with.
            if "asset_type" in self.external_values.columns:
                mask = mask & (self.external_values["asset_type"].fillna("player") == "player")

            # bot_research findings carry whatever rank number the source itself used, which is
            # very often POSITION-RELATIVE ("#1 DL", "#1 RB") rather than a cross-position
            # overall rank -- confirmed the hard way: a same-valued "#1" claim for an IDP player
            # and an offense player landed on the identical percentile when pooled together,
            # even though a #1 RB is worth far more than a #1 DL in real dynasty terms (the
            # same scarcity gap Draft Sharks' own trade_value already reflects structurally).
            # Segment by offense/IDP group, looked up from the broader Draft Sharks pool (which
            # covers both), same distinction _position_group draws for the dedup collision fix.
            if source == "bot_research" and position_by_key:
                row_groups = self.external_values["norm_name"].map(
                    lambda n: _position_group(position_by_key.get(name_key(n)))
                )
                for group_value in row_groups[mask].unique():
                    group_mask = mask & (row_groups == group_value)
                    pct = self.external_values.loc[group_mask, field].rank(pct=True, ascending=higher_is_better) * 100
                    self.external_values.loc[group_mask, "_pct"] = pct
                    self.external_values.loc[group_mask, "_pool_n"] = int(group_mask.sum())
                continue

            pct = self.external_values.loc[mask, field].rank(pct=True, ascending=higher_is_better) * 100
            self.external_values.loc[mask, "_pct"] = pct
            self.external_values.loc[mask, "_pool_n"] = int(mask.sum())

    def reload(self) -> None:
        self._load()

    def set_league_format(self, league_format: Optional[dict]) -> None:
        """Update which format (scoring/superflex/te_premium) to prefer when a player appears
        in more than one baseline/global Dynasty Rankings export, and reload if it actually
        changed. Meant to be called every rerun with the currently active league's real format
        (app.py does this right after resolving league_format_summary) -- cheap no-op via the
        equality check below when nothing's changed, so this is safe to call unconditionally
        rather than needing the caller to track whether a reload is actually warranted."""
        if league_format == self.league_format:
            return
        self.league_format = league_format
        self.reload()

    @property
    def is_loaded(self) -> bool:
        return not self.projections.empty

    @property
    def is_free_agents_loaded(self) -> bool:
        return not self.free_agents.empty

    @property
    def is_trade_values_loaded(self) -> bool:
        return not self.trade_values.empty

    @property
    def freshest_date(self) -> Optional[str]:
        return _compute_freshness(self.projections)[0]

    @property
    def staleness_days(self) -> Optional[int]:
        return _compute_freshness(self.projections)[1]

    @property
    def is_stale(self) -> bool:
        return _compute_freshness(self.projections)[2]

    @property
    def free_agents_freshest_date(self) -> Optional[str]:
        return _compute_freshness(self.free_agents)[0]

    @property
    def free_agents_staleness_days(self) -> Optional[int]:
        return _compute_freshness(self.free_agents)[1]

    @property
    def free_agents_is_stale(self) -> bool:
        return _compute_freshness(self.free_agents)[2]

    @property
    def trade_values_freshest_date(self) -> Optional[str]:
        return _compute_freshness(self.trade_values)[0]

    @property
    def trade_values_staleness_days(self) -> Optional[int]:
        return _compute_freshness(self.trade_values)[1]

    @property
    def trade_values_is_stale(self) -> bool:
        return _compute_freshness(self.trade_values)[2]

    def pick_value(self, label: str) -> Optional[int]:
        """Look up a rookie/future pick's Trade Value Chart price by its exact label
        (e.g. "1.03", "2027 Random Rd 1") -- price only, never ownership. Which team
        actually holds a pick is Sleeper's traded-picks data to say, not Draft Sharks'."""
        if self.trade_values.empty:
            return None
        match = self.trade_values[self.trade_values["norm_name"] == normalize_name(label)]
        return int(match.iloc[0]["value"]) if not match.empty else None

    @staticmethod
    def _contradicted(row: pd.Series, position: Optional[str], team: Optional[str]) -> bool:
        """Does anything KNOWN on both sides say this row is a different person?

        Unknown on either side is not evidence of a mismatch -- an absent position or team must
        not manufacture a contradiction any more than it may manufacture a match. Only a
        disagreement between two values that both exist rejects.
        """
        if team and "team" in row.index and pd.notna(row.get("team")) and str(row["team"]) != str(team):
            return True
        if position and "position" in row.index and pd.notna(row.get("position")):
            queried, matched = position_family(position), position_family(row["position"])
            if queried and matched and queried != matched:
                return True
        return False

    @staticmethod
    def _different_identity_namespace(row: pd.Series, position: Optional[str]) -> bool:
        """Do these two rows sit in different dedup identity namespaces?

        _dedup_by_name_and_position already treats rows in different _position_group buckets as
        two different PEOPLE -- that is what stops "Josh Allen" the QB and "Josh Allen" the DL
        from collapsing onto one record. A resolution that crosses that boundary therefore
        contradicts the merger's own identity model, whatever path it took to get there.

        Deliberately the coarse group, not position_family: a real edge rusher is exported as
        LB by one vendor and DL by another, and both are `idp`, so this leaves those 20 real
        matches alone while rejecting a WR resolving onto a DB.
        """
        if not position or "position" not in row.index or pd.isna(row.get("position")):
            return False
        return _position_group(position) != _position_group(row["position"])

    def _find_match(self, full_name: str, position: Optional[str] = None,
                     team: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> Optional[pd.Series]:
        """The matched row alone, for the callers that only want that. See _resolve."""
        return self._resolve(full_name, position=position, team=team, df=df)[0]

    def _resolve(self, full_name: str, position: Optional[str] = None,
                  team: Optional[str] = None, df: Optional[pd.DataFrame] = None
                  ) -> tuple[Optional[pd.Series], Optional[str], int, bool]:
        """(row, path, candidate_count, verified) -- the match AND how confident the match is.

        Ambiguity is a property of the resolution, so it is returned with it. It used to be
        neither returned nor recorded, which made a silent first-candidate pick indistinguishable
        from an unambiguous exact hit at every call site; app.py's trade calculator had to
        recompute name_key itself to close that gap for one caller. `verified` is True only when
        exactly one row survived, so a caller can tell "this is the player" from "this is the
        first of several that fit".

        Match a Sleeper player onto a row of the given table (default: self.projections).

        Draft Sharks' PDFs give first-initial-only names ("J Chase", not
        "Ja'Marr Chase"), which tanks a naive whole-string fuzzy ratio for anyone
        whose real first name is longer than one letter. So we first try an exact
        (first-initial, last-name) key match — robust to that abbreviation — and
        only fall back to fuzzy whole-string matching for vendors that do export
        full names. Team/position disambiguate when multiple players share a key.

        A manual alias (self.aliases, see load_aliases/save_alias) short-circuits
        all of that with an exact-name lookup, for the handful of players who
        never match automatically no matter what.
        """
        table = self.projections if df is None else df
        if table.empty or not full_name:
            return None, None, 0, False

        alias = self.aliases.get(full_name)
        if alias:
            exact = table[table["norm_name"] == normalize_name(alias)]
            if not exact.empty:
                if len(exact) > 1 and team and "team" in exact.columns:
                    narrowed = exact[exact["team"] == team]
                    if not narrowed.empty:
                        exact = narrowed
                return exact.iloc[0], "alias", len(exact), True
            # alias didn't resolve in this particular table (e.g. player isn't in
            # the free-agent table) — fall through to normal matching below

        norm_name = normalize_name(full_name)
        tokens = norm_name.split()
        if not tokens:
            return None, None, 0, False

        # Try an exact normalized-name match before the fuzzy key below. Vendors that export
        # full names (unlike Draft Sharks' own first-initial-only PDFs) can be matched exactly
        # -- which matters because the (first-initial, LAST TOKEN) key can't safely distinguish
        # two different people whose last token happens to collide: "A.J. Brown" normalizes to
        # "aj brown" and "Amon-Ra St. Brown" to "amonra st brown", both keying to ('a','brown').
        # Confirmed live: the Trade Value Chart holds an exact "aj brown" row (tv=37) that the
        # key match below discarded in favor of "amonra st brown" (tv=83) for BOTH players --
        # a real player getting silently priced as a different one. An exact match against
        # Draft Sharks' own abbreviated table just won't hit (its rows never spell out a full
        # first name), so this falls through to the existing key logic there unaffected.
        exact_matches = table[table["norm_name"] == norm_name]
        if not exact_matches.empty:
            if len(exact_matches) > 1 and team and "team" in exact_matches.columns:
                narrowed = exact_matches[exact_matches["team"] == team]
                if not narrowed.empty:
                    exact_matches = narrowed
            if len(exact_matches) > 1 and position and "position" in exact_matches.columns:
                narrowed = exact_matches[exact_matches["position"] == position]
                if not narrowed.empty:
                    exact_matches = narrowed
            return exact_matches.iloc[0], "exact", len(exact_matches), len(exact_matches) == 1

        key = name_key(norm_name)
        # Use the precomputed column when this table has one (every table _load() builds
        # does) -- falls back to computing it on the fly for an ad hoc table (e.g. a
        # one-off external-source subset) that never went through _load().
        row_keys = table["_name_key"] if "_name_key" in table.columns else table["norm_name"].map(name_key)
        key_matches = table[row_keys == key]
        if not key_matches.empty:
            if len(key_matches) > 1 and team and "team" in key_matches.columns:
                narrowed = key_matches[key_matches["team"] == team]
                if not narrowed.empty:
                    key_matches = narrowed
            if len(key_matches) > 1 and position and "position" in key_matches.columns:
                narrowed = key_matches[key_matches["position"] == position]
                if not narrowed.empty:
                    key_matches = narrowed
            candidate = key_matches.iloc[0]
            # (first-initial, rest-of-name) is a lossy hash -- two real people can share
            # BOTH their first initial and their entire remaining name, which the team/
            # position narrowing above can't fix when Draft Sharks' own first-initial-only
            # export never gave a second row to narrow against in the first place.
            # Confirmed live: the committed baseline has exactly one "B Robinson" row
            # (Bijan Robinson, team=ATL, trade_value=99) -- querying this same table for
            # the real, different Brian Robinson (team=WAS) still returned Bijan's row
            # unmodified with nothing to narrow against, silently pricing a bench RB as a
            # top-5 dynasty asset. A team that's known on both sides and disagrees is real
            # evidence this is a different person, not the same player traded since --
            # reject outright (no match, not a guess) rather than hand back someone else's
            # value. Scoped to this key-based path only: an EXACT full-name match (above)
            # is not a lossy hash, so a team mismatch there is far more likely just stale
            # roster data than a misidentified player, and shouldn't be thrown out.
            if team and "team" in table.columns and pd.notna(candidate.get("team")) and candidate["team"] != team:
                return None, None, len(key_matches), False
            # Same rejection, on the other axis the merger already treats as identity: a
            # same-team, same-key pair can still be two different people if they sit in
            # different dedup namespaces (confirmed live -- a WR resolving onto a DB who
            # happened to share a club and a first initial, which the team check above cannot
            # see). Only the coarse group, so the LB/DL vocabulary split between vendors stays
            # a match.
            if self._different_identity_namespace(candidate, position):
                return None, None, len(key_matches), False
            return candidate, "key", len(key_matches), len(key_matches) == 1

        # The fallback of last resort, and the only path with no key holding it together --
        # so it is the one that must be able to decline. It used to prefer a position-matching
        # candidate and then return candidates[0] regardless, checking team nowhere at all: the
        # rejection rule added to the key path above (see the Bijan/Brian Robinson comment) was
        # never carried down here. Measured on the real committed baseline before this changed,
        # EVERY fuzzy match that resolved against a team-bearing query was a different real
        # person -- 9 of 9 -- each one handing that person's projection, trade value and 3-year
        # outlook to someone else. Guessing and declining are different outcomes, and only one
        # of them is acceptable for a field that becomes a valuation input.
        choices = table["norm_name"].tolist()
        candidates = difflib.get_close_matches(norm_name, choices, n=3, cutoff=self.match_cutoff)
        if not candidates:
            return None, None, 0, False
        survivors = []
        for cand in candidates:
            for _, row in table[table["norm_name"] == cand].iterrows():
                if not self._contradicted(row, position, team):
                    survivors.append(row)
        if not survivors:
            return None, None, len(candidates), False
        return survivors[0], "fuzzy", len(survivors), len(survivors) == 1

    def merge_player(self, player_full_name: str, position: Optional[str] = None,
                      team: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> dict:
        """Return matched fields (tier/vorp/projection/trade_value/rank/...) for one player,
        plus how the match was reached.

        match_path       -- "alias" / "exact" / "key" / "fuzzy", or None on a miss
        match_candidates -- how many rows survived as plausible; 0 on a miss
        match_verified   -- True only when exactly one row fit, so a caller can tell "this is
                            the player" from "this is the first of several that fit"

        Those three exist because ambiguity is a property of the resolution and belongs to the
        producer. Without them a silent first-candidate pick was indistinguishable from an
        unambiguous exact hit at every call site, and the one consumer that needed the
        distinction (app.py's trade calculator, free-text input with no position to narrow on)
        had to recompute name_key itself to recover it."""
        match, path, candidates, verified = self._resolve(
            player_full_name, position=position, team=team, df=df)
        if match is None:
            return {"matched": False, "match_path": None,
                    "match_candidates": candidates, "match_verified": False}
        # The identity of the row that was matched, not of the query -- so a caller can tell
        # whether two different players resolved onto the SAME canonical record. Deliberately
        # (norm_name, position_group): the dedup identity namespace, which is what makes two
        # rows one record in the first place. Namespaced with the other match_ fields so it
        # never collides with a caller's own "name"/"position" keys (build_roster_table
        # row.update()s this straight onto a Sleeper-derived row).
        row = {"matched": True, "match_path": path,
               "match_candidates": candidates, "match_verified": verified,
               "match_canonical_key": (str(match.get("norm_name")),
                                       _position_group(match.get("position")))}
        for field in ("projection", "vorp", "tier", "trade_value", "rank",
                       "position", "team", "pos_rank", "proj_3yr",
                       "roster_status", "proj_3d", "ros_3d", "ceiling", "value_3d",
                       # "value" is the Trade Value Chart's own column name (see
                       # parse_draftsharks_trade_value_chart_pdf) -- that table never goes
                       # through _normalize_columns' header-alias renaming the way CSV/JSON
                       # uploads do, so it's the one table where this whitelist needs both
                       # names to actually surface a price.
                       "value",
                       "source_file", "source_date"):
            if field in match.index and pd.notna(match[field]):
                row[field] = match[field]
        return row

    @property
    def is_external_values_loaded(self) -> bool:
        return not self.external_values.empty

    def composite_capable_source_names(self) -> list[str]:
        """Distinct source_name values currently loaded that can ACTUALLY feed
        composite_player_score -- i.e. have at least one (source_name, source_file) pair in
        _EXTERNAL_PERCENTILE_RULES -- not just every source_name present in external_values.
        Exists because "is this source loaded at all" and "can this source's data ever reach
        the composite" are different questions: ESPN's only baseline file is redraft-scope and
        structurally excluded from the composite entirely (same for FantasyPros' best-ball/
        IDP-redraft files, which sit alongside its dynasty file under the same source_name),
        so a caller (the sidebar's "Composite Sources Loaded" status) that just counted every
        distinct source_name present would overstate what's actually contributing."""
        if self.external_values.empty:
            return []
        capable_source_names = {source for source, _file in _EXTERNAL_PERCENTILE_RULES}
        return sorted(
            n for n in self.external_values["source_name"].dropna().unique()
            if n in capable_source_names
        )

    def external_player_values(self, player_full_name: str, position: Optional[str] = None,
                                team: Optional[str] = None) -> list[dict]:
        """One dict per (source, file) that has an opinion on this player (see
        load_external_values) -- each carrying whatever fields that file's own CSV provides,
        tagged with which source/file it's from. Grouped by file, not just source: one source
        directory can hold multiple distinct lists (e.g. fantasypros/ has a dynasty PPR list
        and a separate, season-long best-ball list) that can both cover the same player with
        different numbers -- collapsing to one row per source would silently drop one of them.
        Unlike merge_player, there's no fixed field whitelist here: a source's columns aren't
        predictable in advance the way Draft Sharks' few known export shapes are, so every
        non-null field on the matched row rides along. Deliberately returns every matching
        (source, file) rather than one "winning" value -- Draft Sharks isn't meant to be the
        only word on a player's worth, so neither is any other single source."""
        if self.external_values.empty or "source_name" not in self.external_values.columns:
            return []
        results = []
        group_cols = ["source_name", "source_file"] if "source_file" in self.external_values.columns else ["source_name"]
        for _, sub in self.external_values.groupby(group_cols, sort=True):
            match = self._find_match(player_full_name, position=position, team=team, df=sub)
            if match is None:
                continue
            row = {k: v for k, v in match.items() if pd.notna(v) and k != "norm_name"}
            results.append(row)
        return results

    def composite_player_score(self, player_full_name: str, position: Optional[str] = None,
                                team: Optional[str] = None) -> Optional[dict]:
        """This app's own single blended read on a player (see the COMPOSITE_* constants'
        docstring for the weighting rationale) -- a weighted average across sources, never a
        raw-number average of scales that don't mean the same thing. Every EXTERNAL source
        (DynastyProcess, FantasyPros, KeepTradeCut, bot_research) gets converted to a percentile
        within its OWN pool first, the only sound way to combine scales this incompatible
        (~0-10000, rank-out-of-552, ~0-9999, a bare rank number). Draft Sharks itself is the one
        exception: its trade_value is already a 0-100 scale AND already scarcity-adjusted by
        position (see _compute_percentiles' own comment on why re-deriving a percentile from it
        actually erases that signal instead of preserving it), so it's used directly rather than
        re-normalized. Returns None when not one source has an opinion, rather than fabricating
        a score from nothing.

        This is always an ADDITIONAL field, never a replacement: it does not feed the trade
        calculator's pricing math (that stays Draft-Sharks-scaled, exactly as tested), and
        every bot-facing context keeps showing every source's own raw number regardless of
        whether this ran -- see merge_player/external_player_values, still called
        independently everywhere they already were."""
        components: list[dict] = []

        def _pool_factor(pool_size: int) -> float:
            # A percentile earned against a handful of rows doesn't mean what it would against
            # hundreds -- see COMPOSITE_MIN_TRUSTED_POOL_SIZE's own docstring for the concrete
            # bug this exists to prevent (a 1-row pool always reads its only member as the
            # 100th percentile, regardless of how good the underlying claim actually is).
            return min(1.0, pool_size / COMPOSITE_MIN_TRUSTED_POOL_SIZE)

        if "_pct" in self.projections.columns:
            ds_match = self._find_match(player_full_name, position=position, team=team, df=self.projections)
            if ds_match is not None and pd.notna(ds_match.get("_pct")):
                source_date = ds_match.get("source_date")
                pool_size = int(ds_match.get("_pool_n") or 0)
                components.append({
                    "source": "draftsharks", "raw": ds_match.get("trade_value"),
                    "percentile": float(ds_match["_pct"]), "source_date": source_date,
                    "pool_size": pool_size,
                    "weight": COMPOSITE_SOURCE_WEIGHTS["draftsharks"] * _recency_weight(source_date) * _pool_factor(pool_size),
                })

        if not self.external_values.empty:
            for (source, source_file), (field, _) in _EXTERNAL_PERCENTILE_RULES.items():
                sub = self.external_values[
                    (self.external_values["source_name"] == source)
                    & (self.external_values["source_file"] == source_file)
                ]
                if sub.empty:
                    continue
                match = self._find_match(player_full_name, position=position, team=team, df=sub)
                if match is None or pd.isna(match.get("_pct")):
                    continue
                source_date = match.get("source_date")
                # Read the pool size _compute_percentiles already recorded for this exact row
                # rather than recounting sub here -- bot_research segments its pool by offense/
                # IDP position group (see _compute_percentiles), so a flat count over all of sub
                # would overstate how many rows this player's own percentile was actually earned
                # against.
                pool_size = int(match.get("_pool_n") or 0)
                components.append({
                    "source": source, "raw": match.get(field),
                    "percentile": float(match["_pct"]), "source_date": source_date,
                    "weight": COMPOSITE_SOURCE_WEIGHTS.get(source, 1.0) * _recency_weight(source_date) * _pool_factor(pool_size),
                    "pool_size": pool_size,
                })

        if not components:
            return None

        total_weight = sum(c["weight"] for c in components)
        if total_weight <= 0:
            return None
        score = sum(c["percentile"] * c["weight"] for c in components) / total_weight

        ages = []
        for c in components:
            if not c.get("source_date"):
                continue
            try:
                ages.append((datetime.now().date() - datetime.fromisoformat(str(c["source_date"])).date()).days)
            except ValueError:
                continue
        avg_age = sum(ages) / len(ages) if ages else None

        return {
            "score": round(score, 1),
            "recency_grade": recency_grade(avg_age),
            "avg_age_days": round(avg_age, 1) if avg_age is not None else None,
            "components": components,
        }

    def list_free_agents(self, exclude_mine: bool = True, position: Optional[str] = None,
                          top_n: Optional[int] = None) -> list[dict]:
        """Free Agent Finder rows, sorted by 3D Value+ descending."""
        df = self.free_agents
        if df.empty:
            return []
        if exclude_mine and "roster_status" in df.columns:
            df = df[df["roster_status"] != "Mine"]
        if position and "position" in df.columns:
            df = df[df["position"] == position]
        if "value_3d" in df.columns:
            df = df.sort_values("value_3d", ascending=False, na_position="last")
        if top_n:
            df = df.head(top_n)
        return df.to_dict("records")

    def build_roster_table(self, player_ids: list[str], players_db: dict[str, dict]) -> list[dict]:
        """Build one row per player id, joining Sleeper metadata with Draft Sharks data."""
        rows = []
        for pid in player_ids:
            info = players_db.get(pid, {}) or {}
            full_name = info.get("full_name") or f"{info.get('first_name', '')} {info.get('last_name', '')}".strip()
            full_name = full_name or pid
            position = info.get("position", "?")
            team = info.get("team") or "FA"
            row = {
                "player_id": pid,
                "name": full_name,
                "position": position,
                "team": team,
                "injury_status": info.get("injury_status"),
            }
            row.update(self.merge_player(full_name, position=position, team=team))

            if self.is_free_agents_loaded:
                fa_info = self.merge_player(full_name, position=position, team=team, df=self.free_agents)
                if fa_info.get("matched"):
                    if "ros_3d" in fa_info:
                        row["fa_ros_proj"] = fa_info["ros_3d"]
                    if "ceiling" in fa_info:
                        row["fa_ceiling"] = fa_info["ceiling"]
                    if "value_3d" in fa_info:
                        row["fa_value"] = fa_info["value_3d"]

            if self.is_external_values_loaded:
                row["external_values"] = self.external_player_values(full_name, position=position, team=team)

            composite = self.composite_player_score(full_name, position=position, team=team)
            if composite is not None:
                row["composite"] = composite

            rows.append(row)
        return rows
