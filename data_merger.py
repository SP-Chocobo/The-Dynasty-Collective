"""
Draft Sharks / War Room projection parser and merger.

Reads locally-saved premium exports (Draft Sharks 3D projections, War Room
tiers, FantasyPros, Dynasty Process, etc.) from data/projections/ and
fuzzy-matches them onto Sleeper player records by name. Nothing here ever
calls out to a paid vendor's API — the files stay local, satisfying each
vendor's terms of service.

Draft Sharks doesn't currently offer a clean CSV export of its rankings —
what you actually get from the site is its rankings page printed to PDF.
That PDF has a two-column layout (a numbers column, then a names column)
which scrambles naive text-extraction order, so parse_draftsharks_pdf()
below reconstructs rows on a *per-page* basis rather than assuming the
whole document reads top-to-bottom in one pass. CSV/JSON exports from
other vendors are still supported via the normal column-alias path.
"""

from __future__ import annotations

import difflib
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECTIONS_DIR = Path("data/projections")
STALE_AFTER_DAYS = 7  # how old loaded projections can get before the UI nudges you to refresh

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


# -- Draft Sharks PDF rankings parsing ----------------------------------------

NFL_TEAM_CODES = (
    "ARI", "ATL", "BAL", "BUF", "CAR", "CHI", "CIN", "CLE", "DAL", "DEN", "DET",
    "GB", "HOU", "IND", "JAC", "KC", "LAC", "LAR", "LVR", "MIA", "MIN", "NE",
    "NO", "NYG", "NYJ", "PHI", "PIT", "SEA", "SF", "TB", "TEN", "UNS", "WAS",
)
# Draft Sharks' team codes vs. Sleeper's: JAC->JAX, LVR->LV, UNS (unsigned) -> FA.
TEAM_ALIASES = {"UNS": "FA", "JAC": "JAX", "LVR": "LV"}

_STAT_LINE_RE = re.compile(r"^(\d+) ([\d,]+) ([\d,]+) (\d+)$")
_TEAM_POS_RE = re.compile(rf"^({'|'.join(NFL_TEAM_CODES)})(QB|RB|WR|TE)(\d+)$")
_REVIEWED_DATE_RE = re.compile(r"Reviewed By[^|]*\|([A-Za-z]{3,9}\s+\d{1,2},\s+\d{4})")


def _extract_reviewed_date(full_text: str) -> Optional[str]:
    match = _REVIEWED_DATE_RE.search(full_text)
    if not match:
        return None
    try:
        return datetime.strptime(match.group(1), "%b %d, %Y").date().isoformat()
    except ValueError:
        return None


def parse_draftsharks_pdf(path: Path) -> tuple[pd.DataFrame, Optional[str]]:
    """Parse a Draft Sharks rankings page saved/printed as PDF.

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
            stat_match = _STAT_LINE_RE.match(line)
            if stat_match:
                rank, proj_1yr, proj_3yr, value_3d = stat_match.groups()
                stat_rows.append((int(rank), int(proj_1yr.replace(",", "")),
                                   int(proj_3yr.replace(",", "")), int(value_3d)))
                i += 1
                continue

            team_pos_match = _TEAM_POS_RE.match(line)
            if team_pos_match and name_rows and "team" not in name_rows[-1]:
                team, position, pos_rank = team_pos_match.groups()
                name_rows[-1].update(
                    team=TEAM_ALIASES.get(team, team), position=position, pos_rank=int(pos_rank)
                )
                i += 1
                continue

            # A name line is any line immediately followed by a TEAMPOSn line.
            if i + 1 < len(lines) and _TEAM_POS_RE.match(lines[i + 1]):
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


def load_projection_file(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        df = pd.read_csv(path)
        df = _normalize_columns(df)
        source_date = None
    elif suffix == ".json":
        df = pd.read_json(path)
        df = _normalize_columns(df)
        source_date = None
    elif suffix == ".pdf":
        df, source_date = parse_draftsharks_pdf(path)
        if df.empty:
            raise ValueError(f"No rankings table found in {path.name}")
    else:
        raise ValueError(f"Unsupported projection file type: {path.suffix}")

    df["source_file"] = path.name
    df["source_date"] = source_date or datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()
    return df


def load_all_projections(projections_dir: Path = PROJECTIONS_DIR) -> pd.DataFrame:
    """Concatenate every CSV/JSON/PDF in the projections folder, newest file wins ties."""
    projections_dir = Path(projections_dir)
    if not projections_dir.exists():
        return pd.DataFrame(columns=["name", "norm_name"])

    files = sorted(
        [p for p in projections_dir.iterdir() if p.suffix.lower() in (".csv", ".json", ".pdf")],
        key=lambda p: p.stat().st_mtime,
    )
    frames = []
    for f in files:
        try:
            df = load_projection_file(f)
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
        frames.append(df)

    if not frames:
        return pd.DataFrame(columns=["name", "norm_name"])

    combined = pd.concat(frames, ignore_index=True, sort=False)
    # across files (sorted oldest -> newest above), the newest file's row wins for a given player
    combined = combined.drop_duplicates(subset="norm_name", keep="last")
    return combined


class DataMerger:
    """Fuzzy-matches Sleeper player records onto locally loaded projection rows."""

    def __init__(self, projections_dir: Path = PROJECTIONS_DIR, match_cutoff: float = 0.82):
        self.projections_dir = Path(projections_dir)
        self.match_cutoff = match_cutoff
        self.projections = load_all_projections(self.projections_dir)

    def reload(self) -> None:
        self.projections = load_all_projections(self.projections_dir)

    @property
    def is_loaded(self) -> bool:
        return not self.projections.empty

    @property
    def freshest_date(self) -> Optional[str]:
        """Most recent source_date (ISO) across all loaded projection files."""
        if not self.is_loaded or "source_date" not in self.projections.columns:
            return None
        dates = pd.to_datetime(self.projections["source_date"], errors="coerce").dropna()
        return dates.max().date().isoformat() if not dates.empty else None

    @property
    def staleness_days(self) -> Optional[int]:
        freshest = self.freshest_date
        if not freshest:
            return None
        return (datetime.now().date() - datetime.fromisoformat(freshest).date()).days

    @property
    def is_stale(self) -> bool:
        days = self.staleness_days
        return days is not None and days >= STALE_AFTER_DAYS

    def _find_match(self, full_name: str, position: Optional[str] = None, team: Optional[str] = None) -> Optional[pd.Series]:
        """Match a Sleeper player onto a projections row.

        Draft Sharks' PDF rankings give first-initial-only names ("J Chase", not
        "Ja'Marr Chase"), which tanks a naive whole-string fuzzy ratio for anyone
        whose real first name is longer than one letter. So we first try an exact
        (first-initial, last-name) key match — robust to that abbreviation — and
        only fall back to fuzzy whole-string matching for vendors that do export
        full names. Team/position disambiguate when multiple players share a key.
        """
        if self.projections.empty or not full_name:
            return None
        norm_name = normalize_name(full_name)
        tokens = norm_name.split()
        if not tokens:
            return None
        key = (tokens[0][0], tokens[-1])

        def row_key(row_norm: str) -> tuple[str, str]:
            t = row_norm.split()
            return (t[0][0], t[-1]) if t else ("", "")

        key_matches = self.projections[self.projections["norm_name"].map(row_key) == key]
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

        choices = self.projections["norm_name"].tolist()
        candidates = difflib.get_close_matches(norm_name, choices, n=3, cutoff=self.match_cutoff)
        if not candidates:
            return None
        if position and "position" in self.projections.columns:
            for cand in candidates:
                rows = self.projections[self.projections["norm_name"] == cand]
                pos_match = rows[rows["position"] == position]
                if not pos_match.empty:
                    return pos_match.iloc[0]
        return self.projections[self.projections["norm_name"] == candidates[0]].iloc[0]

    def merge_player(self, player_full_name: str, position: Optional[str] = None, team: Optional[str] = None) -> dict:
        """Return DS fields (tier/vorp/projection/trade_value/rank/...) for one player, if matched."""
        match = self._find_match(player_full_name, position=position, team=team)
        if match is None:
            return {"matched": False}
        row = {"matched": True}
        for field in ("projection", "vorp", "tier", "trade_value", "rank",
                       "position", "team", "pos_rank", "proj_3yr", "source_file", "source_date"):
            if field in match.index and pd.notna(match[field]):
                row[field] = match[field]
        return row

    def build_roster_table(self, player_ids: list[str], players_db: dict[str, dict]) -> list[dict]:
        """Build one row per player id, joining Sleeper metadata with DS projections."""
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
            rows.append(row)
        return rows
