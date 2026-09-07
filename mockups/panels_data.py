"""The panel group's payload: the four stores in their OWN shapes, constructed because every one
of them is empty in this tree (data/decisions and data/todos hold only lock files, data/pins
does not exist, data/baseline has no bot_research.json or bot_comparisons.json). Nothing here
is a claim about any league; it is the contract's fixture, and every page says so.

What is the app's and not mine:
  - the decision rows' verdict fields come from llm_engine.parse_moderator_verdict run over the
    Moderator texts in dock_data (the same constructed transcript the Debate Dock used), and
    the objective revision from parse_todo_directives -- so the rows are what
    app.process_moderator_output would have written, field for field;
  - every finding's cited_source_admitted / adjudication / composite_impact triple comes from
    bot_research.composite_eligibility, so the eligibility strings are the store's own;
  - the record shapes are decision_log.log_decision's, todo_log.add_todo's, bot_research's
    add_finding / add_comparison's, and pinned_messages' (a sorted list of message timestamps).

What each store is made to exercise, because a panel that only ever sees the happy row has
never been designed:
  DECISIONS  six rows: one whose block carried no RECOMMENDATION line (parse is per-field, and
             log_decision records any block with at least one field), one written before
             provider/model were recorded, three rated (Worked / Didn't Work / Mixed) and two
             not, and a same-day RE-RUN of the same question (a second /debate on the 3.03
             question two minutes after the first), which the store does not dedupe.
  OBJECTIVES seven: three active from Moderator ACTION ITEMs (one revised by a TODO UPDATE and
             referenced since, one with a user note), one the user added by hand and a bot has
             proposed as likely resolved (pending), one resolved with a real note, one resolved
             with the default reason, one dismissed.
  PINS       three timestamps: the first verdict (1,334 chars; its block starts at char 609),
             the first Quant report, and one whose message is NOT in the chat history -- a pin
             that survived a compaction its message did not.
  FINDINGS   six, one per reason a number does or does not count: panel-only on an admitted
             source (awaiting confirmation); a rank from a source not on the allowlist; a
             qualitative claim with no rank; a human-confirmed one that feeds the composite;
             one confirmed then retracted; and a legacy row with no adjudication key and no
             evidence block (never checked, as distinct from checked and absent).
  COMPARISONS two, one from a superflex league and one from a 1QB league, since the store is
             global and the rows say which league asked.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import bot_research  # noqa: E402
import llm_engine  # noqa: E402
import dock_data  # noqa: E402

LEAGUE_ID = "panelprobe"
T0 = dock_data.T0  # 2025-09-06 00:00 UTC
DAY = 86400.0
H = 3600.0

# The transcript is dock_data's; the message timestamps below are its own.
HISTORY = dock_data.transcript()
TS_MOD_1 = next(m["ts"] for m in HISTORY if m["role"] == "moderator")
TS_QUANT_1 = next(m["ts"] for m in HISTORY if m["role"] == "quant")
TS_MOD_2 = [m["ts"] for m in HISTORY if m["role"] == "moderator"][-1]


def _date(ts: float) -> str:
    import datetime as _dt
    return _dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")


def _decision(ts: float, question: str, moderator_text: str, provider: str = "", model: str = "",
              outcome: str = "", outcome_note: str = "", outcome_ts: float | None = None) -> dict:
    """Exactly decision_log.log_decision's row, with the verdict fields from the app's parser."""
    v = llm_engine.parse_moderator_verdict(moderator_text)
    return {
        "ts": ts, "date": _date(ts), "question": question,
        "recommendation": v.get("recommendation", ""), "conviction": v.get("conviction", ""),
        "reason": v.get("reason", ""), "dissent": v.get("dissent", ""), "risk": v.get("risk", ""),
        "recon": v.get("recon", ""), "price_ceiling": v.get("price_ceiling", ""),
        "alternative": v.get("alternative", ""), "moderator_text": moderator_text,
        "provider": provider, "model": model,
        "outcome": outcome, "outcome_note": outcome_note,
        "outcome_date": _date(outcome_ts) if outcome_ts else None,
    }


# A block whose RECOMMENDATION line the model wrote without the colon -- parse_moderator_verdict
# is per-field, so the row is logged with a blank recommendation and the rest intact.
MOD_NO_REC = """Start Nacua over Adams this week: the target share is 31% to 22% and the Rams' opponent funnels to the slot.

RECOMMENDATION - START NACUA
CONVICTION: Unanimous
REASON: 31% target share against a defense allowing the most slot receptions in the league
RISK: Nacua's knee was listed limited on Wednesday; if he sits, Adams is the start by default"""

MOD_HOLD = """Hold Achane. The 2027 1st on offer is a contender's pick and prices at the back of the round; the Quant's number says you are selling 6,410 of value for 5,900, and the Beat has no news that changes his workload. The Contrarian's workload point is the reason this is Majority.

RECOMMENDATION: HOLD
CONVICTION: Majority
REASON: 6,410 for 5,900 as offered; a contender's 2027 1st prices at the back of the round
DISSENT: Contrarian — the health discount is real and a rebuild should sell the assumption of health while the market still pays for it
RISK: An injury before a better offer arrives; the 6,410 is a health number
ACTION ITEM: Check with Roster 6 whether their 2027 1st is available"""

MOD_TAXI = """Promote Shough to the active roster and drop Rattler; the taxi slot is worth more to a rookie WR than a QB2 you are now starting in superflex.

RECOMMENDATION: BUY
CONVICTION: Unanimous
REASON: The superflex slot is live starter demand and the taxi squad exists for players you are not starting
RISK: Rattler clears waivers to a contender who needed a QB2; small, and the Beat found no roster that does"""

# The 3.03 question, re-run two minutes after the first verdict -- the store keeps both rows.
MOD_1_RERUN = dock_data.MOD_1.replace("DISSENT: Contrarian", "DISSENT: Contrarian")  # identical block

DECISIONS: list[dict] = [
    _decision(T0 - 22 * DAY + 9 * H, "Nacua or Adams at WR2 this week?", MOD_NO_REC,
              outcome="Mixed", outcome_note="Nacua 14.2, Adams 13.9 -- both started in the end via flex.", outcome_ts=T0 - 17 * DAY),
    _decision(T0 - 15 * DAY + 11 * H, "Roster 6 wants Achane for their 2027 1st. Hold or sell?", MOD_HOLD,
              outcome="Didn't Work", outcome_note="Achane tweaked the hamstring 09-01; the same offer came back 400 lower.", outcome_ts=T0 - 4 * DAY),
    _decision(T0 - 7 * DAY + 8 * H, "Promote Shough from taxi or keep the slot?", MOD_TAXI,
              provider="claude", model="claude-opus-4-1",
              outcome="Worked", outcome_note="", outcome_ts=T0 - 2 * DAY),
    _decision(TS_MOD_1, dock_data.Q1, dock_data.MOD_1, provider="claude", model="claude-opus-4-1"),
    _decision(TS_MOD_1 + 125, dock_data.Q1, MOD_1_RERUN, provider="claude", model="claude-opus-4-1"),
    _decision(TS_MOD_2, dock_data.Q3, dock_data.MOD_2, provider="claude", model="claude-opus-4-1"),
]

# Objectives, in todo_log.add_todo's shape; ids are the store's own small integers.
_update = llm_engine.parse_todo_directives(dock_data.MOD_2)["updates"][0]
TODOS: list[dict] = [
    {"id": 1, "ts": T0 - 15 * DAY + 11 * H + 2, "date": _date(T0 - 15 * DAY), "text": _update["text"],
     "source": "moderator", "question": "Roster 6 wants Achane for their 2027 1st. Hold or sell?", "decision_ts": None,
     "status": "active", "resolution_reason": "", "resolution_date": None,
     "revisions": [{"ts": TS_MOD_2 + 1, "date": _date(TS_MOD_2), "text": "Check with Roster 6 whether their 2027 1st is available", "reason": _update["reason"]}],
     "notes": [{"ts": T0 - 10 * DAY, "date": _date(T0 - 10 * DAY), "text": "Messaged Roster 6 on 08-27; no answer yet."}],
     "proposals": [], "last_referenced": _date(TS_MOD_2)},
    {"id": 2, "ts": TS_MOD_1 + 1, "date": _date(TS_MOD_1), "text": llm_engine.parse_moderator_verdict(dock_data.MOD_1)["action_item"],
     "source": "moderator", "question": dock_data.Q1, "decision_ts": None, "status": "active",
     "resolution_reason": "", "resolution_date": None, "revisions": [], "notes": [], "proposals": []},
    {"id": 3, "ts": TS_MOD_2 + 1, "date": _date(TS_MOD_2), "text": llm_engine.parse_moderator_verdict(dock_data.MOD_2)["action_item"],
     "source": "moderator", "question": dock_data.Q3, "decision_ts": None, "status": "active",
     "resolution_reason": "", "resolution_date": None, "revisions": [], "notes": [], "proposals": []},
    {"id": 4, "ts": T0 - 12 * DAY, "date": _date(T0 - 12 * DAY), "text": "Find a taxi-squad rookie WR to stash before the trade deadline",
     "source": "manual", "question": "", "decision_ts": None, "status": "likely_resolved",
     "resolution_reason": "The roster data shows a rookie WR added to the taxi squad on 09-04.",
     "resolution_date": None, "revisions": [], "notes": [],
     "proposals": [{"ts": T0 - 1 * DAY, "date": _date(T0 - 1 * DAY), "reason": "The roster data shows a rookie WR added to the taxi squad on 09-04.", "outcome": "pending"}]},
    {"id": 5, "ts": T0 - 22 * DAY + 9 * H + 2, "date": _date(T0 - 22 * DAY), "text": "Confirm Nacua's knee status before Sunday's lock",
     "source": "moderator", "question": "Nacua or Adams at WR2 this week?", "decision_ts": None, "status": "resolved",
     "resolution_reason": "Full participant Friday; started him.", "resolution_date": _date(T0 - 19 * DAY),
     "revisions": [], "notes": [],
     "proposals": [{"ts": T0 - 19 * DAY, "date": _date(T0 - 19 * DAY), "reason": "The Beat reported him a full participant Friday.", "outcome": "accepted", "closed_date": _date(T0 - 19 * DAY)}]},
    {"id": 6, "ts": T0 - 30 * DAY, "date": _date(T0 - 30 * DAY), "text": "Offer Roster 11 a 2026 2nd for their backup TE",
     "source": "manual", "question": "", "decision_ts": None, "status": "dismissed",
     "resolution_reason": "Dismissed by user", "resolution_date": _date(T0 - 25 * DAY),
     "revisions": [], "notes": [], "proposals": []},
    {"id": 7, "ts": T0 - 9 * DAY, "date": _date(T0 - 9 * DAY), "text": "Set the Week 1 lineup before Thursday night",
     "source": "manual", "question": "", "decision_ts": None, "status": "resolved",
     "resolution_reason": "Marked done by user", "resolution_date": _date(T0 - 3 * DAY),
     "revisions": [], "notes": [], "proposals": []},
]

#: The pin store is a sorted list of message timestamps. The third is an ORPHAN: no message in
#: HISTORY carries it (its message was older than a compaction cutoff and was summarised away;
#: app.compact_chat_history does not consult the pin store).
PINNED_TS: list[float] = sorted([TS_MOD_1, TS_QUANT_1, T0 - 40 * DAY + 3 * H])


def _finding(fid: int, ts: float, player: str, source: str, claim: str, rank, adjudication, *,
             retracted: dict | None = None, legacy: bool = False, conviction: str = "", question: str = "",
             league_id: str | None = LEAGUE_ID, sources: int = 0, confirmed: tuple[str, str] | None = None) -> dict:
    row = {"id": fid, "ts": ts, "date": _date(ts), "player_name": player, "source": source, "claim": claim, "rank": rank}
    if legacy:
        # A row written before the gate and the evidence snapshot existed: no adjudication key,
        # no evidence key. composite_impact as the old code wrote it.
        row.update({"composite_impact": "low-weight input" if rank is not None else "none", "conviction": conviction,
                    "question": question, "league_id": league_id})
        return row
    row.update(bot_research.composite_eligibility(source, rank, adjudication, retracted))
    row.update({"conviction": conviction, "question": question, "league_id": league_id,
                "evidence": {"origin": bot_research.ORIGIN_PANEL_RETRIEVED if sources else bot_research.ORIGIN_UNATTRIBUTED,
                             "retrieved_at": _date(ts),
                             "debate_sources": [{"url": f"https://example.invalid/{i}", "title": f"page {i}"} for i in range(sources)]}})
    if confirmed:
        row["confirmed_by"], row["confirmed_at"] = confirmed
    if retracted:
        row["retracted"] = retracted
    return row


_f1 = llm_engine.parse_source_findings(dock_data.MOD_1)[0]
FINDINGS: list[dict] = [
    _finding(1, T0 - 40 * DAY, "Josh Allen", "ESPN", "Ranked the overall QB1 in dynasty for 2025", 1, None, legacy=True,
             conviction="Unanimous", question="Is Allen worth a first?"),
    _finding(2, T0 - 22 * DAY + 9 * H, "Puka Nacua", "ESPN", "Top-five WR in target share through the preseason", 4,
             bot_research.ADJUDICATION_HUMAN_CONFIRMED, conviction="Unanimous", question="Nacua or Adams at WR2 this week?",
             sources=3, confirmed=("human", _date(T0 - 20 * DAY))),
    _finding(3, T0 - 15 * DAY + 11 * H, "De'Von Achane", "FantasyCalc", "Priced as an RB1 in superflex dynasty", 7,
             bot_research.ADJUDICATION_PANEL_ONLY, conviction="Majority", question="Roster 6 wants Achane for their 2027 1st. Hold or sell?", sources=2),
    _finding(4, T0 - 15 * DAY + 11 * H + 1, "Kyren Williams", "ESPN", "Expected to cede early-down work to the rookie after the bye", None,
             bot_research.ADJUDICATION_PANEL_ONLY, conviction="Majority", question="Roster 6 wants Achane for their 2027 1st. Hold or sell?", sources=2),
    _finding(5, T0 - 7 * DAY + 8 * H, "Spencer Rattler", "KTC", "Ranked QB31 in superflex dynasty", 31,
             bot_research.ADJUDICATION_HUMAN_CONFIRMED, conviction="Unanimous", question="Promote Shough from taxi or keep the slot?",
             sources=0, confirmed=("human", _date(T0 - 6 * DAY)),
             retracted={"reason": bot_research.RETRACTED_REJECTED, "by": "human", "at": _date(T0 - 2 * DAY),
                        "note": "KTC had him QB38 when I looked; the panel misread a 1QB list."}),
    _finding(6, TS_MOD_1, _f1["player_name"], _f1["source"], _f1["claim"], _f1["rank"],
             bot_research.ADJUDICATION_PANEL_ONLY, conviction="Majority", question=dock_data.Q1, sources=4),
]

COMPARISONS: list[dict] = [
    {"id": 1, "ts": TS_MOD_1 + 2, "date": _date(TS_MOD_1), "subject": "Tyler Shough", "compared_to": "Matthew Stafford",
     "direction": ">", "source": "KTC", "context": "superflex dynasty", "evidence": "market values the four-year window over the 2025 offense",
     "evidence_type": "qualitative comparative", "panel_undisputed": True, "composite_impact": "none",
     "question": dock_data.Q1, "league_id": LEAGUE_ID},
    {"id": 2, "ts": T0 - 33 * DAY, "date": _date(T0 - 33 * DAY), "subject": "Brock Bowers", "compared_to": "Trey McBride",
     "direction": "~", "source": "ESPN", "context": "1QB, TE premium", "evidence": "back-to-back at TE1/TE2 with the order flipping week to week",
     "evidence_type": "qualitative comparative", "panel_undisputed": True, "composite_impact": "none",
     "question": "Bowers or McBride at 1.11?", "league_id": "otherleague"},
]

#: A minimal league snapshot in sleeper_client.sync_league's shape, enough for app.py's header
#: and the Import Audit view. Every list empty: no roster is claimed.
SNAPSHOT = {
    "synced_at": T0 + 25 * H, "league": {
        "league_id": LEAGUE_ID, "name": "Gold Wyrm Dynasty", "season": "2025", "total_rosters": 12,
        "settings": {"type": 2, "num_teams": 12, "taxi_slots": 4},
        "scoring_settings": {"rec": 1.0, "pass_td": 6, "pass_int": -2},
        "roster_positions": ["QB", "RB", "RB", "WR", "WR", "TE", "FLEX", "SUPER_FLEX", "K", "DEF", "BN", "BN", "BN", "BN", "BN", "BN"],
    }, "rosters": [], "users": [], "traded_picks": [], "nfl_state": {"season": "2025", "week": 1},
    "projection_request": {}, "projection_attempts": [], "projections": {}, "matchups": [],
}


def payload() -> dict:
    return {
        "league": {"id": LEAGUE_ID, "name": "Gold Wyrm Dynasty", "format": "12-team · Superflex · Dynasty"},
        "history": HISTORY, "decisions": DECISIONS, "todos": TODOS, "pinned": PINNED_TS,
        "findings": FINDINGS, "comparisons": COMPARISONS,
        "roleNames": {"quant": "Quant", "beat": "Beat Tracker", "contrarian": "Contrarian", "moderator": "Moderator"},
        "outcomeLabels": list(__import__("decision_log").OUTCOME_LABELS),
        "verdictFields": llm_engine.VERDICT_FIELDS,
        "activeStatuses": list(__import__("todo_log").ACTIVE_STATUSES),
        "archivedStatuses": list(__import__("todo_log").ARCHIVED_STATUSES),
    }


def seed(root: Path) -> list[Path]:
    """Write the four stores (plus the chat history and a snapshot) under `root`, a SCRATCH
    COPY of the repository -- never this tree. Returns the paths written."""
    out = []
    for rel, obj in (
        (f"data/decisions/{LEAGUE_ID}.json", DECISIONS), (f"data/todos/{LEAGUE_ID}.json", TODOS),
        (f"data/pins/{LEAGUE_ID}.json", PINNED_TS), (f"data/chats/{LEAGUE_ID}_history.json", HISTORY),
        ("data/baseline/bot_research.json", FINDINGS), ("data/baseline/bot_comparisons.json", COMPARISONS),
        (f"data/sleeper_snapshots/{LEAGUE_ID}_latest.json", SNAPSHOT),
    ):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(obj, indent=1))
        out.append(p)
    return out


if __name__ == "__main__":
    if len(sys.argv) > 1:
        for p in seed(Path(sys.argv[1])):
            print("wrote", p)
    else:
        p = payload()
        print(f"{len(p['decisions'])} decisions, {len(p['todos'])} objectives, {len(p['pinned'])} pins, "
              f"{len(p['findings'])} findings, {len(p['comparisons'])} comparisons, {len(p['history'])} messages")
        for d in p["decisions"]:
            print(f"  decision {d['date']} rec={d['recommendation']!r:10} conv={d['conviction']!r:22} outcome={d['outcome']!r}")
        for f in p["findings"]:
            print(f"  finding #{f['id']} {f['player_name']:16} rank={f['rank']!s:5} adj={f.get('adjudication')!s:16} -> {f.get('composite_impact')}")
