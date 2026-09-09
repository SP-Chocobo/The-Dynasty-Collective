"""Given the cancellation, WHERE does the level's basis actually change a price?

  slots all held : bpa + adj = (pts - L) + (L - displaced) = pts - displaced   -> L cancels
  a slot open    : adj = 0, so price = pts - L                                 -> L is the price

Measures both arms on real boards, and asks what actually wins the pick at the states where
the engine drafts tight ends. Run from the repo root with PYTHONPATH=.
"""
import json
import data_merger as dm, draft_room as dr, draft_battery as db, run_draft_battery as rdb

CAP = json.load(open("data/league_captures/fourth_and_forever.json")); RP = CAP["roster_positions"]
L = {"roster_positions": RP,
     "scoring_settings": {k: v["value"] for k, v in CAP["scoring_settings_observed"].items()},
     "total_rosters": 12, "settings": {"type": 2}}
D = json.load(open("evidence/roster_shape/ff_rulebook/ff_draft.json"))["picks"]
m = dm.DataMerger(); players_db, _ = rdb.build_players_db_from_capture()
m.set_league_format(db.league_format_hint(L)); season = rdb.season_projections_from_capture()
POS = ("QB", "RB", "WR", "TE")
def f(x):
    try: return float(x)
    except: return None

DA = {}
_da = dr.displacement_adjustments
def da_spy(rp, rpos, levels, unpriced=None):
    out = _da(rp, rpos, levels, unpriced)
    DA.clear(); DA["levels"] = dict(levels); DA["out"] = {k: dict(v) for k, v in out.items()}
    return out
dr.displacement_adjustments = da_spy

print("A) IS adj EXACTLY ZERO WHERE A SLOT IS OPEN? (then the level IS the price there)")
print(f"{'pick':>6}{'seat':>5}{'pos':>5}{'adj':>10}{'displaced':>11}{'level':>9}"
      f"{'basis':>16}{'zero?':>7}")
for AT, me in ((205, "12"), (241, "1"), (281, "8")):
    prior = [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:AT-1]]
    dr.compute_draft_board(m, players_db, prior, me, L, sleeper_projections=season,
                           sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    for p in POS:
        e = DA["out"].get(p)
        if not e: continue
        adj = f(e.get("adjustment")); lvl = DA["levels"].get(p)
        print(f"{AT:>6}{me:>5}{p:>5}{adj:>10.2f}"
              f"{(f(e.get('displaced')) or float('nan')):>11.2f}{lvl:>9.2f}"
              f"{str(e.get('basis'))[:15]:>16}{('YES' if adj == 0.0 else 'no'):>7}")
    print()

print("B) WHAT ACTUALLY WINS THE PICK where the engine takes tight ends")
print(f"{'pick':>6}{'seat':>5}{'chosen (real draft)':>22}{'top row on board':>20}"
      f"{'top bpa':>9}{'top adj':>9}{'top final':>11}{'TE best final':>15}")
for AT in (193, 205, 229, 241, 281):
    rec = D[AT-1]
    me = rec["roster_id"]
    prior = [{"player_id": q["player_id"], "roster_id": q["roster_id"]} for q in D[:AT-1]]
    rows = dr.compute_draft_board(m, players_db, prior, me, L, sleeper_projections=season,
                                  sleeper_basis=dr.SLEEPER_BASIS_SEASON_SUM)
    priced = [r for r in rows if f(r.get("final_score")) is not None]
    priced.sort(key=lambda r: -f(r["final_score"]))
    top = priced[0]
    te = next((r for r in priced if r["position"] == "TE"), None)
    print(f"{AT:>6}{me:>5}{(str(rec.get('position'))+' '+str(rec.get('name')))[:21]:>22}"
          f"{(top['position']+' '+str(top.get('name'))[:14])[:19]:>20}"
          f"{(f(top.get('bpa')) or 0):>9.2f}{(f(top.get('displacement_adj')) or 0):>9.2f}"
          f"{f(top['final_score']):>11.2f}"
          f"{(f(te['final_score']) if te else float('nan')):>15.2f}")
dr.displacement_adjustments = _da
