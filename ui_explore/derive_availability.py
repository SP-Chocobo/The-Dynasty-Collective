"""Derive the UI-exploration availability record (ui_explore/availability.json).

NOT AN ENGINE INPUT. These are disseminated FACTS with their denominators, for the draft
surface to render. Nothing here is a score, a rate or a risk: #294 measured that a durability
grade is not supportable from three seasons, so this file carries counts and nothing else.

ITS SOURCES ARE EXTERNAL FETCHES, so the suite cannot re-run it and no test asserts its output.
That is why the counting rules live HERE rather than only in the JSON they produced (#126):

    mkdir -p /tmp/ext && cd /tmp/ext
    for y in 2024 2025; do
      curl -LO https://github.com/nflverse/nflverse-data/releases/download/weekly_rosters/roster_weekly_$y.csv
      curl -LO https://github.com/nflverse/nflverse-data/releases/download/injuries/injuries_$y.csv
    done
    curl -LO https://raw.githubusercontent.com/dynastyprocess/data/master/files/db_playerids.csv
    python3 ui_explore/derive_availability.py /tmp/ext ui_explore/availability.json

WHAT A WEEK OFF DOES NOT INCLUDE, verified 2026-10-11 rather than assumed. A game he was PULLED
FROM -- hurt in the second quarter and not seen again -- counts as a week PLAYED, because all
three of this file's sources say he was available for it: the roster carries him ACT, the
official report cannot rule a man Out after kickoff, and the inactive list never named him. The
IR designation lands the week AFTER. Checked against five known mid-game injuries (Rice 2024 wk4
ACL, Godwin 2024 wk7 ankle, Chubb 2024 wk15 foot, Nabers and Hill 2025 wk4) -- every one reads
ACT in the week he was hurt, RES from the next.

Then checked at scale against nflverse releases/stats_player `stats_player_week_{y}.csv`, which
carries a row only where a player recorded a countable stat: of the 638 weeks this file counts as
MISSED across 185 board players, ZERO carry a stat line. So no week called missed was played.
The instrument is one-directional on purpose -- a missing row does not prove absence, since
active-but-statless is ordinary, but a PRESENT row does disprove a missed week.

The cost of that boundary, measured the same day and left unpriced: the week he was pulled from
counts in full. Taking each player-season's onset-adjacent week (the last he played before his
first missed week) against his own median volume that season, 26% of 144 fall below half and 10%
below a quarter -- Jalen Hurts' wk16 2024 concussion reads as a played week on 7 attempts against
a 37.5 median. It is NOT corrected here: nothing in these sources separates a mid-game exit from
a blowout benching or a game plan, and the correction would be a judgement wearing a count's
clothes. The record claims "weeks missed", never "weeks healthy", and the surface says so.
Where it could mislead, it is rare: of the 52 board players reading clean, exactly 2 hide a
truncated game while carrying a designation (Drake Maye 2024 wk18, AJ Barner 2025 wk10).
"""
import csv, json, collections, sys, datetime
ext, out = sys.argv[1], sys.argv[2]
SRC = {"roster_weekly": "github.com/nflverse/nflverse-data releases/weekly_rosters",
       "injuries":      "github.com/nflverse/nflverse-data releases/injuries",
       "id_map":        "raw.githubusercontent.com/dynastyprocess/data files/db_playerids.csv"}
#: Reasons the weekly report gives that are NOT injuries. LISTED, never derived as "contains
#: 'not injury'", for the reason player_universe.py lists GAME_TIME_CALL_DESIGNATIONS rather than
#: taking the complement: a reason nobody has ruled on must not fall out of the set by accident.
#: Counting these would re-introduce the exact conflation #294 spent its length removing -- a
#: healthy scratch is not an availability loss to his owner's roster in the sense meant here.
#: `illness` is deliberately NOT in this set: it is a real health absence that really cost weeks,
#: and excluding it would understate the record rather than clean it.
NON_INJURY_REASONS = {
    "not injury related - personal matter", "not injury related - other",
    "not injury related - coach's decision", "coaching decision",
    "coach's decision", "personal matter",
}
ids = {}
for r in csv.DictReader(open(f"{ext}/db_playerids.csv", newline="", encoding="utf-8", errors="replace")):
    s, g = (r.get("sleeper_id") or "").strip(), (r.get("gsis_id") or "").strip()
    if s and g: ids[s] = g

def season(y):
    """Per-WEEK facts for one season. Counters are deliberately not returned.

    A week is MISSED when the roster says injured reserve, when the official report ruled him
    Out or Doubtful, or when he was declared INACTIVE and the report listed an injury for him
    that same week. Returning a SET of week numbers rather than three counters makes
    double-counting impossible by construction: a week that is both inactive and ruled Out is
    one missed week, and summing the three sources charged it twice -- which inflated 100 of
    180 players before it was caught, without moving the membership that made it visible.

    `INA` alone is never enough -- it is also the healthy scratch, and counting it blind
    re-creates the conflation #294 removed. The designation for THAT week is the separator.

    The bye week is absent from the roster file, so `of` counts GAME weeks, not calendar weeks.
    """
    rost, wk = collections.defaultdict(dict), collections.defaultdict(set)
    for r in csv.DictReader(open(f"{ext}/roster_weekly_{y}.csv", newline="", encoding="utf-8", errors="replace")):
        s_ = (r.get("sleeper_id") or "").strip()
        if not s_: continue
        w = int(r["week"])
        if w > 18: continue
        wk[s_].add(w); rost[s_][w] = r.get("status", "")
    des = collections.defaultdict(dict)          # gsis -> week -> (status, part)
    for r in csv.DictReader(open(f"{ext}/injuries_{y}.csv", newline="", encoding="utf-8", errors="replace")):
        if r.get("game_type") != "REG": continue
        st = (r.get("report_status") or "").strip()
        bp = (r.get("report_primary_injury") or "").strip().lower()
        if not st or bp in NON_INJURY_REASONS: continue
        des[r["gsis_id"]][int(r["week"])] = (st, bp)
    return rost, {k: len(v) for k, v in wk.items()}, des


# COMPLETED seasons only. The in-progress season is a PRESENT fact (the live designation the
# card already renders), not a historical rate -- #294, and the owner's own summer-to-heal point.
YEARS = [2025, 2024]
S = {y: season(y) for y in YEARS}
board = {}
fx = json.loads(open("ui_explore/fixture.json").read())
for fmt, arm in fx.items():
    for st, s in arm["states"].items():
        for c in s.get("candidates", []): board[c["player_id"]] = (c["name"], c["position"])

rec = {}
for pid, (nm, pos) in board.items():
    if pos in ("DEF", "K"):          # a team unit has no individual record; a kicker's is inert
        continue
    g = ids.get(pid); seasons = []
    for y in YEARS:
        rost, wkn, des = S[y]
        poss = wkn.get(pid, 0)
        if not poss: continue
        mine, dd = rost.get(pid, {}), (des.get(g, {}) if g else {})
        missed_wks, ir_wks = set(), set()
        for w, status in mine.items():
            if status == "RES":
                missed_wks.add(w); ir_wks.add(w)                      # on IR: off the report
            elif w in dd and (dd[w][0] in ("Out", "Doubtful") or status == "INA"):
                missed_wks.add(w)          # ruled out, or inactive WITH an injury that week
        # The parts are the reasons given FOR THE WEEKS HE MISSED -- not every designation he
        # carried. A Questionable week he played is not a reason he was absent, and listing it
        # made "1 of 17 missed · ankle, quadricep" claim two injuries for one missing week.
        cnt = collections.Counter(dd[w][1] for w in missed_wks if w in dd and dd[w][1])
        for k in [k for k in list(cnt) if k.endswith("s") and k[:-1] in cnt]:
            cnt[k[:-1]] += cnt.pop(k)      # the source lists "rib" beside "ribs" in one record
        seasons.append({"y": y, "missed": len(missed_wks), "of": poss, "ir": len(ir_wks),
                        "parts": [k for k, _ in sorted(cnt.items(), key=lambda kv: (-kv[1], kv[0]))]})
    # THE STRUCTURAL GATE (#294): a record needs a COMPLETED prior season. Without one the
    # figure would read as a confident 100% off a few weeks -- every true rookie did.
    rec[pid] = {"seasons": seasons} if seasons else {"seasons": [], "absent": "no completed NFL season"}
payload = {"_what": "UI-exploration availability RECORD. Counts with denominators, never a grade.",
           "_not": "Not an engine input, not a risk score, not priced. See #294.",
           "_captured": datetime.date.today().isoformat(), "_sources": SRC,
           "_seasons": YEARS, "_excluded": "DEF (team unit) and K (record inert)",
           "players": rec}
open(out, "w").write(json.dumps(payload, separators=(",", ":")))
n = sum(1 for v in rec.values() if v["seasons"])
miss = sum(1 for v in rec.values() if v["seasons"] and any(s["missed"] for s in v["seasons"]))
print(f"{len(rec)} players · {n} with a completed-season record · {len(rec)-n} render as absence")
print(f"{miss} carry missed time; {n-miss} are clean")
