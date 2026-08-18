# Fantasy Football Multi-LLM Command Center

A local "front office" for dynasty fantasy football: it syncs your Sleeper
league automatically, merges in your paid Draft Sharks projections from
files on your own disk, and runs roster questions through a four-model
debate panel — grounded in Draft Sharks' math, the wider public market, and
live news — before handing you one clear verdict.

## The Front Office

| Persona | Model | Job |
|---|---|---|
| **Quant / VORP Specialist** | Claude (Anthropic) | Math only — VORP, positional scarcity, roster construction, trade equity, using your league's real scoring settings and your local Draft Sharks data. One lens, not the final word. |
| **Beat / News Tracker** | Gemini (Google, search-grounded) | Cross-references Draft Sharks against public market consensus (KeepTradeCut, FantasyCalc, FantasyPros, ESPN, etc.), plus live news, injuries, and depth charts. |
| **Contrarian / Risk Analyst** | ChatGPT (OpenAI, web-search-enabled) | Pressure-tests the other two — regression risk, small-sample overreaction, model blind spots, age curves, and Draft-Sharks-vs-market divergence. |
| **Debate Moderator** | Claude (Anthropic) | Synthesizes all three into one actionable verdict, calling out where Draft Sharks, the market, and the news disagree. |

Draft Sharks is deliberately treated as **one input among several**, not
ground truth — the Beat Tracker and Contrarian are explicitly instructed to
weigh it against the broader market and against live news rather than just
restate it.

## Design Principles

- **Zero manual credential exposure for league data.** Sleeper's read API
  (`https://api.sleeper.app/v1/`) needs no API key — just your username.
- **Local data sovereignty.** Draft Sharks exports never leave your machine
  or hit a vendor API — you export/save them yourself and upload them here,
  keeping you compliant with Draft Sharks' terms of service. (Market
  consensus sites like KTC/FantasyCalc/FantasyPros are looked up live by the
  Beat Tracker via ordinary web search, since that data is public.)
- **Persisted league threads.** Every league gets its own chat memory at
  `data/chats/<league_id>_history.json`, independent of every other league.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# fill in ANTHROPIC_API_KEY / GEMINI_API_KEY / OPENAI_API_KEY as you have them —
# the app degrades gracefully and tells you in the sidebar which personas are live

streamlit run app.py
```

You only need the keys for the models you want to use. Sleeper sync and the
roster dashboard work with zero keys configured.

## Using it

1. **Sidebar → Sleeper Sync**: enter your Sleeper username, click **Sync
   Leagues**. All leagues you're in for the current season are discovered
   automatically; pick one from the dropdown. Click **Refresh This League**
   any time to re-pull rosters/scoring/taxi/traded picks — a timestamped
   snapshot is cached in `data/sleeper_snapshots/` so the dashboard still has
   data even if Sleeper is briefly unreachable.
   Use **Manage Leagues** below the dropdown to **Archive** leagues you don't
   want cluttering the front dashboard (dead leagues, leagues you left) and
   to reorder the rest with the ▲/▼ buttons — this is saved per Sleeper user
   in `data/league_prefs.json` and persists across sessions. Archived
   leagues stay listed there so you can unarchive them later; a newly
   discovered league is appended to the end rather than disrupting your
   saved order.
2. **Sidebar → Draft Sharks / War Room Data**: Draft Sharks doesn't offer a
   clean CSV export — what you get is its rankings page saved/printed as a
   PDF. Upload that PDF directly (CSV/JSON from other vendors also work).
   Player names, teams, and positions are parsed and matched onto your
   Sleeper roster automatically.
3. **Main dashboard**: your roster (starters, bench, taxi, IR) with merged
   rank/VORP/projection/3D-value columns, plus a staleness banner if the
   loaded projections are getting old (see below).
4. **Debate Studio**: type a question and either click a quick-action button
   or prefix your message:
   - `/debate <question>` — full four-agent panel (default if no prefix)
   - `/claude <question>` — Quant only
   - `/gemini <question>` — Beat Tracker only
   - `/gpt <question>` — Contrarian only

### Data freshness — you don't need to re-sync every session

Draft Sharks updates aren't needed every time you open the app — the
sidebar and dashboard track the date embedded in the loaded PDF (or the
file's save date for CSV/JSON) and only nudge you to refresh once it's **7+
days old**. Roughly a weekly re-export is plenty; the app won't pester you
in between.

## Project layout

```
sleeper_client.py   Sleeper API wrapper: league discovery, rosters, scoring,
                     taxi, traded picks, cached player DB, snapshot caching.
data_merger.py       Draft Sharks PDF rankings parser + CSV/JSON projection
                     parser, name/team/position matching onto Sleeper
                     players, and projection-freshness tracking.
league_prefs.py       Per-Sleeper-user league archive/reorder preferences.
llm_engine.py         Four-persona prompt routing across Claude / Gemini / ChatGPT.
app.py                 Streamlit dashboard + debate studio.
data/sleeper_snapshots/  Cached league syncs (gitignored).
data/projections/         Your local paid PDF/CSV/JSON exports (gitignored).
data/chats/                 Per-league persisted debate history (gitignored).
data/league_prefs.json      Archived/reordered league ids per user (gitignored).
```

## Notes

- **Draft Sharks PDF format**: their rankings page prints as a two-column
  PDF (a numbers column, then a names column) that scrambles naive
  text-extraction order. `data_merger.py` reconstructs each row on a
  per-page basis rather than assuming the whole document reads top to
  bottom, and disambiguates Draft Sharks' first-initial-only names (e.g.
  "J Chase") against Sleeper's full names using team + position, since
  whole-string fuzzy matching alone under- and over-matches on that
  abbreviation. If Draft Sharks changes their page layout, this parser may
  need updating — send me a fresh export if matching quality drops.
- If your league is dynasty superflex PPR, load the Draft Sharks ranking
  flavor that matches (dynasty PPR superflex), not a generic one — mixing
  multiple ranking flavors in `data/projections/` will give inconsistent
  values for the same players.
- Default models (`claude-3-5-sonnet-20241022`, `gemini-2.0-flash`, `gpt-4o`)
  are set in `.env.example` and overridable via `ANTHROPIC_MODEL` /
  `GEMINI_MODEL` / `OPENAI_MODEL` — point them at newer model releases as
  they become available.
- Sleeper's `/players/nfl` endpoint is large and rate-limit sensitive, so it's
  cached locally for 24 hours before being re-pulled.
