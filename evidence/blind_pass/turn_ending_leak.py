"""Are TURN-ENDING picks where the ordering repair still fails? (#17)

At a turn-ending pick -- the last of a round in a snake, where the same seat picks again
immediately -- there are no intervening picks, so positional_forfeits correctly returns nothing
and acting_now_value is absent. Those rows fall into _acting_now_order's unmeasured block and
are ranked by team_acquisition_value: the exact order this repair replaced.

That is the absence contract behaving, not a bug. The OPEN QUESTION (#17) is whether those picks
should instead weigh deferral to the round AFTER next -- a different quantity, and an engine
change. What the ruling needs is evidence that the gap MATTERS, and the specific worry is
concrete: the first defense of the whole draft landed at 7.12, a turn-ending pick.

So: do K and DEF cluster on turn-ending picks relative to their share of all picks?

Run from the REPO ROOT.
"""
import sys; sys.path.insert(0, "/home/user/The-Dynasty-Collective")
import json, collections
import run_draft_battery as rdb, player_universe as pu

SC = "/tmp/claude-0/-home-user-The-Dynasty-Collective/90289f87-1d2a-5009-8163-038c3cedfc5f/scratchpad/"
players_db, _ = rdb.build_players_db_from_capture()
pos_of = lambda pid: pu.player_position(players_db.get(str(pid)) or {}) or "?"

for arm, label in (("traj_treatment.json", "acting_now ordering"),):
    picks = json.load(open(SC + arm))
    # A pick is TURN-ENDING when the same roster holds the very next pick.
    seats = [str(p["roster_id"]) for p in picks]
    ending = [i for i in range(len(picks) - 1) if seats[i] == seats[i + 1]]
    ending_set = set(ending)
    print("=== %s ===" % label)
    print("  picks: %d   turn-ending: %d (%.1f%%)\n" % (
        len(picks), len(ending), 100 * len(ending) / len(picks)))

    all_pos = collections.Counter(pos_of(p["chosen"]) for p in picks)
    end_pos = collections.Counter(pos_of(picks[i]["chosen"]) for i in ending)
    print("  %-6s%12s%14s%14s%12s" % ("pos", "all picks", "turn-ending", "expected", "ratio"))
    for pos in ("RB", "WR", "TE", "QB", "K", "DEF"):
        n_all = all_pos.get(pos, 0)
        n_end = end_pos.get(pos, 0)
        expected = n_all * len(ending) / len(picks)
        ratio = (n_end / expected) if expected else float("nan")
        flag = "   <-- clustered" if ratio >= 2.0 and n_end >= 2 else ""
        print("  %-6s%12d%14d%14.2f%12.2f%s" % (pos, n_all, n_end, expected, ratio, flag))

    print("\n  === the specific worry: where did K and DEF go FIRST? ===")
    for pos in ("DEF", "K"):
        first = next((i for i, p in enumerate(picks) if pos_of(p["chosen"]) == pos), None)
        if first is None:
            continue
        print("    %-4s first taken at %-7s round %-3d  turn-ending: %s"
              % (pos, picks[first]["pick_label"], picks[first]["round"],
                 "YES" if first in ending_set else "no"))
        early = [i for i, p in enumerate(picks)
                 if pos_of(p["chosen"]) == pos and p["round"] <= 12]
        if early:
            n_end_early = sum(1 for i in early if i in ending_set)
            print("         taken by round 12: %d, of which turn-ending: %d (%.0f%%)"
                  % (len(early), n_end_early, 100 * n_end_early / len(early)))
