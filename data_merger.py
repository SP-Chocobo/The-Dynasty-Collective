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
# the league (standard leagues get K/DEF, IDP leagues also get LB/DL/DB).
POSITION_CODES = ("QB", "RB", "WR", "TE", "K", "DEF", "LB", "DL", "DB")
IDP_POSITIONS = {"LB", "DL", "DB"}


def _position_group(position) -> str:
    """Broad offense/IDP bucket so a same-named offensive and IDP player (a real
    example that surfaced merging baseline data: "Josh Allen" the Bills QB vs.
    "Josh Allen" a DL) never silently collide as the same dedup key in
    _dedup_by_name_and_position below."""
    if not isinstance(position, str) or not position:
        return ""
    return "idp" if position.upper() in IDP_POSITIONS else "offense"


_REVIEWED_DATE_RE = re.compile(r"Reviewed By[^|]*\|([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})")


def _extract_reviewed_date(full_text: str) -> Optional[str]:
    match = _REVIEWED_DATE_RE.search(full_text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def _sniff_pdf_kind(path: Path) -> str:
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
        return "rankings"
    upper = text.upper()
    if "TRADE VALUE CHART" in upper:
        return "trade_value_chart"
    if "FREE AGENT FINDER" in upper or "3D ROS" in upper:
        return "free_agents"
    if "LEAGUE ANALYZER" in upper or "LEAGUE POWER RANKINGS" in upper:
        return "league_analyzer"
    return "rankings"


# -- Dynasty Rankings tool -----------------------------------------------------

_RANKINGS_STAT_RE = re.compile(r"^(\d+) ([\d,]+) ([\d,]+) (\d+)$")
_RANKINGS_TEAM_POS_RE = re.compile(rf"^({'|'.join(NFL_TEAM_CODES)})\s*({'|'.join(POSITION_CODES)})(\d+)$")


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

    for page in reader.pages:
        text = page.extract_text()
        full_text_parts.append(text)
        lines = [l.strip() for l in text.split("\n")]

        stat_rows: list[tuple[int, int, int, int]] = []
        name_rows: list[dict] = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stat_match = _RANKINGS_STAT_RE.match(line)
            if stat_match:
                rank, proj_1yr, proj_3yr, value_3d = stat_match.groups()
                stat_rows.append((int(rank), int(proj_1yr.replace(",", "")),
                                   int(proj_3yr.replace(",", "")), int(value_3d)))
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

    for page in reader.pages:
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


def load_all(
    projections_dir: Path = PROJECTIONS_DIR, default_kind: str = "rankings"
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Parse every CSV/JSON/PDF once, bucketed into (rankings_df, free_agents_df, trade_values_df).

    default_kind is forwarded to load_projection_file for CSV/JSON files -- see its docstring.
    """
    projections_dir = Path(projections_dir)
    empty = pd.DataFrame(columns=["name", "norm_name"])
    if not projections_dir.exists():
        return empty, empty.copy(), empty.copy()

    files = sorted(
        [p for p in projections_dir.iterdir() if p.suffix.lower() in (".csv", ".json", ".pdf")],
        key=lambda p: p.stat().st_mtime,
    )
    rankings_frames, fa_frames, tvc_frames = [], [], []
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
        # trade_value_chart rows (asset_type/value, no rank/team/position-rank) have a
        # different shape than rankings rows -- a separate bucket, not folded into
        # rankings, so DataMerger.projections never mixes player rankings with rookie
        # pick slot/future pick rows that would never sensibly match a roster player.
        if kind == "free_agents":
            fa_frames.append(df)
        elif kind == "trade_value_chart":
            tvc_frames.append(df)
        else:
            rankings_frames.append(df)

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
                 match_cutoff: float = 0.82):
        self.league_dir = Path(league_dir) if league_dir else None
        self.global_dir = Path(global_dir)
        self.baseline_dir = Path(baseline_dir)
        self.external_dir = Path(external_dir)
        self.match_cutoff = match_cutoff
        self._load()

    def _load(self) -> None:
        empty = pd.DataFrame(columns=["name", "norm_name"])
        baseline_rankings, _, _ = load_all(self.baseline_dir / "rankings")
        _, _, baseline_tvc = load_all(self.baseline_dir / "trade_value", default_kind="trade_value_chart")
        global_rankings, _, global_tvc = load_all(self.global_dir)
        if self.league_dir:
            league_rankings, league_fa, league_tvc = load_all(self.league_dir)
        else:
            league_rankings, league_fa, league_tvc = empty.copy(), empty.copy(), empty.copy()
        self.projections = _merge_rankings(baseline_rankings, global_rankings, league_rankings)
        self.free_agents = league_fa
        self.trade_values = _merge_rankings(baseline_tvc, global_tvc, league_tvc)
        self.external_values = load_external_values(self.external_dir)
        self.aliases = load_aliases()

    def reload(self) -> None:
        self._load()

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

    def _find_match(self, full_name: str, position: Optional[str] = None,
                     team: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> Optional[pd.Series]:
        """Match a Sleeper player onto a row of the given table (default: self.projections).

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
            return None

        alias = self.aliases.get(full_name)
        if alias:
            exact = table[table["norm_name"] == normalize_name(alias)]
            if not exact.empty:
                if len(exact) > 1 and team and "team" in exact.columns:
                    narrowed = exact[exact["team"] == team]
                    if not narrowed.empty:
                        exact = narrowed
                return exact.iloc[0]
            # alias didn't resolve in this particular table (e.g. player isn't in
            # the free-agent table) — fall through to normal matching below

        norm_name = normalize_name(full_name)
        tokens = norm_name.split()
        if not tokens:
            return None
        key = (tokens[0][0], tokens[-1])

        def row_key(row_norm: str) -> tuple[str, str]:
            t = row_norm.split()
            return (t[0][0], t[-1]) if t else ("", "")

        key_matches = table[table["norm_name"].map(row_key) == key]
        if not key_matches.empty:
            if len(key_matches) > 1 and team and "team" in key_matches.columns:
                narrowed = key_matches[key_matches["team"] == team]
                if not narrowed.empty:
                    key_matches = narrowed
            if len(key_matches) > 1 and position and "position" in key_matches.columns:
                narrowed = key_matches[key_matches["position"] == position]
                if not narrowed.empty:
                    key_matches = narrowed
            return key_matches.iloc[0]

        choices = table["norm_name"].tolist()
        candidates = difflib.get_close_matches(norm_name, choices, n=3, cutoff=self.match_cutoff)
        if not candidates:
            return None
        if position and "position" in table.columns:
            for cand in candidates:
                rows = table[table["norm_name"] == cand]
                pos_match = rows[rows["position"] == position]
                if not pos_match.empty:
                    return pos_match.iloc[0]
        return table[table["norm_name"] == candidates[0]].iloc[0]

    def merge_player(self, player_full_name: str, position: Optional[str] = None,
                      team: Optional[str] = None, df: Optional[pd.DataFrame] = None) -> dict:
        """Return matched fields (tier/vorp/projection/trade_value/rank/...) for one player."""
        match = self._find_match(player_full_name, position=position, team=team, df=df)
        if match is None:
            return {"matched": False}
        row = {"matched": True}
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

            rows.append(row)
        return rows
