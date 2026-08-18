"""
Draft Sharks / War Room projection parser and merger.

Reads locally-saved premium exports (Draft Sharks 3D projections, War Room
tiers, FantasyPros, Dynasty Process, etc.) and fuzzy-matches them onto
Sleeper player records by name. Nothing here ever calls out to a paid
vendor's API — the files stay local, satisfying each vendor's terms of
service.

Draft Sharks' tools split cleanly into two categories, and DataMerger
stores them accordingly:

  * The "Dynasty Rankings" tool -> parse_draftsharks_pdf(): a format-based
    overall ranking (1yr proj, 3yr proj, 3D Value) — computed from PPR/
    standard, superflex/1QB, TE-premium assumptions, not from any specific
    league's roster. The *same* export is correct for every league sharing
    that format, so it lives in a shared pool (GLOBAL_PROJECTIONS_DIR,
    data/projections/_global/) rather than being re-uploaded per league.
  * The "Free Agent Finder" tool -> parse_draftsharks_free_agents_pdf(): a
    rest-of-season, this-league-contextual view (3D Proj, 3D ROS, Ceiling,
    3D Value+) that also tags each row Mine/Add/Drop/Lock, i.e. whether
    Draft Sharks considers the player already on *your* roster in *this*
    league. This can never be shared — DataMerger only ever loads it from
    one league's own folder (data/projections/<league_id>/).

Both kinds are auto-detected from a PDF's own text, not its filename or
where it was dropped, so app.py can route an upload to the right pool
automatically. (Draft Sharks' League Analyzer — team-vs-team power
rankings, standings — is also league-specific but has no parser here yet;
it's detected and rejected with a clear message rather than silently
mis-parsed by the rankings parser.)

For matching purposes DataMerger.projections is the *merged* view: the
shared/global rankings pool plus the current league's own rankings files,
if any (a league-specific ranking file, should the user ever add one,
takes priority over the global pool for the same player). free_agents
comes only from the current league's own folder.

Both PDFs share a two-column page layout (a numbers column, then a names
column) which scrambles naive text-extraction order — both parsers
reconstruct rows on a *per-page* basis rather than assuming the whole
document reads top-to-bottom in one pass. CSV/JSON exports from other
vendors are still supported via the normal column-alias path.
"""

from __future__ import annotations

import difflib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECTIONS_DIR = Path("data/projections")
GLOBAL_PROJECTIONS_DIR = PROJECTIONS_DIR / "_global"  # Dynasty Rankings: format-based, shared across leagues
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
    """Lowercase, strip suffixes/punctuation so 'A.J. Brown Jr.' == 'aj brown'."""
    if not name:
        return ""
    name = name.lower()
    name = SUFFIXES.sub("", name)
    name = NON_ALNUM.sub("", name)
    return re.sub(r"\s+", " ", name).strip()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    for col in df.columns:
        key = str(col).strip().lower().replace(" ", "_")
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

    'rankings' -> format-based, shareable across leagues. 'free_agents' ->
    this-league-roster-specific. 'league_analyzer' -> also league-specific
    (team-vs-team power rankings/standings) but has no parser yet, so
    callers should reject it with a clear message rather than silently
    feeding it to the rankings parser, which would misread its text.
    """
    import pypdf

    try:
        reader = pypdf.PdfReader(str(path))
        text = (reader.pages[0].extract_text() or "") if reader.pages else ""
    except Exception:
        return "rankings"
    upper = text.upper()
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


def load_projection_file(path: Path) -> tuple[pd.DataFrame, str]:
    """Returns (dataframe, kind) where kind is 'rankings' or 'free_agents'."""
    suffix = path.suffix.lower()
    kind = "rankings"
    if suffix == ".csv":
        df = pd.read_csv(path)
        df = _normalize_columns(df)
        source_date = None
    elif suffix == ".json":
        df = pd.read_json(path)
        df = _normalize_columns(df)
        source_date = None
    elif suffix == ".pdf":
        kind = _sniff_pdf_kind(path)
        if kind == "league_analyzer":
            raise ValueError(f"{path.name} looks like a Draft Sharks League Analyzer export — not supported yet")
        parser = parse_draftsharks_free_agents_pdf if kind == "free_agents" else parse_draftsharks_pdf
        df, source_date = parser(path)
        if df.empty:
            raise ValueError(f"No table found in {path.name}")
    else:
        raise ValueError(f"Unsupported projection file type: {path.suffix}")

    df["source_file"] = path.name
    df["source_date"] = source_date or datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return df, kind


def load_all(projections_dir: Path = PROJECTIONS_DIR) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Parse every CSV/JSON/PDF once, bucketed into (rankings_df, free_agents_df)."""
    projections_dir = Path(projections_dir)
    empty = pd.DataFrame(columns=["name", "norm_name"])
    if not projections_dir.exists():
        return empty, empty.copy()

    files = sorted(
        [p for p in projections_dir.iterdir() if p.suffix.lower() in (".csv", ".json", ".pdf")],
        key=lambda p: p.stat().st_mtime,
    )
    rankings_frames, fa_frames = [], []
    for f in files:
        try:
            df, kind = load_projection_file(f)
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
        (fa_frames if kind == "free_agents" else rankings_frames).append(df)

    def _combine(frames: list[pd.DataFrame]) -> pd.DataFrame:
        if not frames:
            return empty.copy()
        combined = pd.concat(frames, ignore_index=True, sort=False)
        # across files (sorted oldest -> newest above), the newest file's row wins for a given player
        return combined.drop_duplicates(subset="norm_name", keep="last")

    return _combine(rankings_frames), _combine(fa_frames)


def _merge_rankings(*frames: pd.DataFrame) -> pd.DataFrame:
    """Combine rankings frames from multiple pools (e.g. global + league-specific).

    Frames passed later win ties for the same player — callers should pass
    the more-specific/more-authoritative source last (a league's own
    rankings override should beat the shared global pool for that player).
    """
    non_empty = [f for f in frames if not f.empty]
    if not non_empty:
        return pd.DataFrame(columns=["name", "norm_name"])
    combined = pd.concat(non_empty, ignore_index=True, sort=False)
    return combined.drop_duplicates(subset="norm_name", keep="last")


def _compute_freshness(df: pd.DataFrame) -> tuple[Optional[str], Optional[int], bool]:
    if df.empty or "source_date" not in df.columns:
        return None, None, False
    dates = pd.to_datetime(df["source_date"], errors="coerce").dropna()
    if dates.empty:
        return None, None, False
    freshest = dates.max().date().isoformat()
    days = (datetime.now().date() - datetime.fromisoformat(freshest).date()).days
    return freshest, days, days >= STALE_AFTER_DAYS


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

    Loads from two pools: a shared global pool (format-based Dynasty
    Rankings, same data correct for any league sharing that format) and, if
    league_dir is given, that one league's own folder (Free Agent Finder,
    always league-specific; a league-specific rankings override, if ever
    added, takes priority over the global pool for the same player).
    """

    def __init__(self, league_dir: Optional[Path] = None, global_dir: Path = GLOBAL_PROJECTIONS_DIR,
                 match_cutoff: float = 0.82):
        self.league_dir = Path(league_dir) if league_dir else None
        self.global_dir = Path(global_dir)
        self.match_cutoff = match_cutoff
        self._load()

    def _load(self) -> None:
        empty = pd.DataFrame(columns=["name", "norm_name"])
        global_rankings, _ = load_all(self.global_dir)
        if self.league_dir:
            league_rankings, league_fa = load_all(self.league_dir)
        else:
            league_rankings, league_fa = empty.copy(), empty.copy()
        self.projections = _merge_rankings(global_rankings, league_rankings)
        self.free_agents = league_fa
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
                       "source_file", "source_date"):
            if field in match.index and pd.notna(match[field]):
                row[field] = match[field]
        return row

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

            rows.append(row)
        return rows
