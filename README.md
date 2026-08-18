# Fantasy Football Multi-LLM Command Center

A local "front office" for dynasty fantasy football: it syncs your Sleeper
league automatically, merges in your paid Draft Sharks / War Room
projections from files on your own disk, and runs roster questions through
a four-model debate panel before handing you one clear verdict.

## The Front Office

| Persona | Model | Job |
|---|---|---|
| **Quant / VORP Specialist** | Claude (Anthropic) | Math only — VORP, positional scarcity, roster construction, trade equity, using your league's real scoring settings. |
| **Beat / News Tracker** | Gemini (Google, search-grounded) | Live signal only — practice reports, injury designations, pressers, usage trends. |
| **Contrarian / Risk Analyst** | ChatGPT (OpenAI) | Pressure-tests the other two — regression risk, small-sample overreaction, model blind spots, age curves. |
| **Debate Moderator** | Claude (Anthropic) | Synthesizes all three into one actionable verdict, calling out where the math and the news disagree. |

## Design Principles

- **Zero manual credential exposure for league data.** Sleeper's read API
  (`https://api.sleeper.app/v1/`) needs no API key — just your username.
- **Local data sovereignty.** Draft Sharks / War Room / FantasyPros exports
  never leave your machine or hit a vendor API; you drop the CSV/JSON files
  into `data/projections/` yourself, keeping you compliant with each
  vendor's terms of service.
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
2. **Sidebar → Draft Sharks / War Room Data**: upload your 3D projections or
   tier sheet (CSV or JSON). Player names are fuzzy-matched onto your Sleeper
   roster automatically — vendor header naming doesn't need to match exactly.
3. **Main dashboard**: your roster (starters, bench, taxi, IR) with merged
   tier/VORP/projection/trade-value columns.
4. **Debate Studio**: type a question and either click a quick-action button
   or prefix your message:
   - `/debate <question>` — full four-agent panel (default if no prefix)
   - `/claude <question>` — Quant only
   - `/gemini <question>` — Beat Tracker only
   - `/gpt <question>` — Contrarian only

## Project layout

```
sleeper_client.py   Sleeper API wrapper: league discovery, rosters, scoring,
                     taxi, traded picks, cached player DB, snapshot caching.
data_merger.py       CSV/JSON projection parser + fuzzy name matching onto
                     Sleeper player records.
llm_engine.py         Four-persona prompt routing across Claude / Gemini / ChatGPT.
app.py                 Streamlit dashboard + debate studio.
data/sleeper_snapshots/  Cached league syncs (gitignored).
data/projections/         Your local paid CSV/JSON exports (gitignored).
data/chats/                 Per-league persisted debate history (gitignored).
```

## Notes

- Default models (`claude-3-5-sonnet-20241022`, `gemini-2.0-flash`, `gpt-4o`)
  are set in `.env.example` and overridable via `ANTHROPIC_MODEL` /
  `GEMINI_MODEL` / `OPENAI_MODEL` — point them at newer model releases as
  they become available.
- Sleeper's `/players/nfl` endpoint is large and rate-limit sensitive, so it's
  cached locally for 24 hours before being re-pulled.
