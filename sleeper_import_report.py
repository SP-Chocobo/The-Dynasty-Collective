"""What the Sleeper connection ACTUALLY brings in -- run on a machine that can reach the API.

WHY THIS EXISTS. Several open questions about this engine cannot be answered from the offline
harness, because the thing they ask about only arrives over the network. Each has been guessed at
more than once, and a guess about an input is exactly the kind of claim this project keeps having
to withdraw. So rather than reason about what Sleeper probably returns, this asks it.

    #88   the players payload is unavailable here, so its shape is assumed rather than known
    #172  eligibility_bonus and risk_adj are inert because injury_status never arrives -- but
          "never arrives from build_players_db" is not the same claim as "Sleeper does not send it"
    #142  age was measured once and deliberately left unwired; its real coverage is unrecorded
    #179  the RB aging penalty is a vendor number; age from Sleeper is the independent check
    #180  the offline path honours exactly two scoring keys. What does a REAL league carry?
    #178  the superflex share was derived on 1-SF leagues. Is this league 2QB or 2SF?
    ---   can the offence be priced from stats x scoring_settings, as IDP/K/DST already are?

WHAT IT DOES NOT DO. It does not change anything, does not write into data/, and does not send
anything anywhere. It reads, counts, and writes one report file you can look at before sharing.

PRIVACY. Identifiers are scrubbed by default: league name, user names, team names and ids are
replaced by stable short hashes, so the report describes SHAPE and COVERAGE without carrying who
you are or who you play with. Pass --raw if you want them, and read the file before sending it.

USAGE
    python3 sleeper_import_report.py --username YOUR_SLEEPER_NAME
    python3 sleeper_import_report.py --league-id 123456789012345678
    python3 sleeper_import_report.py --username NAME --raw --out my_report.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from typing import Any, Optional

FANTASY = ("QB", "RB", "WR", "TE", "K", "DEF", "DL", "LB", "DB")

#: The scoring keys the OFFLINE path can actually honour, and how. Everything else a league
#: carries is invisible to it -- that is #180, and this report exists partly to size it.
OFFLINE_SCORING_READS = {
    "rec": "bucketed to standard / half_ppr / ppr -- 2-PPR reads as 1-PPR",
    "bonus_rec_te": "read as a BOOLEAN -- a 0.5 and a 2.0 premium are the same to it",
}


def _short(value: Any) -> str:
    """A stable short hash, so two mentions of the same team match without naming it."""
    return "id:" + hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:8]


def _shape(sample: Any, scrub: bool, depth: int = 0) -> Any:
    """WHAT FORM the data actually arrives in -- field, type, and an example value.

    Coverage percentages say how OFTEN a field is there; they do not say what it looks like when
    it is. A field called `injury_status` could be a string, a null, an enum, or a nested object,
    and the difference decides whether it can be wired at all. So this walks one real record and
    reports the structure rather than describing it from memory.

    Example values are scrubbed for anything that reads like a name or an id, because the shape
    is the point and the person is not.
    """
    if depth > 3:
        return "..."
    if isinstance(sample, dict):
        return {k: _shape(v, scrub, depth + 1) for k, v in sorted(sample.items())}
    if isinstance(sample, (list, tuple)):
        if not sample:
            return "list[empty]"
        return [f"list[{len(sample)}] of", _shape(sample[0], scrub, depth + 1)]
    kind = type(sample).__name__
    if sample is None:
        return "None"
    if scrub and isinstance(sample, str) and len(sample) > 3 and not sample.isdigit():
        return f"{kind} e.g. {_short(sample)}"
    return f"{kind} e.g. {sample!r}"


def _field_types(rows, limit: int = 400) -> dict:
    """Every field seen across many records, with the SET of types it takes.

    A field carrying two types across records is a real hazard -- it is how `null` and `0.0`
    come to mean the same thing downstream -- so the set is reported, not the first type seen.
    """
    seen: dict = {}
    for row in list(rows)[:limit]:
        for k, v in (row or {}).items():
            seen.setdefault(k, set()).add(type(v).__name__)
    return {k: sorted(v) for k, v in sorted(seen.items())}


#: Fields whose VALUE DOMAIN is reported verbatim, never scrubbed. These are league-independent
#: NFL facts drawn from a small closed vocabulary -- "Questionable", "IR", "Active" -- so they
#: identify nobody, and hashing them would destroy the only thing worth knowing about them.
#: The scrubber exists to protect who you are and who you play with; applied here it would hide
#: the answer to the question the probe is asking.
VALUE_DOMAIN_FIELDS = ("injury_status", "status", "practice_participation")


def _value_domain(rows, field: str, limit: int = 25) -> dict:
    """WHAT a field actually says, not merely how often it says it.

    THE QUESTION THIS EXISTS TO SETTLE, and it is not a detail. `injury_status` present on 6.8%
    of WRs supports two OPPOSITE readings:
      (a) the field is populated ONLY for players carrying a designation, so ABSENCE MEANS
          HEALTHY -- the input is complete and risk_adj can be wired against it; or
      (b) the field is sparsely or unreliably populated, so ABSENCE MEANS UNKNOWN -- and
          treating a missing value as "healthy" would fabricate a clean bill of health for
          93.2% of receivers.
    A coverage percentage cannot distinguish those. The value domain can: if every present
    value is a real designation (Questionable / Doubtful / Out / IR / PUP / Sus / NA) and none
    of them means "healthy", reading (a) holds. If "Healthy" or "Active" appears among them,
    (b) does. Reporting `status` alongside is the cross-check -- a field that IS ~100% present
    and DOES carry Active/Inactive is the one that answers "is this player available at all",
    and its existence is what makes designation-only injury_status coherent.

    This is the failure the module's own _shape docstring already names -- a field could be a
    string, a null, an enum or a nested object, and the difference decides whether it can be
    wired at all -- and the first version of this report measured presence and never looked.
    """
    seen = collections.Counter()
    for row in rows:
        value = (row or {}).get(field, "__absent__")
        if value is None:
            seen["__explicit_null__"] += 1
        elif value == "__absent__":
            seen["__key_missing__"] += 1
        elif isinstance(value, (list, tuple)):
            seen[f"list{sorted(map(str, value))}"] += 1
        else:
            seen[str(value)] += 1
    return {
        "distinct_values": len(seen),
        "counts": dict(seen.most_common(limit)),
        "truncated": len(seen) > limit,
    }


def _coverage(rows, field: str, by: str = "position") -> dict:
    """Present / absent / blank, counted SEPARATELY per position.

    `is not None` and truthiness are different questions and this engine forbids conflating
    them, so a field that is present but empty is its own column rather than folded into
    missing."""
    out: dict[str, dict] = {}
    for row in rows:
        pos = (row or {}).get(by) or "UNKNOWN"
        slot = out.setdefault(pos, {"n": 0, "present": 0, "absent": 0, "blank": 0})
        slot["n"] += 1
        if field not in (row or {}):
            slot["absent"] += 1
        elif row.get(field) in (None, "", [], {}):
            slot["blank"] += 1
        else:
            slot["present"] += 1
    for slot in out.values():
        slot["present_pct"] = round(100.0 * slot["present"] / slot["n"], 1) if slot["n"] else None
    return dict(sorted(out.items()))


def _headshot_probe(client) -> dict:
    """Can we put a face in a player box? MEASURED, not remembered.

    The owner asked whether player photos are available to fill the player boxes. The URL
    pattern is a thing this codebase does not currently use anywhere -- no reference to
    sleepercdn exists in any shipping module -- so the honest answer is not a pattern recited
    from memory but an HTTP status from the real CDN. This fetches headers for a handful of
    real, currently-rostered-calibre players and reports what came back.

    ABSENCE, deliberately not flattened: "this player has no photo" and "the fetch failed" are
    different facts and are counted separately, exactly as _coverage does for data fields. A
    photo is also a weaker case than a VALUE -- a missing headshot may honestly fall back to a
    silhouette, because a silhouette asserts nothing about the player. That is not the same
    permission the absence contract withholds for a number, and this note exists so the
    distinction is not lost when someone wires this up.
    """
    import urllib.request

    db = client.get_players()
    offense = [(pid, r) for pid, r in db.items()
               if (r or {}).get("position") in ("QB", "RB", "WR", "TE")
               and (r or {}).get("team")]
    offense.sort(key=lambda kv: str(kv[0]))
    sample = offense[:4]
    if not sample:
        return {"checked": 0, "note": "no offensive player with a team in the payload"}

    found, missing, errored, results = 0, 0, 0, []
    for pid, row in sample:
        url = f"https://sleepercdn.com/content/nfl/players/{pid}.jpg"
        entry = {"position": (row or {}).get("position"), "url_pattern": url}
        try:
            req = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(req, timeout=10) as resp:
                entry.update(status=resp.status,
                             content_type=resp.headers.get("Content-Type"),
                             bytes=resp.headers.get("Content-Length"))
                if resp.status == 200:
                    found += 1
                else:
                    missing += 1
        except Exception as exc:                                # noqa: BLE001
            entry["error"] = f"{type(exc).__name__}: {exc}"
            errored += 1
        results.append(entry)

    return {
        "checked": len(sample),
        "headshot_returned_200": found,
        "no_headshot_for_that_player": missing,
        "fetch_errored": errored,          # NOT the same fact as "no headshot"
        "results": results,
        "verdict": ("player headshots ARE available at this pattern" if found
                    else "no headshot resolved -- do NOT wire photos on this evidence"),
    }


def _step(report: dict, name: str, fn):
    """Run one probe. A failure is RECORDED, never fatal -- a report that dies on its third
    endpoint tells you less than one that finishes and names what it could not reach."""
    try:
        report["probes"][name] = {"ok": True, "result": fn()}
    except Exception as exc:                                   # noqa: BLE001 -- reporting tool
        report["probes"][name] = {"ok": False,
                                  "error": f"{type(exc).__name__}: {exc}"}
    print(f"  {'ok  ' if report['probes'][name]['ok'] else 'FAIL'} {name}", flush=True)


def build_report(username: Optional[str], league_id: Optional[str], raw: bool) -> dict:
    from sleeper_client import SleeperClient, compute_points_from_stats

    client = SleeperClient()
    ident = (lambda v: v) if raw else _short
    report: dict = {"scrubbed": not raw, "probes": {}}

    # ---- 1. the players payload: the thing #88 blocks and #172/#142 depend on -------------
    def players():
        db = client.get_players()
        rows = list(db.values())
        offense = [r for r in rows if (r or {}).get("position") in ("QB", "RB", "WR", "TE")]
        keys = collections.Counter(k for r in rows for k in (r or {}))
        return {
            "total_players": len(rows),
            "cache_basis": client.players_cache_basis(),
            "every_field_seen": sorted(keys),
            "field_frequency_top40": dict(keys.most_common(40)),
            "age_coverage": _coverage(rows, "age"),
            "injury_status_coverage": _coverage(rows, "injury_status"),
            "years_exp_coverage": _coverage(rows, "years_exp"),
            "fantasy_positions_coverage": _coverage(rows, "fantasy_positions"),
            # WHAT the status fields actually say -- see _value_domain for why a coverage
            # percentage alone cannot tell "absent means healthy" from "absent means unknown".
            "VALUES_status_fields": {f: _value_domain(rows, f) for f in VALUE_DOMAIN_FIELDS},
            "VALUES_status_fields_offence_only": {
                f: _value_domain(offense, f) for f in VALUE_DOMAIN_FIELDS},
            "multi_position_players": sum(
                1 for r in rows if len((r or {}).get("fantasy_positions") or []) > 1),
            "offensive_players": len(offense),
            "FORM_one_offensive_record": _shape(offense[0], not raw) if offense else None,
            "FORM_field_types_across_400": _field_types(rows),
            "sample_offensive_row": (offense[0] if offense else None) if raw else
                                    sorted((offense[0] or {}).keys()) if offense else None,
        }
    _step(report, "players_nfl", players)

    # ---- 2. per-category STAT projections: can offence be priced like IDP already is? -----
    def projections():
        state = client.get_nfl_state() or {}
        season = str(state.get("season") or "")
        # A17: this used to read `int(state.get("week") or 1) or 1`, which invented week 1
        # whenever Sleeper reported none -- and then printed it as the week it had FETCHED.
        # A report whose whole job is "what actually arrived" must not fabricate its own
        # inputs. The doubled `or 1` also silently converted a real week 0 to 1.
        reported_week = state.get("week")
        week = int(reported_week) if reported_week is not None else None
        if week is None:
            raise ValueError("Sleeper reported no current week; refusing to invent one")
        proj = client.get_weekly_projections(season, week)
        rows = list(proj.values())
        cats = collections.Counter(c for r in rows for c in (r or {}))
        db = client.get_players()
        by_pos = collections.Counter()
        for pid in proj:
            by_pos[((db.get(str(pid)) or {}).get("position") or "UNKNOWN")] += 1
        return {
            "season": season, "week": week,
            "players_with_a_projection": len(rows),
            "players_by_position": dict(sorted(by_pos.items())),
            "stat_categories_seen": sorted(cats),
            "category_frequency_top40": dict(cats.most_common(40)),
            "FORM_one_projection_record": _shape(rows[0], not raw) if rows else None,
            "FORM_stat_types_across_400": _field_types(rows),
            "offence_has_per_category_stats": any(
                (db.get(str(pid)) or {}).get("position") in ("QB", "RB", "WR", "TE")
                for pid in proj),
        }
    _step(report, "weekly_projections", projections)

    # ---- 3. the league itself: scoring surface (#180) and roster shape (#178) -------------
    resolved: dict = {}
    def league():
        lid = league_id
        if not lid:  # noqa: SIM102 -- readability over nesting here
            if not username:
                raise ValueError("need --username or --league-id to read a league")
            user = client.get_user(username)
            if not user:
                raise ValueError(f"no Sleeper user named {username!r}")
            leagues = client.get_user_leagues(str(user.get("user_id"))) or []
            if not leagues:
                raise ValueError("that user has no leagues this season")
            lid = str(leagues[0].get("league_id"))
        resolved["league_id"] = lid      # the RAW id; the reported one is hashed unless --raw
        lg = client.get_league(lid) or {}
        scoring = lg.get("scoring_settings") or {}
        rpos = lg.get("roster_positions") or []
        unmodelled = {k: v for k, v in scoring.items()
                      if k not in OFFLINE_SCORING_READS and v}
        return {
            "league": ident(lid),
            "name": lg.get("name") if raw else ident(lg.get("name")),
            "num_teams": lg.get("total_rosters"),
            "roster_positions": rpos,
            "dedicated_QB_slots": rpos.count("QB"),
            "SUPER_FLEX_slots": rpos.count("SUPER_FLEX"),
            "outside_178_derivation": rpos.count("QB") > 1 or rpos.count("SUPER_FLEX") > 1,
            "scoring_settings": scoring,
            "scoring_keys_total": len(scoring),
            "scoring_keys_the_offline_path_reads": OFFLINE_SCORING_READS,
            "scoring_keys_it_CANNOT_honour": sorted(unmodelled),
            "unmodelled_count": len(unmodelled),
            "FORM_scoring_settings_types": {k: type(v).__name__ for k, v in sorted(scoring.items())},
            "FORM_league_record": _shape({k: v for k, v in lg.items()
                                          if k not in ("scoring_settings",)}, not raw),
        }
    _step(report, "league_config", league)

    # ---- 4. what arrives about the PEOPLE, and how much of it do we throw away? ----------
    def league_users():
        """Whether Sleeper sends profile imagery, and what this app currently does with it.

        Asked because the answer was about to be given from memory. `avatar` is known to arrive
        -- run_fixture_validation.py:30 already lists it among the fields safe to strip -- but
        "a field named avatar arrives" is not "we can render a photo", and the difference is a
        URL pattern nobody here has verified against the live CDN. So this fetches the candidate
        image and reports the HTTP status, rather than asserting the pattern is right.

        Absence is reported as absence: a user with no avatar set is counted separately from a
        user whose avatar failed to fetch. Those are different facts.
        """
        import urllib.request

        users = client.get_league_users(resolved["league_id"]) or []
        if not users:
            raise ValueError("no users returned for this league")

        fields = collections.Counter()
        for u in users:
            for k in (u or {}):
                fields[k] += 1
            for k in ((u or {}).get("metadata") or {}):
                fields[f"metadata.{k}"] += 1

        with_avatar = [u for u in users if (u or {}).get("avatar")]
        meta_avatar = [u for u in users if ((u or {}).get("metadata") or {}).get("avatar")]

        # MEASURE the URL pattern instead of remembering it.
        probes = []
        for u in with_avatar[:3]:
            aid = str(u.get("avatar"))
            for label, url in (("full", f"https://sleepercdn.com/avatars/{aid}"),
                               ("thumb", f"https://sleepercdn.com/avatars/thumbs/{aid}")):
                try:
                    req = urllib.request.Request(url, method="HEAD")
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        probes.append({"kind": label, "status": resp.status,
                                       "content_type": resp.headers.get("Content-Type"),
                                       "bytes": resp.headers.get("Content-Length")})
                except Exception as exc:                        # noqa: BLE001
                    probes.append({"kind": label, "error": f"{type(exc).__name__}: {exc}"})

        return {
            "users_in_league": len(users),
            "users_with_a_profile_avatar": len(with_avatar),
            "users_with_NO_avatar_set": len(users) - len(with_avatar),
            "users_with_a_custom_team_avatar": len(meta_avatar),
            "FORM_user_record": _shape(users[0], not raw),
            "fields_seen": dict(sorted(fields.items())),
            "avatar_url_probe": probes or "no user in this league has an avatar set",
            "player_headshots": _headshot_probe(client),
            # The gap this probe exists to size.
            "this_app_reads_only": ["display_name", "metadata.team_name"],
            "arrives_but_UNUSED": sorted(
                k for k in fields
                if k not in ("display_name", "metadata.team_name")
            ),
        }
    _step(report, "league_users", league_users)

    # ---- 5. does this league's OWN scoring change a real player's points? -----------------
    def scoring_effect():
        lg = report["probes"]["league_config"]["result"]
        proj = report["probes"]["weekly_projections"]["result"]
        if not lg.get("ok", True) or "scoring_settings" not in lg:
            raise ValueError("league_config did not resolve")
        state = client.get_nfl_state() or {}
        wk = state.get("week")                      # A17: never invented -- see probe 2
        if wk is None:
            raise ValueError("Sleeper reported no current week; refusing to invent one")
        raw_proj = client.get_weekly_projections(str(state.get("season") or ""), int(wk))
        db = client.get_players()
        mine = lg["scoring_settings"]
        plain = {"rec": mine.get("rec", 0), "bonus_rec_te": mine.get("bonus_rec_te", 0)}
        rows = []
        for pid, stats in list(raw_proj.items()):
            info = db.get(str(pid)) or {}
            if info.get("position") not in ("QB", "RB", "WR", "TE"):
                continue
            full = compute_points_from_stats(stats, mine)
            two = compute_points_from_stats(stats, plain)
            if full or two:
                rows.append({"pos": info.get("position"), "full": full, "two_keys_only": two,
                             "delta": round(full - two, 2)})
        rows.sort(key=lambda r: -abs(r["delta"]))
        changed = [r for r in rows if abs(r["delta"]) > 0.01]
        return {
            "scoreable_offensive_players": len(rows),
            "players_whose_points_change": len(changed),
            "pct_changed": round(100.0 * len(changed) / len(rows), 1) if rows else None,
            "largest_deltas_top10": rows[:10],
            "reading": ("the offline path's two keys reproduce this league's real scoring"
                        if not changed else
                        "this league carries scoring the offline path cannot express"),
        }
    _step(report, "scoring_effect", scoring_effect)

    return report


def render(report: dict) -> str:
    out = ["SLEEPER IMPORT REPORT", "=" * 60,
           f"identifiers scrubbed: {report.get('scrubbed')}", ""]
    for name, probe in report["probes"].items():
        out.append(f"[{'OK' if probe['ok'] else 'FAILED'}] {name}")
        if not probe["ok"]:
            out.append(f"    {probe['error']}")
            continue
        r = probe["result"]
        if name == "players_nfl":
            out.append(f"    players: {r['total_players']}  (cache basis: {r['cache_basis']})")
            for f in ("age", "injury_status", "years_exp"):
                cov = r[f"{f}_coverage"]
                shown = {k: v["present_pct"] for k, v in cov.items() if k in FANTASY}
                out.append(f"    {f} present %% by position: {shown}")
            out.append(f"    players with >1 fantasy position: {r['multi_position_players']}")
            for f in VALUE_DOMAIN_FIELDS:
                dom = (r.get("VALUES_status_fields") or {}).get(f)
                if not dom:
                    continue
                real = {k: v for k, v in dom["counts"].items()
                        if not k.startswith("__")}
                out.append(f"    {f} VALUES ({dom['distinct_values']} distinct): {real}")
        elif name == "weekly_projections":
            out.append(f"    season {r['season']} week {r['week']}: "
                       f"{r['players_with_a_projection']} projected")
            out.append(f"    offence has per-category stats: {r['offence_has_per_category_stats']}")
            out.append(f"    stat categories: {len(r['stat_categories_seen'])}")
        elif name == "league_config":
            out.append(f"    {r['num_teams']} teams, QB slots {r['dedicated_QB_slots']}, "
                       f"SUPER_FLEX {r['SUPER_FLEX_slots']}")
            out.append(f"    outside #178's derivation domain: {r['outside_178_derivation']}")
            out.append(f"    scoring keys: {r['scoring_keys_total']}, "
                       f"UNMODELLED by the offline path: {r['unmodelled_count']}")
            out.append(f"    unmodelled: {r['scoring_keys_it_CANNOT_honour']}")
        elif name == "league_users":
            out.append(f"    {r['users_in_league']} users; "
                       f"{r['users_with_a_profile_avatar']} have a profile avatar, "
                       f"{r['users_with_NO_avatar_set']} have none set")
            out.append(f"    custom team avatars: {r['users_with_a_custom_team_avatar']}")
            out.append(f"    avatar URL probe: {r['avatar_url_probe']}")
            _hs = r.get("player_headshots") or {}
            out.append(f"    player headshots: {_hs.get('headshot_returned_200', '?')} of "
                       f"{_hs.get('checked', '?')} checked returned 200 "
                       f"({_hs.get('fetch_errored', '?')} fetch errors) "
                       f"-> {_hs.get('verdict', 'not probed')}")
            out.append(f"    this app reads only: {r['this_app_reads_only']}")
            out.append(f"    arrives but UNUSED: {r['arrives_but_UNUSED']}")
        elif name == "scoring_effect":
            # A18: pct_changed is legitimately None when nothing was scoreable. The
            # producer honoured that and the renderer did not -- it printed "(None%)".
            _pct = r.get("pct_changed")
            _pct_txt = "not computable -- no scoreable player" if _pct is None else f"{_pct}%"
            out.append(f"    {r['players_whose_points_change']} of "
                       f"{r['scoreable_offensive_players']} offensive players change "
                       f"({_pct_txt})")
            out.append(f"    -> {r['reading']}")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--username")
    ap.add_argument("--league-id")
    ap.add_argument("--raw", action="store_true",
                    help="keep real names and ids (read the file before sharing it)")
    ap.add_argument("--out", default="sleeper_import_report.json")
    args = ap.parse_args()
    if not args.username and not args.league_id:
        ap.error("give --username or --league-id")

    print("probing Sleeper...", flush=True)
    report = build_report(args.username, args.league_id, args.raw)
    with open(args.out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, default=str)
    text = render(report)
    print("\n" + text)
    with open(args.out.replace(".json", ".txt"), "w", encoding="utf-8") as fh:
        fh.write(text)
    print(f"wrote {args.out} and {args.out.replace('.json', '.txt')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
