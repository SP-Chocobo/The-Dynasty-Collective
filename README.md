# Fantasy Football Multi-LLM Command Center

A local "front office" for fantasy football — dynasty first, but redraft,
keeper, Best Ball, and Chopped all get genuinely different treatment, not
just a label swap (see "League format" below). It syncs your Sleeper league
automatically, merges in your paid Draft Sharks projections from files on
your own disk, and runs roster questions through **The Prytaneum** — the
four-model deliberation chamber described below — grounded in Draft Sharks'
math, the wider public market, and live news — before handing you one clear
verdict.

## The Front Office

| Persona | Model | Job |
|---|---|---|
| **Quant / VORP Specialist** | Claude (Anthropic) | Math only — VORP, positional scarcity, roster construction, trade equity, using your league's real scoring settings, your local Draft Sharks data, and Sleeper's own native weekly stat-category projections. Neither numeric source is the final word. |
| **Beat / News Tracker** | Gemini (Google, search-grounded) | Cross-references Draft Sharks against public market consensus (KeepTradeCut, FantasyCalc, FantasyPros, ESPN, etc.), plus live news, injuries, and depth charts. |
| **Contrarian / Risk Analyst** | ChatGPT (OpenAI, web-search-enabled) | Pressure-tests the other two — regression risk, small-sample overreaction, model blind spots, age curves, and Draft-Sharks-vs-market divergence. |
| **Debate Moderator** | Claude (Anthropic) | Synthesizes all three into one actionable verdict, calling out where Draft Sharks, the market, and the news disagree, and closes with a structured recommendation (see "Structured verdicts & the decision log" below). |

Draft Sharks is deliberately treated as **one input among several**, not
ground truth — the Beat Tracker and Contrarian are explicitly instructed to
weigh it against the broader market and against live news rather than just
restate it. Every role is fully reassignable to any of the three providers
(sidebar → 🤖 Roles & Routing) — the table above is just the recommended
default, not a hard requirement; all three providers now have their own
native live web search, so which one ends up on Beat/Contrarian is a
"whose answers do you like" choice, not a capability tradeoff.

## Engineering Doctrine

Semantic integrity, the required audit chain, and the contracts a load-bearing quantity must
carry before it enters the engine: see [ENGINEERING_DOCTRINE.md](ENGINEERING_DOCTRINE.md). It
exists because a component-level audit passed a system whose quantities had drifted apart at the
boundaries, and the K/DST investigation is recorded there as the discovery mechanism.

## Design Principles

- **Zero manual credential exposure for league data.** Sleeper's read API
  (`https://api.sleeper.app/v1/`) needs no API key — just your username.
- **Local data sovereignty.** Draft Sharks exports never leave your machine
  or hit a vendor API — you export/save them yourself and upload them here.
  DynastyProcess/FantasyPros/KeepTradeCut/ESPN work the same way: only
  facts-only extractions (name/team/position/rank/value — never the
  vendor's own PDF, page layout, or branding) ever get committed, per the
  same reasoning applied consistently across every source rather than
  re-litigated per vendor — see "The baseline pool & the composite score"
  below. (Live web search by the Beat Tracker/Contrarian mid-debate is
  separate from this and untouched by it.)
- **Persisted league threads.** Every league gets its own chat memory at
  `data/chats/<league_id>_history.json`, independent of every other league.

## The Draft Engine — Contextual Decision Matrix Engine (CDME)

**Contextual Decision Matrix Engine (CDME)** is this project's canonical name
for its core deterministic decision-synthesis system — the machinery behind
Draft Room, the Mock Draft prototype, and every multi-chair draft simulation
in `draft_simulation.py`. It evaluates available candidates against universal
value and the contextual dimensions relevant to the current decision
state — roster construction, positional need, scarcity/cliff risk, survival,
denial/block opportunity, eligibility/flexibility, and defined tiebreak
conditions — to produce team-specific acquisition value and decision-state
outputs.

CDME is **not** a single ranking formula, an LLM, or an autonomous drafter.
It is the deterministic synthesis layer that converts several interacting
signals into one frozen decision state that downstream interfaces and
optional AI debate can interpret. It has no LLM anywhere in its own critical
path — see `draft_room.py`'s own module docstring for why that's a hard
requirement, not a style preference, given a live draft's pick clock.

**What it consumes:** the live board (Sleeper roster/pick state plus
Draft Sharks/Sleeper-native projections already loaded elsewhere in this
app), the league's own scoring/roster settings, and the picks already made
so far in the current draft.

**What it produces, in two layers:**

- `draft_room.py` computes the base valuation math per candidate —
  `universal_value` (team-agnostic: BPA + time-horizon + risk adjustments)
  and **Team Acquisition Value (TAV)**, CDME's principal quantitative
  output — `universal_value + need_bonus + eligibility_bonus`, this
  roster's own fit layered on top of the team-agnostic number. All three
  terms are unit-matched to the same bpa-anchored scale and individually
  bounded (`need_bonus` capped at `NEED_BONUS_MAX`; `eligibility_bonus` —
  the value a candidate's multi-position flexibility unlocks, computed by
  `lineup_optimizer.py`'s real assignment-problem solver — is rescaled from
  its native Draft-Sharks-`trade_value` currency into that same bpa scale
  and capped at `ELIGIBILITY_BONUS_MAX`) specifically so neither roster-fit
  term can override a genuine talent gap on its own; see "Known Limitations
  & Audit History" below for the real defect this bound was added to close.
- `pick_synthesis.py` adds the contextual signals that don't answer "how
  good is this player" but "how badly do I need to make THIS selection
  right now": positional cliff, survival probability, denial/rival
  premium, positional-run detection, market-consensus reach, and
  **pick necessity** (`pick_necessity` / `necessity_label`) — built
  additively from those already-computed signals, never a new invented
  number.

**PickSnapshot** (`pick_synthesis.PickSnapshot`) is CDME's principal decision
artifact: a frozen representation of the board, the narrowed candidate set,
every contextual signal above, the **decision regime** (how decisive vs.
contested the evidence is), and an input-state stamp — the one object every
downstream consumer (UI panel, stored decision log, LLM debate) reasons over
instead of recomputing or guessing any of it.

**Candidate narrowing** (`pick_synthesis.narrow_candidates`) is what turns
the full scored board into the human-facing **candidate set** ("the hand"):
the top players by TAV, plus the single best remaining player at every
position the board covers (closing a real blind spot a pure VOR cutoff would
otherwise create — see that function's own docstring), plus any player the
user has explicitly flagged. This is the option set a human actually
chooses from, and the one this project's own adversarial validation work
(`option_set_analysis.py`) exists specifically to measure the completeness
of.

**Decision Forces** are the small, interpretable flags a candidate can carry
inside its own PickSnapshot entry — near-tie, cliff protection, block
opportunity, pure value — surfaced directly rather than left for a reader
(human or LLM) to infer from raw numbers.

**Where the UI fits:** `draft_board_ui.py` and `app.py` are a **translation
layer** over CDME's outputs. They render PickSnapshot's already-decided
ranking, badges, and forces — they must never independently re-rank
candidates, invent a competing value, or re-derive CDME's math themselves.

**Where AI debate fits:** `pick_debate.py`'s multi-persona "Debate My Pick"
is optional **interpretive escalation** over a frozen PickSnapshot — it may
interpret, contextualize, or challenge the evidence CDME already computed,
but it is never a replacement for CDME as the deterministic decision
authority, and it is never given the chance to compute or guess a number
CDME didn't already provide.

**Architectural relationship, summarized:**

```
CDME (draft_room.py + pick_synthesis.py)
  → PickSnapshot (frozen decision state: candidates, TAV, Decision Forces, Decision Regime)
    → presentation (draft_board_ui.py / app.py — translates, never re-derives)
    → optional debate escalation (pick_debate.py — interprets, never replaces)
```

## The Prytaneum — Multi-Intelligence Deliberation

**The Prytaneum** is the Dynasty Collective's multi-intelligence deliberation
capability. It receives deterministic evidence and decision context from CDME
(and from any surface's own already-computed reads) and provides structured
interpretation through four roles — **Quant** (quantitative/valuation
analysis), **Beat** (substantive/contextual read), **Contrarian** (adversarial
challenge), and **Moderator** (adjudication and final synthesis) — see "The
Front Office" above for what each role actually does and which model powers
it by default. It is an escalation layer for questions where deterministic
analysis benefits from interpretation, disagreement, or synthesis. It does
**not** replace CDME as the authoritative deterministic decision engine, does
not independently re-price players, and never becomes the authoritative
scoring layer.

The three-tier relationship, stated plainly:

```
CDME computes.
The Prytaneum deliberates.
The user decides.
```

Or as the full chain: `CDME → decision state / evidence → The Prytaneum →
user judgment`. Every specialized decision surface (Draft Room, Trade
Calculator, League, Matchup, Maintenance) can **escalate** into The
Prytaneum — a small, persistent 💬 Debate control, present on every surface,
hands over that surface's own already-computed `ScreenContext` (see
`screen_context.py`) rather than making the roles re-derive or guess at
what's on screen. See "Structured verdicts & the decision log" and "Debate
Studio" -- now formally The Prytaneum -- below for the full user-facing
behavior.

Draft Room additionally has its **own**, separate, dedicated deliberation
system ("Debate My Pick": Strategist, Skeptic, Caller — see `pick_debate.py`)
that reasons over one frozen `PickSnapshot` with no live search. This is
deliberately **not** part of The Prytaneum — different roles, different
scope, built specifically for one board state — and is not being renamed by
this terminology pass.

This project also maintains a separate, offline **engine-validation harness**
(`draft_simulation.py`, `draft_counterfactual.py`, `roster_diagnostics.py`,
`option_set_analysis.py`, and the `run_*_validation.py` drivers) that
measures CDME's own behavior — divergence from best-player-available and
market consensus, weak-roster tracing, decomposable roster diagnostics, and
option-set completeness — against real simulated drafts. That harness
reads CDME's outputs; it is not part of CDME itself, and never modifies
production decision logic on its own authority (see each module's own
docstring for its own explicit, pre-declared thresholds).

**What this harness has, and has not, established.** Multi-chair
("12-chair") simulations run every seat through the same production
`build_snapshot` machinery — never a simulation-specific valuation
shortcut — and have confirmed each chair's roster/pick state stays
correctly isolated (no cross-chair contamination) and that contextual terms
(need, eligibility, cliff, denial) stay bounded relative to real
`universal_value` gaps rather than overriding them. That is a real,
demonstrated finding. It is **not** evidence that CDME's picks are
"better" than BPA or market ADP in any outcome sense — no real-season
result data feeds this harness — and a divergence from BPA/ADP in a
simulated trajectory is not treated as inherently correct just because the
context engine produced it; sometimes BPA or ADP is the right call, and the
harness's own option-set/divergence measurements are read that way, not as
a scorecard CDME is trying to win. Nor does path-dependent divergence
across simulated drafts constitute proof that a Markov/state-sufficiency
assumption holds — it demonstrates the mechanism is contextually
responsive, not that its state representation is complete or optimal.

**Looking further ahead:** see `ROADMAP.md` for the longer-term vision of a
centrally maintained, canonical knowledge substrate feeding CDME and every
surface above — a vision document, not a description of anything built
today.

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

### Staying up to date

There's no live sync between this repo and your local copy — git doesn't
work that way, and Streamlit needs the actual files on disk to run. The
closest thing to it: `update_and_run.ps1` (Windows) / `update_and_run.sh`
(Mac/Linux) pulls the latest pushed code, installs anything new in
`requirements.txt`, and launches the app, all in one command:

```powershell
.\update_and_run.ps1        # Windows
```
```bash
./update_and_run.sh         # Mac/Linux — chmod +x it once first
```

Run that instead of `streamlit run app.py` directly whenever you want
whatever's newest. It never touches `data/` or `.env` — those are yours,
gitignored, and untouched by pulling new code.

You only need the keys for the models you want to use. Sleeper sync and the
roster dashboard work with zero keys configured. Rather than hand-editing
`.env`, you can also paste them straight into the app: sidebar → **🔑 Connect
Your Accounts** takes a pasted `.env`-style blob (or an uploaded
`.txt`/`.env`/`.pdf`) with any of `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` /
`OPENAI_API_KEY` / `SLEEPER_USERNAME` on it, applies them immediately, and
writes them into your local `.env` so it's a one-time step. It also
recognizes a few common aliases (`CLAUDE`, `GOOGLE`, `CHATGPT`, `GPT`) and
falls back to sniffing bare key values by their provider prefix (`sk-ant-`,
`AIza…`, `sk-…`) if you paste something with no labels at all.

**Run this locally — don't deploy it to a public host.** Every persistence
mechanism in this app (chat history, the decision log, league archive/
reorder prefs, Draft Sharks uploads, player aliases, format overrides, the
remembered Sleeper username) is a flat JSON file on local disk, by design —
see "Design Principles" above. That's correct and private for
`streamlit run app.py` on your own machine, but breaks on something like Streamlit
Community Cloud: the filesystem there isn't durable (a redeploy or a
free-tier sleep/wake cycle can wipe `data/` without warning) and, worse,
isn't private to you — it's one shared container across every visitor to
that URL, so their local files (and yours) can collide or leak into each
other. The Sleeper-session auto-restore (below) is the clearest example —
whoever loaded the page last is whose session the next visitor would see —
but the same mismatch applies to every file under `data/`. None of this
code changes based on where you run it; running it locally is what makes it
correct.

## Using it

1. **Sidebar → Sleeper Sync**: enter your Sleeper username, click **Sync
   Leagues**. All leagues you're in for the current season are discovered
   automatically. Your username is remembered locally
   (`data/last_session.json`) and re-synced automatically the next time you
   open or refresh the page — Streamlit's own `session_state` resets on
   every browser reload, so without this you'd have to type your username
   and click Sync Leagues again every single time.
   Pick which league you're viewing from the **📂 Active League** switcher
   at the top of the main dashboard, not the sidebar — it's the control
   you'll use most, so it lives front and center. **🔄 Refresh** sits right
   next to it to re-pull that league's rosters/scoring/taxi/traded picks; a
   timestamped snapshot is cached in `data/sleeper_snapshots/` so the
   dashboard still has data even if Sleeper is briefly unreachable, and a
   league that's never been synced before auto-fetches once the first time
   you switch to it, rather than showing empty until you separately hit
   Refresh.
   Since Sleeper's league list is a full replacement each time (not
   incremental), **Sync Leagues** doubles as new-league detection — anything
   you've joined or created since last sync just shows up. It also detects
   the opposite: if a league you were tracking is no longer returned (you
   left, were removed, or the league was deleted), a prompt appears letting
   you **Archive**, **Delete**, or **Keep as-is** for each one, rather than
   it just silently vanishing from the list with its local data left behind
   forever. This check is against what's actually persisted, not just the
   current browser session, so it still works on your very first sync after
   a restart.
   Use **Manage Leagues** below the dropdown to **Archive** leagues you don't
   want cluttering the front dashboard (still fully cached, just hidden) or
   **Delete** them permanently (purges the cached snapshot, that league's
   own Draft Sharks uploads, chat history, and format override — gated
   behind a confirmation step since it's not reversible). Reorder the rest
   with the ▲/▼ buttons. All of this is saved per Sleeper user in
   `data/league_prefs.json` and persists across sessions; a newly discovered
   league is appended to the end rather than disrupting your saved order.
   Deleting is local-only — it doesn't leave the Sleeper league itself, so
   if you're still actually a member it'll simply reappear, unsynced, next
   time you sync.
2. **Sidebar → Draft Sharks / War Room Data**: one upload box, auto-routed
   by what the file actually is — the kind is sniffed from the PDF's own
   content, not its filename or which league happens to be selected:
   - **Dynasty Rankings** — a season/multi-year overall ranking (1yr proj,
     3yr proj, 3D Value), computed from *format* assumptions (PPR/standard,
     superflex/1QB, TE premium), not from any specific roster. The same
     export is correct for every league sharing that format, so it goes
     into a **shared pool** (`data/projections/_global/`) and is available
     to every league automatically — no re-uploading per league, no
     cross-league copying to reason about.
   - **Free Agent Finder** — a rest-of-season, this-league-contextual view
     (3D Proj, 3D ROS, Ceiling, 3D Value+) that also tags each player Mine
     (already on your roster), Add/Drop (Draft Sharks' own suggested waiver
     move), or blank (an ordinary free agent). This genuinely can't be
     shared — it reflects one league's actual roster — so it's stored under
     `data/projections/<league_id>/` and only ever applies to the league
     selected when you upload it. Supports K/DEF and IDP (LB/DL/DB)
     leagues, not just standard offensive skill positions.
   - **League Analyzer** (team-vs-team power rankings/standings) is also
     league-specific but isn't parsed yet — uploading one shows a clear
     error rather than being silently mis-read by the rankings parser.
   Even a same-format shared ranking won't perfectly match every league's
   exact rules, so this league's **full, real Sleeper scoring settings**
   (every non-zero stat-category weight, not just a PPR/superflex label)
   are always given to the Quant too — see "Scoring-aware tier adjustment"
   below. CSV/JSON exports from other vendors also work via the normal
   column-alias path, and are treated as format-based (shared pool) like
   Dynasty Rankings.
3. **Main dashboard**: your roster (starters, bench, taxi, IR) with merged
   rank/VORP/projection/3D-value columns (plus rest-of-season/ceiling/value
   from the Free Agent Finder export, when loaded), and a full-width
   **Free Agents** panel below it — filterable by position, sorted by 3D
   Value+, with your own roster excluded by default (toggle to include it).
   If any roster players didn't auto-match to your loaded Draft Sharks data,
   an **Unmatched Players** expander shows up under the match-rate line —
   pick the player, type the exact name Draft Sharks printed for them, and
   save; that mapping is remembered in `data/player_aliases.json` and
   overrides automatic matching for that player from then on. Automatic
   matching mostly works, but an unusual name shape, a mid-season team
   change, or WR/RB dual eligibility can occasionally slip through it. A
   **Manual Aliases** expander right below it lists every alias currently
   set with a Remove button next to each, to go back to auto-matching.
   The upload box itself has a **comments/questions/labels** text field
   right alongside the file picker — write a note at the moment you upload
   (e.g. "ignore this ranking, Bijan tweaked his hamstring in preseason")
   rather than having to track it down afterward. Above that is a **Global /
   Specific league(s)** toggle — pick Specific and a league multiselect
   appears — since a note's scope can't be reliably guessed from its content
   the way a Draft Sharks PDF's kind can: "Chase is questionable" is true
   for every league, but "considering trading my 2nd for their WR1" is
   clearly about one league's roster and would just be noise (or actively
   misleading) in another league's debate. It defaults to Global; a
   Specific-scoped note is only ever included in the leagues you picked.
   Click **Upload** to submit everything together (it's a form, not an
   instant-on-select uploader, so nothing gets processed until you actually
   click it). If the file turns out to be recognized Draft Sharks data, the
   note still reaches the panel as a small reference-material entry with
   the same scope.
   Below that, a full-width **Reference Material** panel holds anything
   uploaded that *isn't* recognized Draft Sharks data — a screenshot of an
   injury notification, an article, a tweet — instead of the upload just
   silently discarding it. This panel always lists everything regardless of
   scope (so you can find and manage anything), showing each item's current
   scope and letting you change it after the fact. Every item's caption
   (not the raw file) is what actually reaches The Prytaneum, labeled
   explicitly as an unverified claim to weigh, not fact; edit a caption
   there any time too.
4. **The Prytaneum** (formerly labeled "Debate Studio"): type a question and
   either click a quick-action button or prefix your message:
   - `/debate <question>` — full four-role deliberation (default if no prefix)
   - `/claude <question>` — Quant only
   - `/gemini <question>` — Beat Tracker only
   - `/gpt <question>` — Contrarian only
   When Free Agent Finder data is loaded, the top 15 available free agents
   (by 3D Value+) are included in the context automatically, so waiver/pickup
   questions have real data to reason from.
   The Prytaneum also has real memory now: your last ~16 messages (plus any
   compacted summary — see below) are fed back into every deliberation's
   context, so a later question can reference earlier trade discussions,
   consensus verdicts, and roster strategy instead of starting fresh each
   time.

### Scoring-aware tier adjustment

A Draft Sharks tier list is computed under Draft Sharks' own scoring
assumptions, which will often sit somewhere *between* what two different
list flavors assume for your actual league — a partial-PPR league between
a full-PPR and a standard list, a modest TE bonus that only partly closes
the gap a full TE-premium list would show, and so on. Rather than treating
a loaded tier/value number as exact, the Quant is given this league's
complete real scoring settings and instructed to use judgment: nudge a
player's implied value up or down when the specific weights point that
way, and say so explicitly rather than silently overriding the number.

### League format — dynasty, redraft, Best Ball, Chopped

Dynasty vs. keeper vs. redraft is detected automatically from Sleeper
(`settings.type`) and shapes reasoning without you doing anything: in a
non-dynasty league, the Quant is told explicitly to discount or ignore
Draft Sharks' 3yr/5yr multi-year projections and rookie-pick trade value,
since the roster doesn't persist to next season and only this-year
production matters.

Best Ball and Chopped are a different story — I don't have verified
knowledge of the exact Sleeper API field either mode uses (Chopped
especially is newer/niche), and I'd rather not guess a field name and risk
silent misdetection. So they're a manual **Special format** dropdown next
to the league selector, off by default:
- **Best Ball**: no start/sit decisions (your highest-scoring eligible
  lineup is picked automatically each week) and typically no waivers or
  trades either. The panel is told to say so plainly if asked a
  week-to-week question that doesn't apply, and redirect toward what
  actually is decidable — draft-day roster construction and depth.
- **Chopped**: no 1v1 matchups — the whole field competes each week and the
  single lowest scorer is eliminated, their full roster dumped onto
  waivers at once. Trades are disabled, so the panel never suggests or
  evaluates one in a Chopped league. Start/sit leans toward floor over
  ceiling more than usual, since surviving one bad week against the entire
  field matters more than a big week against one opponent.

Setting this doesn't touch Sleeper — it's local-only and instant, one
dropdown per league, persisted to `data/league_formats.json`.

### Chat history compaction

Long-running leagues build up a lot of chat history. **🧹 Compact History**
(next to Clear Chat History, once there's something to compact) distills
everything older than a chosen age (30 days by default) into one dense
memory block — targeted players, trade/waiver consensus reached, long-term
roster strategy — via a dedicated Claude call, then prunes the raw old
messages, keeping recent turns untouched. It's safe by construction: the
file is never overwritten unless the summarization call actually succeeds
(a failure leaves your history exactly as it was), a timestamped backup of
the pre-compaction file is written first regardless, and a prior summary is
merged forward on repeated compactions rather than overwritten, so older
context doesn't quietly disappear over multiple runs.

### Data freshness — you don't need to re-sync every session

Draft Sharks updates aren't needed every time you open the app — the
sidebar and dashboard track the date embedded in the loaded PDF (or the
file's save date for CSV/JSON) and only nudge you to refresh once it's **7+
days old**. Roughly a weekly re-export is plenty; the app won't pester you
in between. The sidebar's **Status** section shows one glanceable overall
**Data Freshness** grade (Fresh/Recent/Aging/Stale, the same scale the
composite score uses) above the per-source breakdown, driven by the oldest
of everything currently loaded — purely informational, never a gate, since
the committed baseline keeps every answer working regardless of how old
anything is.

Every debate also gets an explicit **DATA FRESHNESS** manifest in its
context — an as-of date and age for Draft Sharks Dynasty Rankings, Draft
Sharks Free Agent Finder, and the Sleeper league sync, sorted freshest
first (the Beat Tracker's and Contrarian's own live web search is always
treated as fresher than any of those, since it runs at the moment of the
question). When two sources disagree, the panel is instructed to lean
toward the more recently updated one — decisively for time-sensitive
claims like injury status or depth chart position, only mildly for stable
long-term dynasty valuations, since staleness doesn't invalidate a
season-long projection the way it invalidates "is this guy still the
starter." The Moderator treats this as its primary tie-breaker and is told
to say explicitly when it's using it, so a verdict reads as "X is more
current" rather than an unexplained "X is more correct." Data missing
entirely is handled the same way: the panel is told plainly what isn't
loaded and to answer anyway from positional reasoning, market consensus,
and general judgment — never to refuse or stall — flagging the gap in its
answer only when it's actually material to the question, not as boilerplate
on every response. A source aged 30+ days is called out as **egregiously
outdated** rather than lumped in with ordinary staleness.

### Proactive nudge for stale waiver data

Free Agent Finder data is the most time-sensitive thing this app loads —
waiver value shifts week to week, unlike season-long dynasty rankings. So
rather than leaving that caveat buried in the LLM's prose, the app itself
checks it deterministically: if the loaded Free Agent Finder data is stale
when you ask a debate question, a **⚠️ NOTICE** message appears in the
chat suggesting a fresh export, before the panel answers anyway with
what's loaded. It won't repeat itself every question — the nudge is keyed
to that file's specific as-of date, so it only fires once per that
freshness state (a fresh session, or the data getting even more stale,
resets it), not on every message while you're mid-conversation.

### Structured verdicts & the decision log

Every `/debate` answer ends with a structured block instead of one free-text
verdict line:

```
RECOMMENDATION: BUY / SELL / HOLD / WAIT
CONVICTION: Unanimous / Majority / Split / Speculative / Worth investigation
REASON: <the deciding factor>
DISSENT: <who dissented and why — only if CONVICTION is Majority>
RISK: <the biggest risk to this being wrong>
RECON: <a concrete thing to ask another manager — only if CONVICTION is Worth investigation>
PRICE CEILING: <the most to give up — only if it's a trade question>
ALTERNATIVE: <a genuinely better different move — only when one actually exists, typically a
              SELL/WAIT trade call or an unsettled Split/Speculative one. Not mechanical: most
              non-BUY verdicts still omit this line, and unlike everything above it, when it IS
              written it gets a sentence or two of real reasoning, not just a bare name>
```

**CONVICTION is deliberately not a confidence percentage** — a self-reported
number from an LLM is fake precision with nothing calibrating it. Instead it
reflects something real: whether the Quant, Beat Tracker, and Contrarian
actually agree.

- **Unanimous** — all three land the same direction.
- **Majority** — two agree, one dissents; the Moderator says who and why.
- **Split** — no real consensus among the three.
- **Speculative** — agreement isn't the issue, the underlying evidence is
  thin (a rookie with no track record, a projection with no market/news
  confirmation, stale data).
- **Worth investigation** — the analysis is sound as far as it goes, but the
  real answer depends on something only another manager can tell you. The
  Moderator's `RECON` line spells out exactly what to go ask them — e.g.
  "Ask Team 4 if Player X is available for picks."

Every parsed verdict is appended to that league's **decision log**
(`data/decisions/<league_id>.json`) — question, recommendation, conviction,
reason, dissent, risk, recon, price ceiling, and the full Moderator text.
Parsing fails soft: if a response doesn't follow the format (or a provider
call errored), nothing is logged rather than recording a fabricated verdict.
A **📋 Decision Log** expander under the chat history shows the running
table for the selected league, newest first — the actual point being able
to look back later and check whether the front office's calls held up.

### Persistent objectives

A one-off verdict is easy to lose track of. A Moderator verdict whose
`ACTION ITEM` line implies a genuinely new, trackable objective
(`data/todos/<league_id>.json`) — "offer Team 4 a 2027 3rd for Player X
before Thursday's waiver run," not a restated call — gets logged automatically,
and every future question in that league gets the list of currently open
ones as standing context, not just questions that happen to mention them:
a rebuild-vs-contend objective shapes even an unrelated start/sit call. The
Moderator can also propose one looks done (`TODO LIKELY RESOLVED`) or
revise it when new information changes what it actually is
(`TODO UPDATE`) — either way you confirm or reject the proposal, it never
closes or rewrites one on its own. The **🎯 Active Objectives** expander lists
everything currently open (🤖 for panel-sourced, ✍️ for ones you added by
hand), lets you add one manually, and resolve/dismiss/delete with an
optional note that becomes permanent strategic memory in the **Archive**
below it — a later related question can then weigh whether something
similar already worked or already missed, not just re-derive the same
reasoning cold.

Any bot message in The Prytaneum can also become an objective directly
— a **🎯 Add as objective** button next to the pin button drops that
message's own text straight into the Active Objectives box (free, no model
call), and a **🤖 Ask Moderator** button in that box can replace it with a
version condensed from the surrounding conversation and the league's
existing objectives, for a long or meandering answer actually worth
distilling down to the real ask buried in it.

### The baseline pool & the composite score

Draft Sharks (uploaded by you, per "Local data sovereignty" above) isn't
the only *structured* valuation source anymore — `data/baseline/` also
ships four more, extracted as facts-only CSVs (never the vendor's own
PDF/branding) and **committed to git**, so a fresh clone isn't empty on
first launch the way `data/projections/` is. Three of the four (everything
but ESPN, which is redraft-scope — see below) can be refreshed without a
code change too: sidebar → **🔄 External Valuation Sources** takes a
fresher CSV in the same shape and overwrites that source's file exactly,
so the composite keeps reading it as one continuous source rather than
quietly double-counting an untracked second copy alongside the old one.

| Source | Shape | Scope |
|---|---|---|
| **DynastyProcess** (`external/dynastyprocess/`) | 1QB/2QB point value, ~0-10000 scale, derived from FantasyPros' ECR via a documented formula | Dynasty |
| **FantasyPros** (`external/fantasypros/`) | Rank/tier off an expert panel — dynasty, best-ball, *and* IDP lists, each kept in its own file | Dynasty (one file) + redraft (two files) |
| **KeepTradeCut** (`external/keeptradecut/`) | Crowdsourced 0-9999 value, players and picks on one scale | Dynasty |
| **ESPN** (`external/espn/`) | Three analysts' individual + averaged IDP ranks | Redraft |

None of these are blended into Draft Sharks' own numbers — every source
rides alongside it as its own labeled opinion
(`DataMerger.external_player_values`), each on its own incompatible scale. On top of
that, `DataMerger.composite_player_score` computes this app's **own**
single 0-100 blended score per player: every *external* source is
converted to a percentile against its *own* pool first (the only sound
way to combine scales this different — ~0-10000, rank-out-of-552,
~0-9999, a bare rank number), then weighted — KTC a bit lower (a
crowd-vote average), a source's weight halving every 60 days as it ages
(`COMPOSITE_RECENCY_HALFLIFE_DAYS`) so a fresh source outweighs a stale
one automatically. Draft Sharks itself is the one exception: its
trade_value is already a 0-100 scale *and* already scarcity-adjusted by
position (elite offense reaches 100, elite IDP tops out around 35-45 by
Draft Sharks' own judgment), so it's weighted a bit higher and used
directly rather than re-normalized — re-deriving a percentile from it
would rank it against a pool so bottom-loaded with bench/depth players at
every position that almost any real starter clears the 80th percentile
regardless of how good they actually are, erasing the very scarcity
signal that made Draft Sharks worth weighting highest in the first place.
Redraft-scope files (FantasyPros' best-ball/IDP lists, ESPN) never feed
it — only genuine dynasty sources do. No coverage anywhere returns `None`
(shown as **Incomplete Player Profile**), never a fabricated number.

A percentile is only as meaningful as the pool it's computed against.
Below `COMPOSITE_MIN_TRUSTED_POOL_SIZE` (20) rows, a source's weight scales
down proportionally to how thin its pool actually is — confirmed the hard
way early on: with a single bot-research finding on the books, it read as
the 100th percentile regardless of whether the underlying claim was rank 1
or rank 15, since a pool of one always ranks its only member first. Every
structured source (Draft Sharks, DynastyProcess, FantasyPros, KTC) already
clears that threshold by hundreds of rows and is never affected in
practice — it only bites bot-research findings early on, before enough
have accumulated. Those findings are also segmented into offense/IDP pools
before being percentiled, not pooled together: a source's own claim is very
often position-relative ("#1 DL", "#1 RB"), and a #1 DL claim and a #1 RB
claim pooled together would land on the same percentile despite representing
very different real dynasty value tiers — the same scarcity gap Draft
Sharks' own trade_value already reflects structurally (see above).

Draft Sharks' own Dynasty Rankings data feeding this score is itself
picked per-league by format automatically now (see the Notes section
below), rather than an arbitrary file-order accident, so the same player's
trade_value here reflects your actual league's real settings, not
whichever export happened to load last.

### Panel-vetted research becomes durable, not just one answer

The Beat Tracker and Contrarian both have live web search on every call
(and your own captioned reference material counts too) — when either
surfaces a specific, named-source claim about a player that the rest of
the panel, Contrarian very much included, doesn't dispute, the Moderator
can write it into two more repeatable lines in its structured block:

```
SOURCE FINDING: <player> | <source> | <the claim> | <a bare rank, ONLY if the source stated one>
SOURCE COMPARISON: <player A> | <player B> | > / < / ~ | <source> | <context> | <evidence>
```

Both persist to `data/baseline/` (`bot_research.json` / `bot_comparisons.json`,
global and git-tracked, append-only) via `bot_research.py`, and both are
fed back into every future debate as dated context. Only findings that
carry a real stated rank feed the composite score, at a low weight (below
even KTC's); a qualitative finding, and *every* comparison (a relative
claim has no absolute number to give it), stay reference-only forever —
`composite_impact` is stored explicitly on each entry rather than left for
a reader to infer. The reasoning: a handful of debate-surfaced comparisons
is nowhere near KeepTradeCut's millions of votes, so there's no real
signal yet to build an Elo-style relative model from — that stays a
possible future step once (if) real volume accumulates, not something
attempted today.

## Project layout

```
sleeper_client.py   Sleeper API wrapper: league discovery, rosters, scoring,
                     taxi, traded picks, cached player DB, snapshot caching.
data_merger.py       Draft Sharks PDF parsers (Dynasty Rankings + Free Agent
                     Finder + Trade Value Chart, auto-detected) + FantasyPros/
                     KeepTradeCut/ESPN parsers + CSV/JSON projection parser,
                     name/team/position matching onto Sleeper players,
                     projection-freshness tracking, and the composite score
                     (DataMerger.composite_player_score).
bot_research.py       Panel-vetted findings/comparisons from live bot research
                       or the user's own reference material — see "Panel-vetted
                       research becomes durable" above.
bot_config.py          Which provider/model/personality runs each of the four
                        personas, user-configurable with sensible defaults.
bot_benchmark.py       Side-by-side model comparison for a given role/question,
                        judged by a separate model call.
todo_log.py             Persistent per-league objectives the panel reads as
                         standing context on every question, can propose as
                         likely resolved or revise as new information comes in,
                         and the user can add manually or resolve/dismiss --
                         see "Persistent objectives" below.
pinned_messages.py      Manually pinned chat messages, retrieved automatically
                         when a later question looks related.
player_universe.py      Builds the full roster/free-agent player list a given
                         debate question can reason about, merging Sleeper's
                         roster data with whatever Draft Sharks/external data
                         is loaded.
league_prefs.py       Per-Sleeper-user league archive/reorder preferences.
league_format.py       Manual Best Ball / Chopped override + the strategic
                        guidance text injected into context for each.
attachments.py           Reference material (screenshots/articles) that isn't
                          structured Draft Sharks data — storage, captions,
                          and per-item global-vs-league(s) scoping.
llm_engine.py               Four-persona prompt routing across Claude / Gemini / ChatGPT,
                             plus the structured-verdict/TODO/SOURCE FINDING/
                             SOURCE COMPARISON parsers.
decision_log.py               Per-league record of every parsed Moderator verdict.

  -- Contextual Decision Matrix Engine (CDME) -- see "The Draft Engine" above --
draft_room.py                    CDME's base valuation math: universal_value, Team
                                  Acquisition Value (TAV), the scored board.
pick_synthesis.py                 CDME's contextual layer: necessity, positional cliff,
                                   survival/denial, decision_regime, narrow_candidates,
                                   and PickSnapshot -- CDME's frozen decision artifact.
draft_strategy.py                  Survival probability / opportunity-cost / denial-value
                                    analysis and positional-run detection, consumed by
                                    pick_synthesis.py.
draft_board_ui.py                    Pure formatting/serialization for the Draft Room's
                                      rendered board -- a translation layer over CDME's
                                      already-decided candidates, never a second ranking.
pick_debate.py                        "Debate My Pick" -- optional LLM interpretive
                                       escalation over a frozen PickSnapshot, never a
                                       replacement for CDME.
screen_context.py                      The shared ScreenContext contract every surface's
                                        Debate chip builds from (Draft Room, Trade
                                        Calculator, Matchup, Free Agents, League).
design_system.py                        Shared color/type/motion tokens + CSS reused by
                                         every surface's HTML/native styling.
trade_ledger_ui.py                       Pure formatting helpers for the Trade Calculator's
                                          roster-aware production UI.
depth_ratings.py                         Shared Strong/Average/Weak/None depth judgment
                                          used by Trade Calculator, League's Depth Map, and
                                          Matchup's readiness strip.
lineup_optimizer.py                      Exact-assignment (Hungarian) optimal starting
                                          lineup solver.
lineup_readiness.py                      Matchup's readiness-strip decomposition.
league_standings.py                      Real Sleeper win-loss records.
rookie_draft.py                          Rookie-draft-specific pick/value handling.
draft_simulation.py                      Deterministic multi-chair draft simulation
                                          harness -- runs CDME against itself across every
                                          seat, never a second draft engine.
draft_counterfactual.py                  Engine validation: recomputes the full board at
                                          each real pick to compare CDME's choice against
                                          pure BPA and market ADP. Measurement only.
roster_diagnostics.py                    Engine validation: decomposable per-team roster
                                          diagnostics off a completed simulated draft --
                                          deliberately no single aggregate power score.
option_set_analysis.py                   Engine validation: whether CDME's own narrowed
                                          candidate set ever excludes the true best
                                          available player.
run_draft_validation.py,
run_counterfactual_analysis.py,
run_option_set_analysis.py,
run_out_of_sample_validation.py          Drivers for the above -- not part of the app or
                                          the fast test suite; run by hand, write to
                                          data/draft_simulation_trials/ (gitignored).

app.py                         Streamlit dashboard + The Prytaneum.
update_and_run.ps1/.sh          Pulls latest code + deps, then launches the app.
test_*.py                       unittest coverage — no pytest dependency.
data/baseline/               Facts-only starting data, COMMITTED to git (not
                              gitignored) so a fresh clone isn't empty — see
                              "The baseline pool & the composite score" above.
data/baseline/rankings/, trade_value/   Draft Sharks baseline, by format.
data/baseline/external/<source>/        DynastyProcess/FantasyPros/KeepTradeCut/
                                         ESPN baseline CSVs + each source's own
                                         ATTRIBUTION.md.
data/baseline/bot_research.json          Panel-vetted single-player findings.
data/baseline/bot_comparisons.json       Panel-vetted player-vs-player comparisons.
data/sleeper_snapshots/  Cached league syncs (gitignored).
data/projections/_global/   Live-uploaded Dynasty Rankings / Trade Value Chart
                             exports, shared by every league (gitignored) --
                             supersedes data/baseline/ per-player, never
                             replaces it.
data/projections/<league_id>/  Free Agent Finder exports, one folder per league,
                                never shared (gitignored).
data/attachments/           Reference material + captions.json (gitignored).
data/chats/                 Per-league persisted debate history (gitignored).
data/decisions/              Per-league decision log, one JSON file per league (gitignored).
data/todos/                  Per-league persistent objectives, one JSON file per
                              league (gitignored) -- see "Persistent objectives" above.
data/pins/                   Per-league pinned message timestamps (gitignored).
data/bot_config.json        Which provider/model/personality runs each persona (gitignored).
data/benchmark_results.json Saved model-comparison benchmark runs (gitignored).
data/last_session.json      Last-used Sleeper username, for auto-restore on page refresh (gitignored).
data/league_prefs.json      Archived/reordered league ids per user (gitignored).
data/league_formats.json    Manual Best Ball/Chopped overrides (gitignored).
data/player_aliases.json    Manual name-matching overrides (gitignored).
.streamlit/config.toml      Dark theme — see "Notes" below for why this file matters.
```

## Known Limitations & Audit History

This project has gone through a structured internal audit cycle (an initial
build-and-validate pass, followed by a dedicated adversarial review pass
against the actual production code paths rather than prior conclusions)
before being frozen as a candidate baseline for independent review. This
section records what that process actually found — both the defect it
caught and fixed, and the real, deliberately unresolved limitations it
chose to document rather than change — so the distinction between
"measured and fixed," "measured and intentionally left alone," and
"known gap" stays visible rather than getting lost once the code settles.

**The eligibility-bonus unit defect (fixed).** `eligibility_bonus` — the
value a candidate's multi-position flexibility unlocks — is computed by
`lineup_optimizer.py` as a real assignment-problem answer, correctly
returned in whatever currency its caller supplies (Draft Sharks
`trade_value`, a 0–100 scale). It was being added directly into
`team_acquisition_value`, a sum whose other two terms live on a different,
non-interchangeable 0–100 scale (bpa-anchored `universal_value` and
`need_bonus`, which is capped at `NEED_BONUS_MAX` for exactly this reason).
Measured on the committed baseline, the two scales diverge by a mean of
11.7 points and up to 63.0 — and because `eligibility_bonus` was the one
contextual term with no equivalent cap, it could, on real data, produce a
bonus of 82.00 (6.8x `NEED_BONUS_MAX`) that overrode a 30+ point real
`universal_value` gap outright, reproduced in both a standard 1QB league
(WR/TE dual eligibility) and an IDP league (WR/DB). **This is fixed**: the
term is now rescaled into `universal_value`'s own bpa scale at the point of
consumption (`draft_room.py`, `TRADE_VALUE_SCALE_MAX`/
`ELIGIBILITY_BONUS_MAX`) and bounded equal to `NEED_BONUS_MAX`, on the
reasoning that both terms answer the same question — "how good is this
player for THIS roster" — and the architecture already fixes the bound for
that class. `lineup_optimizer.py` itself was intentionally left untouched
and stays general-purpose (its other consumer, `roster_diagnostics.py`,
genuinely wants raw `trade_value` units).

**The methodology lesson this defect exposed.** A large, passing test suite
can still fail to exercise an entire production dimension if its fixtures
don't reflect real data shapes. Every harness and test file in this project
built `players_db` with single-position `fantasy_positions`, for which
`eligibility_bonus` is exactly `0.0` by construction — so the defect above
was live in production (the real app uses Sleeper's own genuinely
multi-position `fantasy_positions`) while measuring as `0.0` across the
entire prior validation corpus, including every multi-chair simulation.
Permanent regression coverage now exists in `test_draft_room.py`'s
`EligibilityBonusWiringTests` — including a test that reproduces the exact
original defect scenario and was verified to actually fail under the
pre-fix math, not just pass by construction — but the general lesson is
preserved here as methodology: a fixture that's cheaper to build than real
data can silently make an entire code path untestable without ever
producing a failing test.

**Known, deliberately unresolved limitations:**

- **Half PPR has no dedicated rankings source.** The committed Draft Sharks
  baseline covers Standard, Full PPR, and their superflex/TE-premium
  variants, but no Half-PPR-specific export — `_rankings_format_match_score`
  in `data_merger.py` already documents this and picks Full PPR as the
  closest available approximation rather than leaving a Half-PPR league
  unscored. Measured directly: a Half-PPR and Full-PPR board are
  byte-identical today (`HalfPprIsAKnownDataLimitationTests` in
  `test_draft_room.py` pins this down as a regression-coupled fact, not
  just a note — if a real Half-PPR source is ever added, that test starts
  failing and is the signal to update this section too). The app now
  discloses this directly wherever Half PPR is shown or selectable, rather
  than silently returning Full-PPR numbers under a different label.
- **Dynasty injury discount is trajectory-aware, and that interaction is
  measured but not proven optimal.** In dynasty leagues, `risk_adj` (the
  injury-status discount) is scaled down for a player whose
  `time_horizon_adj` is genuinely positive — a health flag matters less
  against a long-horizon value case than against one built on already-
  realized production — floored so an injury never becomes irrelevant even
  for the strongest forward trajectory. This was promoted to production
  after real-data stress testing found it reorders only close, contextual
  comparisons and never overrides a large (25+ point) `universal_value`
  gap. What it has **not** been validated against is real dynasty outcome
  data — the interaction is a principled, bounded, documented calibration
  choice, not an empirically backtested one, the same honesty this project
  applies to its other unproven weighting constants.
- **KeepTradeCut consensus data has no freshness tracking.** Draft Sharks'
  own exports (Dynasty Rankings, Free Agent Finder) get the
  Fresh/Recent/Aging/Stale treatment described above; KTC-derived
  `consensus_rank`/`consensus_tier`/`reach_label` data, which can reach the
  optional LLM debate layer via `PickSnapshot`, currently does not. It
  never reaches CDME's own deterministic valuation or `pick_necessity`
  math — confirmed directly, `compute_draft_board` and
  `compute_pick_necessity` have no executable reference to any consensus
  field — so a stale KTC export cannot silently change a deterministic
  recommendation, only the market-consensus color an LLM debate sees.

## Notes

- **`.streamlit/config.toml` is what actually makes this a dark app.** The
  custom CSS injected in `app.py` only recolors the outer shell (`.stApp`,
  the badges, The Prytaneum's own message blocks) — every *native* widget (buttons, the
  roster dataframe, selectboxes, the segmented control) is themed by
  Streamlit itself, and without a `[theme]` section they render in
  Streamlit's default light theme regardless of what the custom CSS does.
  That mismatch was live in this app for a while — a dark shell around
  light-themed buttons and a white-canvas roster table — until actually
  running it in a browser and screenshotting it surfaced it; reading the
  code alone never would have. If you ever see a widget that looks
  "wrong" (wrong-colored buttons, a white table), check this file and the
  actual theme first before reaching for more CSS overrides.
  The same file also carries the rest of the visual identity: `Inter` for
  body text, `Space Grotesk` for headings, `JetBrains Mono` for The
  Prytaneum's transcripts and code, all loaded straight from Google Fonts via
  Streamlit's native `"name:url"` theme-font syntax — and a distinct,
  slightly darker `[theme.sidebar]` so the sidebar reads as its own panel
  instead of a visually-fused continuation of the main page.
- **Roster table**: sorted Starters → Bench → TAXI → IR (not roster order
  as Sleeper returns it), and slot/injury status are color-coded with the
  same emerald/gold/crimson palette as everything else, via a pandas
  `Styler` passed straight to `st.dataframe`.
- **Sleeper's own native projections**: alongside Draft Sharks, every league
  sync also pulls Sleeper's own per-stat-category weekly projection for each
  player (pass yards, receptions, rush TDs, etc.) and scores it under your
  league's *actual* `scoring_settings` — the same math Sleeper's own apps use
  to show a "proj" points column. This shows up as `sleeper_proj` in the
  roster table and in the debate context, as a second, independent
  quantitative source to weigh against Draft Sharks. **Caveat**: unlike the
  league/roster/user endpoints this project otherwise uses, that projections
  endpoint isn't part of Sleeper's *documented* public API — it's
  reverse-engineered from what Sleeper's own clients call internally, and
  could change shape or disappear without notice. Every call to it fails
  soft (the sidebar just shows "Sleeper Native Projections ❌" and everything
  else keeps working) — if it stops matching reality, tell me what broke and
  I'll fix the parsing. It's also a **single week's** number, not a season or
  multi-year total like Draft Sharks' — the Quant prompt is told this
  explicitly so it doesn't compare the two at face value.
- **Draft Sharks PDF format**: their rankings page prints as a two-column
  PDF (a numbers column, then a names column) that scrambles naive
  text-extraction order. `data_merger.py` reconstructs each row on a
  per-page basis rather than assuming the whole document reads top to
  bottom, and disambiguates Draft Sharks' first-initial-only names (e.g.
  "J Chase") against Sleeper's full names using team + position, since
  whole-string fuzzy matching alone under- and over-matches on that
  abbreviation. If Draft Sharks changes their page layout, this parser may
  need updating — send me a fresh export if matching quality drops.
- **Draft Sharks Free Agent Finder**: a structurally different export from
  Dynasty Rankings — different columns (3D Proj / 3D ROS / Ceiling / 3D
  Value+ instead of 1yr/3yr proj), different "rank" semantics (this-league
  contextual, not a pure dynasty overall rank), and a `Mine`/`Add`/`Drop`/
  `Lock` status tag Draft Sharks assigns per player. It's kept as its own
  table (`DataMerger.free_agents`) rather than merged into the rankings
  table, so the two don't clobber each other's meaning of "rank" or
  "value" — both get cross-matched onto your roster independently, and the
  Free Agents panel/context only ever reads from the free-agent table.
  IDP (LB/DL/DB) and K/DEF are supported since some leagues score them, but
  are only lightly tested against one real export — flag it if a position
  or team code doesn't parse right.
- Draft Sharks ships Dynasty Rankings as several distinct format-specific
  exports (PPR/standard × superflex/1QB × TE premium, plus separate PPR/
  superflex flavors for IDP), and the **committed baseline covers all of
  them** (`data/baseline/rankings/`) — you don't need to pick just one for
  the shared pool anymore. `DataMerger` reads each active league's real
  Sleeper scoring settings (superflex, PPR/half-PPR/standard, TE premium)
  and automatically prefers whichever file's own assumptions actually match
  that league whenever the same player appears in more than one, weighted
  by how much each axis actually swings a player's value (superflex
  heaviest, then TE premium, then scoring) — see `_detect_rankings_format`/
  `_rankings_format_match_score` in `data_merger.py`. **No dedicated
  Half-PPR export exists in that set today** — a Half-PPR league falls back
  to the closest available Full-PPR file, disclosed directly in the app;
  see "Known Limitations & Audit History" above. A live upload to the
  shared pool (`data/projections/_global/`) still works the same way and is
  still preferred over baseline per-player; loading more than one flavor
  there just isn't a footgun anymore. (Free Agent Finder is unaffected —
  it's already specific to your one league and stored separately.)
- Default models (`claude-sonnet-5`, `gemini-2.0-flash`, `gpt-4o`) are set
  in `.env.example` and overridable via `ANTHROPIC_MODEL` / `GEMINI_MODEL`
  / `OPENAI_MODEL` — point them at newer model releases as they become
  available. The Claude default is checked against Anthropic's own current
  model list; Gemini/OpenAI's aren't verified the same way here, so it's
  worth checking each provider's own docs if either seems to be erroring on
  a model-not-found.
- Sleeper's `/players/nfl` endpoint is large and rate-limit sensitive, so it's
  cached locally for 24 hours before being re-pulled.
