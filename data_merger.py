"""
Draft Sharks / War Room projection parser and merger.

Reads locally-saved premium CSV/JSON exports (Draft Sharks 3D projections,
War Room tiers, FantasyPros, Dynasty Process, etc.) from data/projections/
and fuzzy-matches them onto Sleeper player records by name. Nothing here
ever calls out to a paid vendor's API — the files stay local, satisfying
each vendor's terms of service.
"""

from __future__ import annotations

import difflib
import re
from pathlib import Path
from typing import Optional

import pandas as pd

PROJECTIONS_DIR = Path("data/projections")

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


def load_projection_file(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path)
    elif path.suffix.lower() == ".json":
        df = pd.read_json(path)
    else:
        raise ValueError(f"Unsupported projection file type: {path.suffix}")
    df = _normalize_columns(df)
    df["source_file"] = path.name
    return df


def load_all_projections(projections_dir: Path = PROJECTIONS_DIR) -> pd.DataFrame:
    """Concatenate every CSV/JSON in the projections folder, newest file wins ties."""
    projections_dir = Path(projections_dir)
    if not projections_dir.exists():
        return pd.DataFrame(columns=["name", "norm_name"])

    files = sorted(
        [p for p in projections_dir.iterdir() if p.suffix.lower() in (".csv", ".json")],
        key=lambda p: p.stat().st_mtime,
    )
    frames = []
    for f in files:
        try:
            frames.append(load_projection_file(f))
        except Exception:
            continue  # skip unparsable/misformatted files rather than crashing the app

    if not frames:
        return pd.DataFrame(columns=["name", "norm_name"])

    combined = pd.concat(frames, ignore_index=True, sort=False)
    # keep the row from the most-recently-modified file for each player
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

    def _find_match(self, norm_name: str) -> Optional[pd.Series]:
        if self.projections.empty or not norm_name:
            return None
        choices = self.projections["norm_name"].tolist()
        matches = difflib.get_close_matches(norm_name, choices, n=1, cutoff=self.match_cutoff)
        if not matches:
            return None
        return self.projections[self.projections["norm_name"] == matches[0]].iloc[0]

    def merge_player(self, player_full_name: str) -> dict:
        """Return DS fields (tier/vorp/projection/trade_value/rank) for one player, if matched."""
        match = self._find_match(normalize_name(player_full_name))
        if match is None:
            return {"matched": False}
        row = {"matched": True}
        for field in ("projection", "vorp", "tier", "trade_value", "rank", "position", "team", "source_file"):
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
            row = {
                "player_id": pid,
                "name": full_name,
                "position": info.get("position", "?"),
                "team": info.get("team") or "FA",
                "injury_status": info.get("injury_status"),
            }
            row.update(self.merge_player(full_name))
            rows.append(row)
        return rows
