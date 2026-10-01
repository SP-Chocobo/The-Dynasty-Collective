"""The dock's payload: one league chat history in the app's OWN shape, constructed because no
real one is stored in this tree (data/chats holds only .gitkeep).

The shape is app.append_message's: {role, content, ts, provider?, model?}. A Full Prytaneum
run is exactly [quant, beat, contrarian, moderator] back to back (app.py groups on that
sequence, find_last_debate matches on it). The Moderator's closing block uses the exact labels
llm_engine.VERDICT_FIELDS parses; the failed chair is llm_engine's own fail-soft string (a
"⚠️ ..." message, appended as content like any other -- run_debate never drops a chair). The
attached context is the REAL ScreenContext prompt seed from scratchpad/mockup_data.json
(superflex_r3: on the clock at 3.03), so "Considering" carries what the app would carry.

What is constructed and says so: the prose of the four chairs. Their lengths (900-2,400 chars)
are set to what the chairs' own system prompts ask for ("be concise" for Beat/Contrarian; a
numbers-first report for Quant; a verdict then a block for the Moderator). Markdown inside the
reports is deliberate: the chairs are not told not to write it, and how the dock renders it is
one of the things the probe measures.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

HERE = Path(__file__).parent

T0 = 1757116800.0  # 2025-09-06 00:00 UTC; spacing is what a real session looks like

MODELS = {
    "quant": ("claude", "claude-sonnet-4-5"),
    "beat": ("gemini", "gemini-2.5-pro"),
    "contrarian": ("openai", "gpt-5"),
    "moderator": ("claude", "claude-opus-4-1"),
}


def _m(role: str, content: str, ts: float) -> dict:
    msg = {"role": role, "content": content, "ts": ts}
    if role in MODELS:
        msg["provider"], msg["model"] = MODELS[role]
    return msg


SUMMARY = (
    "Earlier in this chat (compacted 2025-08-30): the panel reviewed the startup draft plan "
    "twice. Consensus was to anchor the roster on two QBs before round 4 in this superflex "
    "format and to treat TE as a round-5-or-later position unless T Mcbride fell. A HOLD "
    "verdict on D Achane was recorded on 08-22 (Majority; Contrarian dissented on workload). "
    "One objective was opened: check with Roster 6 whether their 2027 1st is available."
)

Q1 = (
    "On the clock at 3.03. The board has Stafford at 107 and Shough at 104 but Shough has "
    "37% survival to my next turn and Stafford is basically gone. Do I take Stafford here or "
    "gamble that Shough comes back?"
)

QUANT_1 = """Numbers first, then what they mean for 3.03.

**Draft Sharks / engine view (season + 3-year)**
- M Stafford (QB, LAR): universal value 101.8, your acquisition value 106.7 UV pts. Need term +4.85 — you have one QB and this is superflex, so the second QB slot is live starter demand, not depth.
- T Shough (QB, NO): universal value 99.6, acquisition 104.1. Same need term. The 2.6-point gap between them is INSIDE the engine's 2.0-point noise band only if you round generously; it is not.
- Next QB after those two: B Mayfield at 100 acquisition, survival 72%.

**Sleeper weekly projection (this week only)**
Stafford 19.4, Shough 15.1, Mayfield 18.8 under your scoring (6 pt pass TD, -2 INT). One week; do not read it as the season.

**Positional scarcity**
There are 3 QBs in the top 8 of your board and 16 picks before your next turn. The engine's forfeit for skipping QB until then is 34.9 UV pts — the largest positional forfeit on the board by 9 points. That is the number that decides this, not the Stafford-vs-Shough gap.

**Divergence to note**
Draft Sharks' 3-year view has Shough ahead of Stafford (age: 37 vs 25). Your league scoring gives no bonus that closes that; it is purely horizon. The engine's dynasty-horizon adjustment already prices it and still lands Stafford 2.6 ahead on acquisition.

Net: if you want a QB at this pick, Stafford is the number. If you want to defer QB, the cost is 34.9, and Mayfield at 72% survival is the realistic fallback, not Shough at 37%."""

BEAT_1 = """Market and news, labelled by source.

**Market consensus (KTC / FantasyCalc, checked today)**
- KTC superflex dynasty: Shough 4,410, Stafford 3,120, Mayfield 3,390. The market has Shough a full tier above Stafford — this is the biggest Draft Sharks vs market split on your board.
- FantasyCalc superflex: same ordering, Shough ranked QB14, Stafford QB22.
- Why they disagree: age. The market is pricing 2027-2029; Draft Sharks' season projection is pricing this year, where Stafford's offense (Nacua, Adams) is the better situation.

**News / depth chart (ESPN, team beat, last 72h)**
- Stafford: full participant all week, no back flare-up reported since August. Named starter, no controversy.
- Shough: named Week 1 starter over Rattler on Tuesday's presser. Coaching staff quote: "he's earned it." Rookie contract, four-year window.
- Mayfield: healthy; Evans/Godwin both active.

**Signal**
The room is drafting rookies early — 42 of 48 picks in the last comparable startup went to first-year players in rounds 1-3. Shough's 37% survival is the engine's read of those rosters' boards; the market number says the real figure is probably lower.

Label: KTC/FantasyCalc figures are market, not projection. Depth chart claims are from team pressers, not speculation."""

CONTRARIAN_1 = """Pressure-testing both.

Against the Quant: the 2.6-point gap is real but it is a SEASON number on a 37-year-old with a back history. The engine's horizon adjustment is a model, not an observation — Draft Sharks' own 3-year view flips the order, and the Quant said so. Two of your three numeric sources disagree with the recommendation; that should cap conviction.

Against the Beat: KTC is a crowd of dynasty players who systematically overpay for youth at QB. A 4,410 vs 3,120 spread is a market opinion about 2028, and you are on the clock in 2025 with one QB rostered. The market being "right" about Shough does not make him available at 3.19.

What both are missing: you do not have to choose between them at THIS pick. Mayfield at 100 acquisition and 72% survival is within 7 points of Stafford and almost certainly there at your next turn. The real question is whether 7 UV pts of QB is worth more than the best non-QB on the board now — C Lamb at 100, 18% survival, at a position where you have nothing.

My read: taking Stafford is defensible and it is what the numbers say. Taking Lamb and Mayfield across the two picks is the higher-variance, higher-ceiling line, and nobody above priced it. Risk on Stafford is not the pick — it is the age cliff arriving mid-window with no exit value."""

MOD_1 = """Take Stafford. The forfeit for skipping QB to your next turn is 34.9 UV pts, the biggest positional cost on the board, and Shough at 37% survival is not a plan — the market number the Beat pulled says the true figure is lower. The Contrarian's Lamb-then-Mayfield line is the one real alternative and it rests on Mayfield surviving 16 picks at 72%; that is a bet, and this is a decisive regime where the engine's own margin (4.1 clear of the second priced candidate, outside the 2.0 noise band) says you do not need one. Draft Sharks' 3-year view flipping the order is why this is Majority and not Unanimous.

RECOMMENDATION: BUY
CONVICTION: Majority
REASON: 34.9 UV pts positional forfeit for deferring QB, with the only alternative QB at 37% survival
DISSENT: Contrarian — prefers C Lamb now and B Mayfield at 3.19 (72% survival) as a higher-ceiling two-pick line
RISK: Stafford's age cliff arrives inside your window with no exit value; a back recurrence turns a 107 into a 2027 problem
ACTION ITEM: If Mayfield is still on the board at 3.19, take him as QB2 regardless of what else is there
SOURCE FINDING: Tyler Shough | KTC | Ranked a full tier above Stafford in superflex dynasty value | 14
SOURCE COMPARISON: Tyler Shough | Matthew Stafford | > | KTC superflex dynasty | market values the four-year window over the 2025 offense"""

Q2 = "Why not Shough though? 37% isn't nothing and he's 12 years younger."

MOD_FOLLOWUP = """Because 37% is the engine compounding sixteen rosters' own boards, and the Beat's market read says those boards like Shough MORE than the engine assumes — so the honest number is below 37, not above it. You'd be passing on a 107 for a coin flip that's weighted against you.

The age point is real and it's exactly why the call was Majority rather than Unanimous. If your plan is to compete in 2027-2029 rather than now, that changes the weighting and I'd say so — but nothing in your roster context says that; you have one QB, twelve teams, and a superflex slot that is live demand today.

If you want the younger arm, the line that actually works is the Contrarian's: Lamb now, Mayfield at 3.19 at 72%. That gives you the WR you have nothing at and a QB2 who is 32 rather than 37. It is not the call I made, but it is a coherent one, and it does not involve hoping Shough falls."""

Q3 = (
    "Roster 6 just offered me their 2027 1st and Kyren Williams for Achane. I'm rebuilding at RB "
    "anyway. Take it?"
)

QUANT_2 = """**Trade equity (Draft Sharks trade values, this league's format)**
- D Achane: 6,410
- K Williams: 4,180
- Roster 6's 2027 1st: the engine values a future 1st at the league's mid-round average, 2,900, until the standings give it a slot. Roster 6 finished 3rd last year; if that holds, the pick is worth closer to 2,200.

Raw: you send 6,410, you receive 6,380 to 7,080 depending on the pick. Even to slightly favourable on paper.

**Roster fit**
Your RB room after the trade: Williams, B Hall, K Walker. Starter demand at RB in this format is 2 plus flex; you would still fill it. Achane's need term on your roster is +4.2; Williams' would be +3.9 — near-identical fit.

**What the numbers do not know**
Whether the 2027 1st lands at 1.03 or 1.10 is the whole trade. That is a standings question, not a valuation one."""

BEAT_2 = "⚠️ Gemini request failed: 503 Service Unavailable"

CONTRARIAN_2 = """The Quant has this as even and it is not, in two ways that cut against each other.

Against taking it: Roster 6 is a contender trading a future pick for a win-now back. Contenders' picks are late. Pricing that 1st at 2,900 flatters it; 2,200 is the realistic figure and the Quant said so. At 2,200 you are sending 6,410 for 6,380 and taking on Williams' workload questions (the Rams drafted Hunter in April).

For taking it: Achane's value is a health number. He has finished one full season in three. The market price of 6,410 assumes the healthy version; you are selling the assumption, which is what a rebuild should do.

No Beat report reached me, so I could not check the Hunter split or Achane's current status. Treat both of those as unverified. My position: the trade is fine in principle and mispriced in one specific place. Ask for the 2027 1st to become their 2026 1st, or add a 2nd. Do not take it as offered."""

MOD_2 = """The trade is close to even on paper and the paper is missing the one number that decides it: where Roster 6's 2027 1st lands. The Beat Tracker did not report this round — the Gemini call failed — so nothing here about Kyren Williams' Hunter split or Achane's current status is verified, and I am not going to pretend it is. Two of three chairs reached the panel. What they agree on: as offered, this is a contender buying your best asset with their latest pick.

RECOMMENDATION: WAIT
CONVICTION: Worth investigation
REASON: The 2027 1st is priced at a league average it will not reach if Roster 6 contends again; the trade is even only at that flattering price
RISK: Achane's next injury arrives before a better offer does and the 6,410 becomes a 4,500
RECON: Ask Roster 6 whether they would swap the 2027 1st for their 2026 1st, or add a 2027 2nd — that is the exact gap the Quant measured
PRICE CEILING: Achane for Williams plus a 1st and a 2nd, nothing less
ALTERNATIVE: If Roster 6 will not move on the pick, Roster 9 is the other contender with an RB hole and they hold their own 2026 1st, which is a known slot rather than a guess — the same conversation there resolves the one number this panel could not.
ACTION ITEM: Counter Roster 6 with Achane for K Williams + 2026 1st before Thursday's waiver run
TODO UPDATE: 1 | Check with Roster 6 whether their 2026 1st is available, not the 2027 | the 2027 pick is priced at a slot it is unlikely to reach"""


#: app.maybe_nudge_stale_free_agents' own wording -- the one writer of the "notice" role.
NOTICE = (
    "Your Free Agent Finder data is 19 days old (as of 2025-08-18). Waiver/roster value shifts week "
    "to week, so if this question is about a current decision, a fresh export would likely be more "
    "accurate — upload one in the sidebar when you get a chance. Answering with what's loaded for now."
)


def transcript() -> list[dict]:
    t = T0
    rows = [_m("summary", SUMMARY, t)]
    t += 3600 * 20
    rows.append(_m("user", Q1, t)); t += 4
    rows.append(_m("quant", QUANT_1, t)); t += 9
    rows.append(_m("beat", BEAT_1, t)); t += 14
    rows.append(_m("contrarian", CONTRARIAN_1, t)); t += 8
    rows.append(_m("moderator", MOD_1, t)); t += 120
    rows.append(_m("user", Q2, t)); t += 6
    rows.append(_m("moderator", MOD_FOLLOWUP, t)); t += 3600 * 5
    rows.append(_m("user", Q3, t)); t += 1
    rows.append(_m("notice", NOTICE, t)); t += 4
    rows.append(_m("quant", QUANT_2, t)); t += 1
    rows.append(_m("beat", BEAT_2, t)); t += 7
    rows.append(_m("contrarian", CONTRARIAN_2, t)); t += 9
    rows.append(_m("moderator", MOD_2, t))
    return rows


#: The attached context, verbatim from the real ScreenContext seed in scratchpad/mockup_data.json.
ATTACHED_CONTEXT = {
    "surface": "Draft Room",
    "looking_at": "On the clock for pick 3.03.",
    "decision": "Decision regime: decisive.",
    "evidence": (
        "M Stafford (QB) — PREFERRED, acquisition value 107 UV pts, survival 0%\n"
        "T Shough (QB) — PREFERRED, acquisition value 104 UV pts, survival 37%\n"
        "T Mcbride (TE) — STRONG ACTION, acquisition value 103 UV pts, survival 0%\n"
        "C Lamb (WR) — STRONG ACTION, acquisition value 100 UV pts, survival 18%\n"
        "B Mayfield (QB) — PREFERRED, acquisition value 100 UV pts, survival 72%\n"
        "D Achane (RB) — PREFERRED, acquisition value 96 UV pts, survival 0%\n"
        "J Jefferson (WR) — PREFERRED, acquisition value 92 UV pts, survival 72%\n"
        "K Walker (RB) — PREFERRED, acquisition value 91 UV pts, survival 44%\n"
        "...and 59 more candidate(s) in the current pool/scope."
    ),
    "entities": ["M Stafford", "T Shough", "T Mcbride", "C Lamb", "B Mayfield", "D Achane", "J Jefferson", "K Walker"],
}

TODOS = [
    {"id": 1, "ts": T0 - 86400 * 9, "date": "2025-08-28", "text": "Check with Roster 6 whether their 2027 1st is available",
     "source": "moderator", "question": "Is Roster 6 a trade partner for picks?", "decision_ts": None, "status": "active",
     "resolution_reason": "", "resolution_date": None, "revisions": [], "notes": []},
    {"id": 2, "ts": T0 + 3600 * 20 + 40, "date": "2025-09-06", "text": "If Mayfield is still on the board at 3.19, take him as QB2 regardless of what else is there",
     "source": "moderator", "question": Q1, "decision_ts": None, "status": "active",
     "resolution_reason": "", "resolution_date": None, "revisions": [], "notes": []},
    {"id": 3, "ts": T0 + 3600 * 25 + 40, "date": "2025-09-06", "text": "Counter Roster 6 with Achane for K Williams + 2026 1st before Thursday's waiver run",
     "source": "moderator", "question": Q3, "decision_ts": None, "status": "active",
     "resolution_reason": "", "resolution_date": None, "revisions": [], "notes": []},
]


def payload() -> dict:
    return {
        "league": {"name": "Gold Wyrm Dynasty", "format": "12-team · Superflex · Dynasty"},
        "history": transcript(),
        "attached": ATTACHED_CONTEXT,
        "todos": TODOS,
        "pinned": [T0 + 3600 * 20 + 35],  # the first verdict is pinned
        "roleNames": {"quant": "Quant", "beat": "Beat Tracker", "contrarian": "Contrarian", "moderator": "Moderator"},
        "verdictFields": ["RECOMMENDATION", "CONVICTION", "REASON", "DISSENT", "RISK", "RECON", "PRICE CEILING", "ALTERNATIVE", "ACTION ITEM"],
    }


if __name__ == "__main__":
    out = HERE / "dock_transcript.json"
    out.write_text(json.dumps(payload(), indent=1))
    rows = transcript()
    print(f"wrote {out} · {len(rows)} messages · chars per role:")
    for r in rows:
        print(f"  {r['role']:11s} {len(r['content']):5d}  {'(fail-soft)' if r['content'].startswith('⚠️') else ''}")
