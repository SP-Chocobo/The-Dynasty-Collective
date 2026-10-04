/* ============================================================================================
   Gold Wyrm round 2 — shared model (revision after ADJUDICATION_R2). Everything is DERIVED from
   states.json; no engine field is invented. The model is rebuilt per state.

   Rules carried (round 1 ADJ + round 2 ADJ):
   - the board's order is team_acquisition_value; positional_forfeit informs and never ranks, and
     it is never the spatial order of anything;
   - the cross-position comparison names THREE real quantities: value now, what each position's
     best is worth at your next turn (position_next_turn_value), and the two-pick plan that adds
     them (verified: forfeit(P) == tav(P) − next_turn(P));
   - no tie is ever asserted (ambiguities is empty in every state); the margin is rendered;
   - a measured value is never rendered as an absence: measured zeros print 0.0 with their basis;
     the only hidden rows are rows identical across the names being compared;
   - basis labels are the engine's own words, verbatim;
   - depth_exposure prints a digit ONLY under depth_basis == "measured";
   - cliff word = cliff.tier 1:1; neighbour from the bpa order, named only when the gap reproduces;
     "below this board" is scoped to the measured order;
   - no name is read from a rail pick that has not happened (no > consumed);
   - the late negativity is attributed to displacement_adj (measured) in bright type, beside the
     number it explains.
   ============================================================================================ */
const STATE_KEYS = ["early", "mid", "late"];
const FORMAT_KEYS = Object.keys(DATA.formats);
const VOCAB = DATA.vocab;
/* flex eligibility comes from the engine's own map (player_universe.FLEX_SLOT_POSITIONS), never restated here */
const FLEX_MAP = VOCAB.FLEX_SLOT_POSITIONS;
const isFlexSlot = slot => Object.prototype.hasOwnProperty.call(FLEX_MAP, slot);
const eligible = (slot, pos) => slot === pos || (isFlexSlot(slot) && FLEX_MAP[slot].includes(pos));
const OFFENSE = new Set(["QB", "RB", "WR", "TE"]);                       // §14: tanks are offense-only, permanently
/* The one home for how defensive positions are LISTED (#126). Owner's call: DL, LB, DB,
   always and everywhere, independent of the order a league's own roster_positions happens
   to use -- HEAVY_IDP read correctly only by accident of its slot list, and the compound
   door's own label and demand line were rendering them alphabetically (DB / DL / LB). */
const IDP_ORDER = ["DL", "LB", "DB"];
const IDP = new Set(IDP_ORDER);
const byIdp = ps => ps.slice().sort((a, b) => IDP_ORDER.indexOf(a) - IDP_ORDER.indexOf(b));
const num = x => typeof x === "number" && isFinite(x);
const f1  = x => num(x) ? (Math.abs(x) < 0.05 ? "0.0" : x.toFixed(1).replace("-", "−")) : "—";
const sgn = x => num(x) ? (Math.abs(x) < 0.05 ? "±0.0" : (x > 0 ? "+" : "−") + Math.abs(x).toFixed(1)) : "—";
const pad = n => String(n).padStart(2, "0");
const pc  = p => `var(--${(p || "k").toLowerCase()})`;
const esc = s => String(s == null ? "" : s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/"/g, "&quot;");
const POS  = {QB:"quarterback", RB:"running back", WR:"receiver", TE:"tight end", K:"kicker", DEF:"defense", DL:"defensive lineman", LB:"linebacker", DB:"defensive back", IDP:"defender"};
const PLUR = {QB:"quarterbacks", RB:"running backs", WR:"receivers", TE:"tight ends", K:"kickers", DEF:"defenses", DL:"defensive linemen", LB:"linebackers", DB:"defensive backs", IDP:"defenders"};
const TIER_WORD = {HIGH:"a sharp drop", MEDIUM:"a moderate drop", LOW:"no cliff"};
const ORD = ["", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth"];
const posOfPlayer = p => (p && (p.pos || p.position)) || "";
const nameTip = (p, extra) => p && p.name
  ? `${p.name}\n${[posOfPlayer(p), p.team, extra].filter(Boolean).join(" · ")}`
  : "";
const slotTag = (slot, p) => (p && isFlexSlot(slot) && posOfPlayer(p)) ? `${slot}·${posOfPlayer(p)}` : slot;
const tipAttr = t => t ? ` data-tip="${esc(t)}"` : "";
const ordinal = n => n + (["th","st","nd","rd"][(n % 100 > 10 && n % 100 < 14) ? 0 : (n % 10 < 4 ? n % 10 : 0)]);
/* engine labels, verbatim, read from the engine at build time (lineup_optimizer.EXPOSURE_BASIS_LABELS,
   DISPLACEMENT_BASIS_LABELS, draft_strategy.DENIAL_BASIS_LABELS, draft_room.SLOT_SHARE_LABELS). */
const DEPTH_LABEL = VOCAB.EXPOSURE, DISP_LABEL = VOCAB.DISPLACEMENT, DENIAL_LABEL = VOCAB.DENIAL, SHARE_LABEL = VOCAB.SLOT_SHARE;

/* roster: greedy fill of the league's slots from a list of picks */
function slotRoster(picks, slots){
  const left = picks.slice();
  return slots.map(slot => {
    let i = left.findIndex(p => p.pos === slot);
    if (i < 0 && isFlexSlot(slot)) i = left.findIndex(p => eligible(slot, p.pos));
    if (i < 0 && slot === "BN")   i = left.length ? 0 : -1;
    return {slot, p: i < 0 ? null : left.splice(i, 1)[0]};
  });
}

function buildModel(key, fmt){
  fmt = fmt || FORMAT_KEYS[0];
  const F = DATA.formats[fmt], S = F.states[key], RAIL = F.rail;
  const C = S.candidates.slice().sort((a, b) => a.rank - b.rank);
  const M = {key, fmt, F, S, C, RAIL};

  /* ---- turn geometry, read off the rail (pick_order) ---- */
  M.NOW_NO = S.consumed + 1;
  M.KNOWN = RAIL.filter(p => p.no <= S.consumed);
  const MINE = RAIL.filter(p => p.mine).map(p => p.no);
  M.NEXT_NO = MINE.find(n => n > M.NOW_NO) || null;
  M.PREV_NO = [...MINE].reverse().find(n => n < M.NOW_NO) || null;
  M.BETWEEN = M.NEXT_NO ? RAIL.filter(p => p.no > M.NOW_NO && p.no < M.NEXT_NO) : [];
  console.assert(M.BETWEEN.length === S.intervening, "rail span and intervening_picks disagree");
  M.NOW_PICK = RAIL.find(p => p.no === M.NOW_NO);
  M.NEXT_PICK = M.NEXT_NO ? RAIL.find(p => p.no === M.NEXT_NO) : null;
  M.AFTER_ME = M.BETWEEN[0] || null;
  M.LAST = M.KNOWN[M.KNOWN.length - 1] || null;
  M.coord = p => `${p.rnd}.${pad(p.inr)}`;

/* #187 absence contract, on the card: a row with no season projection must not render as a
   measured zero. Math.round(null) is 0, and "0 pts" beside a name is a claim the engine never
   made. #204's companion rule applies too: a row priced on a different arm from the rest of the
   board is not commensurable with it, and the board was saying nothing at all about that. */
M.PRICED_ARM = "points_vor_sleeper_season_scored";
M.hasPts = c => c.projected_points !== null && c.projected_points !== undefined;
M.pts = (c, word) => M.hasPts(c) ? `${Math.round(c.projected_points)} ${word || "pts"}` : "no season projection";
M.offArm = c => !!c.bpa_source && c.bpa_source !== M.PRICED_ARM;
M.armMark = c => M.offArm(c) ? ` <span class="arm" data-tip="Priced on a different arm\nThis name carries no season projection, so the engine fell back to ${c.bpa_source.replace(/_/g, " ")}. Every other name here is priced on ${M.PRICED_ARM.replace(/_/g, " ")}. The two are not the same instrument, so this row's value is not strictly comparable with the rest of the list.">off-arm</span>` : "";


/* A compound door's depth list, which cannot be the top N by value.
   IDP_FLEX is a SHARED slot, and shared_slot_alternatives prices a shared slot at the MAX
   replacement level over the positions it admits -- so every position but the max one carries a
   per-position displacement constant (measured in LIGHT_IDP: LB 0.00, DB -32.81, DL -42.99, zero
   variance within a position). That constant is ~3x the whole within-position merit spread, so
   ordering by value alone fills a three-position door with one position's names: the Defenders
   door showed four linebackers, and a defensive back with a HIGHER bpa than the leader sat 21
   rows down in the drawer. The engine is right -- those are the slot's real alternatives and
   that is their real cost. What it does not owe the reader is the impression that DL and DB do
   not exist. So a compound door spends its rows on one name per position it admits, plus the
   next name at the leader's own, and lets the gap column say what each one costs. */
M.doorDepth = (d, best, list) => {
  if (!d.compound) return list.slice(1, 4);
  const seen = new Set([best.player_id]), out = [];
  const take = c => { if (c && !seen.has(c.player_id)) { seen.add(c.player_id); out.push(c); } };
  take(list.find(c => c.position === best.position && !seen.has(c.player_id)));
  d.positions.forEach(p => { if (p !== best.position) take(list.find(c => c.position === p && !seen.has(c.player_id))); });
  return out.sort((a, b) => b.team_acquisition_value - a.team_acquisition_value);
};

  M.nextLabel = M.NEXT_PICK ? M.coord(M.NEXT_PICK) : "—";
  const SEAT_TURNS = {}; M.BETWEEN.forEach(p => SEAT_TURNS[p.seat] = (SEAT_TURNS[p.seat] || 0) + 1);
  M.seatsText = () => {
    const seats = Object.keys(SEAT_TURNS), twice = seats.filter(s => SEAT_TURNS[s] > 1), once = seats.filter(s => SEAT_TURNS[s] === 1), parts = [];
    if (twice.length) parts.push(`rosters ${twice.join(", ")} each pick twice`);
    if (once.length) parts.push(`roster${once.length > 1 ? "s" : ""} ${once.join(", ")} pick${once.length > 1 ? "" : "s"} once`);
    return parts.join("; ");
  };
  M.waitShort = () => `Next turn <b>${M.nextLabel}</b> (#${M.NEXT_NO}) · <b>${S.intervening} picks</b> away`;
  M.waitText = () => `You pick again at <b>${M.nextLabel}</b> (#${M.NEXT_NO}), after <b>${S.intervening} picks</b> — ${M.seatsText()}.`;
  /* §1: who is on the clock is never ambiguous, with or without a rail */
  M.clockShort = () => `next up: <b>Roster ${M.AFTER_ME ? M.AFTER_ME.seat : "—"}</b>${M.LAST ? ` · last taken: <b>${M.short(M.LAST.name)}</b> (Roster ${M.LAST.seat})` : ""}`;
  M.clockText = () => `On the clock: <b>you</b> (Roster ${S.seat}) · next up: Roster ${M.AFTER_ME ? M.AFTER_ME.seat : "—"}${M.LAST ? ` · last taken: <b>${M.short(M.LAST.name)}</b> by Roster ${M.LAST.seat}` : " · first pick of the draft"}`;

  /* ---- names: the family name is the collision key ("Brown" for Amon-Ra St. Brown, A.J. Brown
          and Chase Brown); a collision keeps the particle: A. St. Brown / A. Brown / C. Brown; if
          initial + surname still collides, the full name is used ---- */
  const parts = n => { const w = (n || "").split(" "); const particle = w.length >= 3 && /^(St\.|Van|De|Da|Di|La|Le|Del|Von)$/i.test(w[w.length - 2]);
    return {first: w[0], family: w[w.length - 1], surname: particle ? w.slice(-2).join(" ") : w[w.length - 1], multi: w.length > 1}; };
  const FAM = {}, INIT = {};
  new Set([...M.KNOWN.map(p => p.name), ...C.map(c => c.name)]).forEach(n => { const q = parts(n); FAM[q.family] = (FAM[q.family] || 0) + 1; const k = q.first[0] + ". " + q.surname; INIT[k] = (INIT[k] || 0) + 1; });
  M.short = n => { const q = parts(n); if (!q.multi || FAM[q.family] <= 1) return q.surname; const k = q.first[0] + ". " + q.surname; return INIT[k] <= 1 ? k : n; };
  const short = M.short;

  /* ---- my roster ---- */
  M.ROSTER = slotRoster(S.myPicks, S.slots);
  M.STARTERS = M.ROSTER.filter(r => r.slot !== "BN");
  M.heldAt = pos => S.myPicks.filter(p => p.pos === pos);
  M.openAt = pos => M.STARTERS.filter(r => r.slot === pos && !r.p).length;
  M.openFlexFor = pos => M.STARTERS.find(r => !r.p && r.slot !== pos && isFlexSlot(r.slot) && eligible(r.slot, pos)) || null;
  M.startersFull = M.STARTERS.every(r => r.p);
  M.benchFilled = M.ROSTER.filter(r => r.slot === "BN" && r.p).length;
  M.benchTotal = M.ROSTER.filter(r => r.slot === "BN").length;
  M.slotFor = c => {
    const held = M.heldAt(c.position), want = M.STARTERS.filter(r => r.slot === c.position).length;
    if (M.openAt(c.position) > 0) return held.length === 0 ? {kind:"vacant", slot:want > 1 ? c.position + "1" : c.position} : {kind:"second", slot:c.position + (held.length + 1), beside:held[0]};
    const fx = M.openFlexFor(c.position); if (fx) return {kind:"flex", slot:fx.slot, holder:held[0] || null};
    return {kind:"bench", slot:"BN", holder:held[0] || null};
  };
  M.slotPhrase = c => { const s = M.slotFor(c);
    if (s.kind === "vacant") return `starts at <b>${s.slot}</b> — you hold no ${POS[c.position]}`;
    if (s.kind === "second") return `starts at <b>${s.slot}</b> beside ${short(s.beside.name)}`;
    if (s.kind === "flex")   return `starts at <b>${s.slot}</b>${s.holder ? ` — ${short(s.holder.name)} holds ${c.position}` : ""}`;
    return `<b>bench</b> — your starting slots are full`; };
  M.slotShort = c => { const s = M.slotFor(c); return s.kind === "bench" ? "bench" : s.slot; };
  M.rosterStrip = (c, vertical) => {
    let lit = false; const s = c ? M.slotFor(c) : null;
    const cells = M.STARTERS.map(r => {
      const fills = c && !lit && !r.p && s.kind !== "bench" && r.slot === s.slot; if (fills) lit = true;
      const need = !r.p && !isFlexSlot(r.slot) && M.heldAt(r.slot).length === 0;
      const label = r.p ? short(r.p.name) : fills ? "← " + short(c.name) : "open";
      if (vertical) return `<div class="slot ${r.p ? "" : "open"} ${need ? "need" : ""} ${fills ? "fills" : ""}"><span class="s">${slotTag(r.slot, r.p)}</span><span class="p"${tipAttr(r.p ? r.p.name : "")}>${label}</span></div>`;
      return `<span class="slotc ${r.p ? "" : "open"} ${need ? "need" : ""} ${fills ? "fills" : ""}"${tipAttr(r.p ? r.p.name : "")}><span class="s">${slotTag(r.slot, r.p)}</span>${label}</span>`;
    });
    /* A bench name is still a name. Every starting slot got its own chip while six bench slots
       were compounded into "2 of 6", so the players you had actually drafted were the only ones
       on this strip with no name at all. Names get chips, like starters do; only the EMPTY
       remainder stays a count, because an empty slot has nothing to say. */
    /* A bench name is still a name, so the strip says the names -- but in ONE chip, not one
       chip per bench slot. Giving each bench slot its own chip pushed this strip onto a second
       line in the 13-starter formats, and the 30px it took came straight out of the open door's
       card region below, which collapsed to zero cards with its scroll affordance off-screen.
       The strip is one line; the roster sheet is where a roster gets room. Only the EMPTY
       remainder stays a count, because an empty slot has nothing to say. */
    const benchHeld = M.ROSTER.filter(r => r.slot === "BN" && r.p);
    const toBench = !!(c && s.kind === "bench");
    const stillOpen = M.benchTotal - M.benchFilled - (toBench ? 1 : 0);
    const parts = benchHeld.map(r => short(r.p.name));
    if (toBench) parts.push("← " + short(c.name));
    if (stillOpen > 0) parts.push(`${stillOpen} open`);
    const bnLabel = parts.join(" · ");
    const bnTip = benchHeld.length ? benchHeld.map(r => r.p.name).join(", ") : "";
    const bnCls = (benchHeld.length ? "" : "open ") + (toBench ? "fills" : "");
    /* The two containers have room in different directions, so the bench takes a different
       shape in each. The horizontal strip is ONE line and cannot grow sideways, so it gets one
       chip. The vertical roster column is a column -- it has room downward and a fixed width
       with an ellipsis, where that same one-line label was being cut off -- so it gets a row
       per name. Same facts, laid out the way each container can actually hold them. */
    const bnCells = vertical
      ? parts.map((label, i) => `<div class="slot ${i < benchHeld.length ? "" : "open"} ${toBench && label.startsWith("←") ? "fills" : ""}"><span class="s">BN</span><span class="p"${tipAttr(i < benchHeld.length ? benchHeld[i].p.name : "")}>${label}</span></div>`).join("")
      : `<span class="slotc ${bnCls}"${tipAttr(bnTip)}><span class="s">BN</span>${bnLabel}</span>`;
    return cells.join("") + bnCells;
  };

  /* ---- positions, board order (tav) and measured order (bpa) ---- */
  /* every position the league's own slots can start: named slots, plus each flex slot's eligible
     positions (from the engine's map). Doors: a named position is its own door; a flex-only offensive
     position is its own door (TE always, FLEX_AND_POSITION_DOORS §2); flex-only IDP compounds into one. */
  const NAMED_RAW = [...new Set(S.slots.filter(sl => sl !== "BN" && !isFlexSlot(sl)))];
  // offence keeps the league's own slot order; defence is always listed in IDP_ORDER
  const NAMED = NAMED_RAW.filter(p => !IDP.has(p)).concat(byIdp(NAMED_RAW.filter(p => IDP.has(p))));
  const FLEX_ONLY = [...new Set(S.slots.filter(isFlexSlot).flatMap(sl => FLEX_MAP[sl]))].filter(p => !NAMED.includes(p));
  const FLEX_IDP = byIdp(FLEX_ONLY.filter(p => IDP.has(p)));
  M.LINEUP_ORDER = NAMED.concat(FLEX_ONLY.filter(p => !IDP.has(p))).concat(FLEX_IDP);
  M.DOORS = NAMED.map(p => ({key:p, label:POS[p], positions:[p], compound:false}))
    .concat(FLEX_ONLY.filter(p => !IDP.has(p)).map(p => ({key:p, label:POS[p], positions:[p], compound:false})));
  const idpFlexOnly = FLEX_IDP;
  if (idpFlexOnly.length) M.DOORS.push({key:"IDP", label:"defense (" + idpFlexOnly.join(" / ") + ")", positions:idpFlexOnly, compound:true});
  M.doorOf = pos => M.DOORS.find(d => d.positions.includes(pos)) || null;
  M.POSITIONS = M.LINEUP_ORDER.filter(p => C.some(c => c.position === p));
  M.DEMAND = S.demand || {}; M.SHARE_BASIS = S.slot_share_basis || null;
  M.shareLabel = () => M.SHARE_BASIS ? (SHARE_LABEL[M.SHARE_BASIS] || M.SHARE_BASIS) : "basis not reported";
  M.demandText = pos => num(M.DEMAND[pos]) ? `demand <b>${M.DEMAND[pos].toFixed(2)}</b>/team · <i class="basis">${M.shareLabel()}</i>` : "";
  M.atPos = pos => C.filter(c => c.position === pos);
  M.atPosBpa = pos => M.atPos(pos).slice().sort((a, b) => b.bpa - a.bpa);
  M.best = pos => M.atPos(pos)[0] || null;
  M.posRank = c => M.atPos(c.position).findIndex(x => x.player_id === c.player_id);
  M.FORFEIT = {}; M.NEXTV = {};
  C.forEach(c => { if (num(c.positional_forfeit)) M.FORFEIT[c.position] = c.positional_forfeit; if (num(c.position_next_turn_value)) M.NEXTV[c.position] = c.position_next_turn_value; });
  M.POS_BY_COST = Object.keys(M.FORFEIT).sort((a, b) => M.FORFEIT[b] - M.FORFEIT[a]);
  /* superlative scoped to the positions the board has names at (ADJ R2 §4) */
  M.costWord = pos => { const n = M.POS_BY_COST.length; if (n < 2) return "";
    const which = pos === M.POS_BY_COST[0] ? "most" : pos === M.POS_BY_COST[n - 1] ? "least" : null; if (!which) return "";
    return `${which} of ${n} measured`; };
  M.LEADER = C[0];
  M.get = id => C.find(c => c.player_id === id);
  M.VALUE_ORDER_POS = []; C.forEach(c => { if (!M.VALUE_ORDER_POS.includes(c.position)) M.VALUE_ORDER_POS.push(c.position); });
  /* doors in the board's value order (a door's rank is its best name's rank); doors with no name last, in lineup order */
  M.doorBest = d => C.find(c => d.positions.includes(c.position)) || null;
  /* #30: K and DEF price against a WEEKLY WIRE STREAMER, not a season hold -- a categorically
     different alternative, so they are held out of the surfaced doors by default. The list is the
     engine's (STREAMABLE_POSITIONS), never restated here. */
  M.STREAMABLE = new Set(DATA.vocab.STREAMABLE_POSITIONS || []);
  M.isStreamDoor = d => d.positions.length > 0 && d.positions.every(p => M.STREAMABLE.has(p));
  M.DOOR_ORDER = M.DOORS.filter(d => M.doorBest(d)).sort((a, b) => M.doorBest(a).rank - M.doorBest(b).rank).concat(M.DOORS.filter(d => !M.doorBest(d)));

  /* ---- the cliff ---- */
  M.cliffNext = c => {
    const l = M.atPosBpa(c.position), i = l.findIndex(x => x.player_id === c.player_id), n = l[i + 1];
    if (!n || !c.positional_cliff || !num(c.positional_cliff.gap)) return null;
    return Math.abs((c.bpa - n.bpa) - c.positional_cliff.gap) < 0.02 ? n : null;
  };
  M.tierWord = c => TIER_WORD[(c.positional_cliff || {}).tier] || "no drop measured";
  M.cliffTo = c => { const n = M.cliffNext(c); return n ? `to ${short(n.name)}` : `to a player off this board (measured order)`; };
  M.cliffText = c => { const k = c.positional_cliff; if (!k || !num(k.gap)) return "no drop measured behind him";
    return `${M.tierWord(c)} behind him (${f1(k.gap)}, ${M.cliffTo(c)})`; };
  M.adjacentMeasured = (a, b) => { const l = M.atPosBpa(a.position); const ia = l.findIndex(x => x.player_id === a.player_id), ib = l.findIndex(x => x.player_id === b.player_id); return Math.abs(ia - ib) === 1 ? (ia < ib ? a : b) : null; };

  /* ---- depth: a digit only when measured; otherwise the engine's own label ---- */
  M.depth = c => c.depth_basis === "measured" ? {n:f1(c.depth_exposure), why:DEPTH_LABEL.measured} : {n:null, why:DEPTH_LABEL[c.depth_basis] || `not measured -- ${String(c.depth_basis).replace(/_/g, " ")}`};
  /* ---- displacement: the late board's negativity, named (ADJ R2 §1) ---- */
  M.displaced = c => c.displacement_basis === "measured" && num(c.displacement_adj) && Math.abs(c.displacement_adj) >= 0.05;
  M.dispSentence = c => { if (!M.displaced(c)) return "";
    const rest = c.team_acquisition_value - c.displacement_adj;
    return `<span class="disp"><b>${f1(c.displacement_adj)}</b> of this is the displacement of a starting slot you have already filled — measured against your own starters. The player himself: <b>${f1(rest)}</b>.</span>`; };
  M.dispShort = c => M.displaced(c) ? `<span class="disp">${f1(c.displacement_adj)} is filled-slot displacement (measured) · himself ${f1(c.team_acquisition_value - c.displacement_adj)}</span>` : "";
  /* availability: the engine carried the designation and did not charge it */
  /* §14 tank, per state: the engine's latest sample at or before this pick, shown as of that pick
     (the rail reproduces the engine's drain only through #80, so the client never drains it). No bands. */
  const G = (DATA.gauge && DATA.gauge[fmt]) || null;
  M.tankable = pos => OFFENSE.has(pos);
  M.tank = pos => { if (!G || !num(G.opening[pos]) || !OFFENSE.has(pos)) return null;
    const base = G.history.filter(h => h.at <= S.consumed).sort((a, b) => b.at - a.at)[0];
    const N = G.opening[pos], left = base.left[pos], starters = G.starterRank[pos];
    const startersLeft = Math.max(0, left - (N - starters));
    return {N, left, starters, startersLeft, pctLeft: Math.round(100 * left / N), sampleAt: base.at, coverage: G.coverage[pos], rows: G.rowsOnBoard[pos]}; };
  /* waiting on a position: who you get, when, what it costs — in that order */
  M.waitLine = (pos, short) => num(M.FORFEIT[pos]) ? `If you wait, the best ${short ? "" : POS[pos] + " "}left at <b>#${M.NEXT_NO}</b> is worth about <b>${f1(M.NEXTV[pos])}</b> — <b>${f1(M.FORFEIT[pos])}</b> less than taking one now.` : `No next-turn value is measured for ${PLUR[pos] || pos} on this board.`;
  M.DEAREST = M.POS_BY_COST[0] || null;
  M.avail = c => c.injury_status ? `<i class="inj">${c.injury_status}</i> <span class="note">not charged</span>` : "";

  /* ============================================================================================
     compare(a, b): across positions, three real quantities — value now (the board's order), what
     each position's best is worth at your next turn, and the two-pick plan (now + next). Verified
     on this payload: forfeit(P) == tav(best at P) − next_turn(P), so plan edge == forfeit edge.
     Within a position the next-turn value is identical and says nothing; the relation rests on
     value, the measured drop, horizon, designation and depth.
     ============================================================================================ */
  M.compare = (a, b) => {
    const r = {a, b, same:a.position === b.position, dv:a.team_acquisition_value - b.team_acquisition_value};
    r.valueLeader = r.dv >= 0 ? a : b;
    if (!r.same) {
      r.hasNext = num(M.NEXTV[a.position]) && num(M.NEXTV[b.position]);
      if (r.hasNext) {
        r.aThenB = a.team_acquisition_value + M.NEXTV[b.position];   // A now, B's position at my next turn
        r.bThenA = b.team_acquisition_value + M.NEXTV[a.position];
        r.planEdge = r.aThenB - r.bThenA;                               // > 0 favours A first
        r.nextGap = M.NEXTV[a.position] - M.NEXTV[b.position];          // what remains at A's position vs B's at my next turn
        r.planLeader = r.planEdge >= 0 ? a : b;
      }
    } else {
      r.ahead = M.adjacentMeasured(a, b);
      r.dh = a.time_horizon_adj - b.time_horizon_adj;
      const da = M.depth(a), db = M.depth(b); r.depthDiff = da.n && db.n && da.n !== db.n ? [da.n, db.n] : null;
    }
    return r;
  };
  /* the sentences, from the relation. A = subject, B = the other. */
  M.whyLines = (a, b) => {
    const r = M.compare(a, b), A = `<b>${short(a.name)}</b>`, B = `<b>${short(b.name)}</b>`, out = [];
    const lead = r.dv >= 0 ? A : B, trail = r.dv >= 0 ? B : A;
    out.push(`${lead} is <b>${f1(Math.abs(r.dv))}</b> ahead of ${trail} in value to your roster now — the board's order.`);
    if (!r.same) {
      if (r.hasNext) out.push(`Wait on ${b.position} and the best ${POS[b.position]} left at your next turn is worth <b>${f1(M.NEXTV[b.position])}</b>; wait on ${a.position} and the best ${POS[a.position]} left is worth <b>${f1(M.NEXTV[a.position])}</b>. Both picks together: <b>${short(r.planLeader.name)} now</b> is the better two-pick plan by <b>${f1(Math.abs(r.planEdge))}</b>.`);
      else out.push(`No next-turn value is measured for ${!num(M.NEXTV[a.position]) ? a.position : b.position} on this board.`);
    } else {
      if (r.ahead) out.push(`They are neighbours in the order the drop was measured; between them the engine finds <b>${M.tierWord(r.ahead)}</b> (${f1(r.ahead.positional_cliff.gap)}).`);
      else out.push(`Behind ${A}: ${M.cliffText(a)}. Behind ${B}: ${M.cliffText(b)}.`);
      if (f1(a.time_horizon_adj) !== f1(b.time_horizon_adj)) out.push(`Dynasty horizon: ${sgn(a.time_horizon_adj)} on ${A}, ${sgn(b.time_horizon_adj)} on ${B}.`);
      if ((a.injury_status || null) !== (b.injury_status || null)) out.push(`${a.injury_status ? `${A} is listed ${a.injury_status}` : `${A} carries no designation`}; ${b.injury_status ? `${B} is listed ${b.injury_status}` : `${B} none`}. The designation is carried and not charged.`);
      if (r.depthDiff) out.push(`Depth insurance ${r.depthDiff[0]} against ${r.depthDiff[1]}.`);
    }
    return out;
  };
  /* a subject's own drop, said once */
  M.ownLine = c => `Behind him: ${M.tierWord(c)} (${f1(c.positional_cliff.gap)}, ${M.cliffTo(c)}).`;
  M.comparatorFor = c => c.player_id === M.LEADER.player_id ? (C[1] || null) : M.LEADER;

  /* ---- what else: the board's leader (if not him), the best at every other position, the next
          at his own position on the board ---- */
  M.alternatives = (c, max) => {
    const ids = new Set([c.player_id]), out = [];
    const push = x => { if (x && !ids.has(x.player_id)) { ids.add(x.player_id); out.push(x); } };
    push(M.LEADER);
    M.POSITIONS.filter(p => p !== c.position).forEach(p => push(M.best(p)));
    const own = M.atPos(c.position); push(own[M.posRank(c) + 1] || null);
    if (M.posRank(c) > 0) push(own[0]);
    out.sort((x, y) => y.team_acquisition_value - x.team_acquisition_value);
    return out.slice(0, max || 3);
  };
  /* the cost of taking b instead of a — three cells across positions (now · next turn · plan),
     two within (now · the drop between them) */
  M.costOf = (b, a) => {
    const r = M.compare(b, a), cells = [];
    cells.push({k:"now", v:sgn(r.dv)});
    if (!r.same) {
      if (r.hasNext) { cells.push({k:`at #${M.NEXT_NO}`, v:sgn(r.nextGap)}); cells.push({k:"both picks", v:sgn(r.planEdge), fav:r.planEdge > 0}); }
      else cells.push({k:`at #${M.NEXT_NO}`, v:"not measured"});
    } else {
      if (r.ahead) cells.push({k:"between them", v:`${M.tierWord(r.ahead)} · ${f1(r.ahead.positional_cliff.gap)}`});
      else { const l = M.atPosBpa(a.position); const n = Math.abs(l.findIndex(x => x.player_id === a.player_id) - l.findIndex(x => x.player_id === b.player_id)); cells.push({k:"measured order", v:`${n} places apart`}); }
    }
    return cells;
  };
  M.costHTML = (b, a) => M.costOf(b, a).map(c => `<span class="cc ${c.fav ? "fav" : ""}"><span class="ck">${c.k}</span><span class="cv">${c.v}</span></span>`).join("");
  M.costKey = subj => `<b>now</b> = value against ${short(subj.name)} today, the board's order · <b>at #${M.NEXT_NO}</b> = what his position leaves at your next turn against what ${subj.position} leaves · <b>both picks</b> = the two added together, him first`;

  /* ---- the engine's working (hidden until asked): every number with its kind; measured zeros print ---- */
  const KIND = {measured:"measured", count:"a count", withheld:"withheld", unmeasured:"not measured", not_charged:"not charged"};
  M.working = c => {
    const d = M.depth(c), rows = [
      {l:"Value to your roster", v:f1(c.team_acquisition_value), b:"what the board is ordered by", k:"measured"},
      {l:"Value to any roster", v:f1(c.universal_value), b:"before your roster is considered", k:"measured"},
      {l:"Credit for your open slot", v:f1(c.need_bonus), b:"what your lineup is missing where he would start", k:"measured"},
      d.n ? {l:"Depth insurance", v:d.n, b:d.why, k:"measured"} : {l:"Depth insurance", v:"—", b:d.why, k:c.depth_basis === "no_surplus" ? "not_charged" : "unmeasured"},
      c.displacement_basis === "measured" ? {l:"Lineup displacement", v:f1(c.displacement_adj), b:DISP_LABEL.measured, k:"measured"} : {l:"Lineup displacement", v:"—", b:DISP_LABEL[c.displacement_basis] || "not measured", k:"unmeasured"},
      {l:`Best ${POS[c.position]} left at your next turn`, v:num(c.position_next_turn_value) ? f1(c.position_next_turn_value) : "—", b:`what the position is expected to offer at #${M.NEXT_NO} if you wait on it`, k:num(c.position_next_turn_value) ? "measured" : "unmeasured"},
      {l:`Cost of waiting on ${c.position}`, v:num(c.positional_forfeit) ? f1(c.positional_forfeit) : "—", b:"the best now minus the best left at your next turn — an aid beside the rank, never what ranks", k:num(c.positional_forfeit) ? "measured" : "unmeasured"},
      {l:"Dynasty horizon", v:sgn(c.time_horizon_adj), b:"the age / experience term inside his value", k:"measured"},
      {l:"Projected season points", v:f1(c.projected_points), b:M.hasPts(c) ? "season fantasy points under this league's scoring — a different unit from the value rows" : `no season projection exists for this name, so the engine priced it on ${(c.bpa_source||"another arm").replace(/_/g," ")} instead — a different instrument from every other row here`, k:M.hasPts(c) ? "measured" : "not_priced"},
      c.risk_basis === "designation_not_priced" ? {l:"Availability", v:c.injury_status || "no designation", b:"the designation is carried and not charged against his value — this is not “no risk”", k:"not_charged"} : {l:"Availability term", v:f1(c.risk_adj), b:String(c.risk_basis).replace(/_/g, " "), k:"measured"},
      {l:"Drop behind him", v:c.positional_cliff ? `${c.positional_cliff.tier} · ${f1(c.positional_cliff.gap)}` : "—", b:`the engine's tier and the raw gap to the next ${POS[c.position]} in the order it was measured (${M.cliffNext(c) ? short(M.cliffNext(c).name) : "a player not on this board"})`, k:"measured"},
      c.denial_basis === "measured" ? {l:"Kept from a rival", v:f1(c.denial_value) + (c.denial_team ? ` (roster ${c.denial_team})` : ""), b:DENIAL_LABEL.measured + (num(c.denial_value) && Math.abs(c.denial_value) < 0.05 ? " — a zero is a measurement" : ""), k:"measured"} : {l:"Kept from a rival", v:"—", b:DENIAL_LABEL[c.denial_basis] || "not measured", k:"unmeasured"},
      {l:"Picks until your next turn", v:String(S.intervening), b:"a count read off the pick order; shown in place of the survival estimate while that is withheld", k:"count"},
    ];
    (S.withheld || []).forEach(w => rows.push({l:({survival_probability:"Chance he lasts to your next turn", opportunity_cost:"Cost of waiting on him", expected_value_of_waiting:"Expected value if you wait"})[w] || w, v:"withheld", b:"computed, then held back: it failed calibration against real drafts", k:"withheld"}));
    return rows.map(e => `<div class="ev ${e.k}"><span class="el">${e.l}</span><span class="en">${e.v}</span><span class="eb"><i class="ek">${KIND[e.k]}</i> ${e.b}</span></div>`).join("");
  };

  /* ---- atoms ---- */
  M.face = (c, size) => { const init = (c.name || "").split(" ").map(w => w[0]).slice(0, 2).join("");
    const img = location.protocol === "file:" ? "" : `<img alt="" src="https://sleepercdn.com/content/nfl/players/${c.player_id}.jpg" onerror="this.remove()">`;
    return `<span class="face ${size || ""}" data-pos="${c.position}" style="--pc:${pc(c.position)}" data-tip="${esc(c.name)}">${init}${img}</span>`; };
  M.pill = p => `<span class="pill" style="background:${pc(p)}">${p}</span>`;
  M.copyBtn = c => `<button class="copy" data-copy="${esc(c.name)}" data-tip="Copy the name to carry to Sleeper">⧉ copy name</button>`;
  M.whoSub = c => `${M.pill(c.position)}<span>${c.team}</span><span>·</span><span>${M.pts(c, "projected pts")}</span>${M.armMark(c)}<span>·</span><span>${M.slotPhrase(c)}</span>${c.injury_status ? `<span>·</span>${M.avail(c)}` : ""}`;

  /* ---- rails ---- */
  const box = (p, cls, line2) => `<div class="pk ${cls}" data-tip="${esc(p.no <= S.consumed ? `${p.name} · ${p.pos} · ${p.team}` : `${M.coord(p)} · ${p.mine ? "you" : "Roster " + p.seat}`)}">
      <div class="c"><span>${M.coord(p)}</span>${p.no <= S.consumed ? M.pill(p.pos) : `<span>#${p.no}</span>`}</div>
      <div class="nm">${line2}</div><div class="sd">${p.mine ? "YOU" : "Roster " + p.seat}</div></div>`;
  M.ticks = () => `<div class="ticks">${M.BETWEEN.map(p => `<i data-tip="#${p.no} · Roster ${p.seat}"></i>`).join("")}</div>`;
  /* A: named past boxes (as many whole boxes as fit, newest nearest the clock), YOU ARE UP, one span, YOUR NEXT */
  M.railA = () => {
    const past = M.KNOWN.slice(-14).reverse().map(p => box(p, p.mine ? "mine" : "", short(p.name))).join("");
    return `<div class="past">${past}</div>${box(M.NOW_PICK, "now mine", "YOU ARE UP")}
      <div class="span"><span class="t"><b>${S.intervening} picks</b> before your next turn</span>${M.ticks()}<span class="seats">${M.seatsText()}</span></div>
      ${M.NEXT_PICK ? box(M.NEXT_PICK, "next mine", "YOUR NEXT") : ""}`;
  };
  /* B: boxes both directions — past named, between as slim seat tokens, future slim dotted */
  M.railB = () => RAIL.map(p => {
    if (p.no <= S.consumed) return box(p, (p.mine ? "mine " : "") + (p.no < (M.PREV_NO || 0) ? "dimmed" : ""), short(p.name));
    if (p.no === M.NOW_NO) return box(p, "now mine", "YOU ARE UP");
    if (p.no === M.NEXT_NO) return box(p, "next mine", "YOUR NEXT");
    if (p.no < (M.NEXT_NO || Infinity)) return `<div class="pk between" data-tip="#${p.no} · ${M.coord(p)} · Roster ${p.seat}"><div class="sd">R${p.seat}</div></div>`;
    return `<div class="pk future ${p.mine ? "mine" : ""}" data-tip="#${p.no} · ${M.coord(p)}"><div class="sd">${p.mine ? "YOU" : "R" + p.seat}</div></div>`;
  }).join("");

  /* ---- sheets content ---- */
  /* Expand/collapse the bench, per roster. A bench of six is worth showing outright; a dynasty
     bench of twenty is a wall, and Sleeper scrolls for exactly that reason. So the DEFAULT is
     derived from the league rather than chosen: show the names while the bench is shallow,
     fold them once it is deeper than the starting lineup, which is the point at which the
     bench stops being a tail and starts being the bulk of the card. The reader's own toggle
     always wins over the default, and is remembered across re-renders because it is keyed by
     seat rather than by position in the grid. */
  M.BENCH_FOLD_DEFAULT = M.benchTotal > M.STARTERS.length;
  M.benchToggled = M.benchToggled || new Set();
  M.benchFolded = seat => M.benchToggled.has(seat) ? !M.BENCH_FOLD_DEFAULT : M.BENCH_FOLD_DEFAULT;
  M.allRosters = () => {
    const seats = [...new Set(RAIL.map(p => p.seat))].sort((a, b) => Number(a) - Number(b));
    return seats.map(seat => { const me = seat === S.seat, picks = me ? S.myPicks : M.KNOWN.filter(p => p.seat === seat);
      const r = slotRoster(picks, S.slots), starters = r.filter(x => x.slot !== "BN");
      const benchP = r.filter(x => x.slot === "BN" && x.p), benchOpen = M.benchTotal - benchP.length;
      const turns = M.BETWEEN.filter(p => p.seat === seat).map(p => "#" + p.no);
      return `<div class="rcard ${me ? "me" : ""} ${turns.length ? "soon" : ""} ${M.benchFolded(seat) ? "foldbn" : ""}" data-seat="${seat}"><h4>${me ? "You" : "Roster " + seat}<span class="note">${turns.length ? `picks ${turns.join(", ")} before your next turn` : me ? "on the clock" : "no pick before your next turn"}</span></h4>
        <div class="sg">${starters.map(x => `<span class="sl ${x.p ? "" : "open"}"${tipAttr(nameTip(x.p))}><i>${slotTag(x.slot, x.p)}</i>${x.p ? short(x.p.name) : "open"}</span>`).join("")}</div>
        <div class="sg bn">
          <button class="sl bh" data-bench="${seat}" aria-expanded="${!M.benchFolded(seat)}" data-tip="${M.benchFolded(seat) ? "Show this roster's bench" : "Hide this roster's bench"}">bench ${benchP.length} of ${M.benchTotal}<em>${M.benchFolded(seat) ? "expand ▸" : "collapse ▾"}</em></button>
          ${benchP.map(x => `<span class="sl bnrow"${tipAttr(nameTip(x.p))}><i>BN${posOfPlayer(x.p) ? "·" + posOfPlayer(x.p) : ""}</i>${short(x.p.name)}</span>`).join("")}${benchOpen > 0 ? `<span class="sl open bnrow"><i>BN</i>${benchOpen} open</span>` : ""}</div>
        </div>`; }).join("");
  };
  M.boardGrid = () => {
    const seats = [...new Set(RAIL.map(p => p.seat))].sort((a, b) => Number(a) - Number(b)), rounds = [...new Set(RAIL.map(p => p.rnd))].sort((a, b) => a - b);
    let html = `<div class="dbgrid" style="grid-template-columns:44px repeat(${seats.length},minmax(58px,1fr))"><div class="dbh"></div>` + seats.map(x => `<div class="dbh">${x === S.seat ? "YOU" : x}</div>`).join("");
    rounds.forEach(r => { html += `<div class="dbh">R${r}</div>`; seats.forEach(x => { const p = RAIL.find(q => q.rnd === r && q.seat === x); if (!p) { html += `<div class="dbc"></div>`; return; }
      const fut = p.no > S.consumed; html += `<div class="dbc ${p.mine ? "mine" : ""} ${fut ? "future" : ""} ${p.no === M.NOW_NO ? "now" : ""}"${fut ? "" : tipAttr(nameTip(p, `${M.coord(p)} · #${p.no}`))}>${fut ? `<span class="q">${M.coord(p)}</span>` : `<span class="p" style="color:${pc(p.pos)}">${p.pos}</span><span class="p">${short(p.name)}</span>`}</div>`; }); });
    return html + "</div>";
  };
  M.squad = subject => `<div class="chair"><div class="who" style="color:var(--gold-b)">What this does</div><p>Three chairs argue <b>${subject}</b>: one for, one against, one to settle it. They read the same facts you see here and may not add a number to them.</p></div>
    <div class="chair"><div class="who" style="color:var(--sky-b)">What it costs</div><p>Three provider calls, then one per follow-up. Nothing is ever called on its own; this room works fully with no provider configured. Callable only while you are on the clock.</p></div>
    <div class="chair"><div class="who" style="color:var(--violet-b)">Where it lands</div><p>On the player you end up taking, readable from the draft board afterwards. No verdict attaches to a player you passed on.</p></div>
    <div class="chair empty"><div class="who">Strategist · Skeptic · Caller</div><p>Not called.</p></div>`;
  return M;
}

/* ============================================================================================
   Chrome shared by every variant: review bar, sheets, copy, and the scroll affordance — every
   list that overflows says so ("↓ N more") so a short list over a dark fold is never mistaken
   for a failed render, and a captioned count never silently differs from what is drawn.
   ============================================================================================ */
function markScrollers(){
  document.querySelectorAll("[data-list]").forEach(el => {
    let more = el.parentElement.querySelector(":scope > .more"); if (!more) { more = document.createElement("div"); more.className = "more"; el.parentElement.appendChild(more); }
    const rows = [...el.querySelectorAll("[data-row]")], edge = el.scrollTop + el.clientHeight;
    const whole = rows.filter(r => r.offsetTop >= edge - 1).length, part = rows.filter(r => r.offsetTop < edge - 1 && r.offsetTop + r.offsetHeight > edge + 1).length;
    if (el.scrollHeight > el.clientHeight + 1 && whole + part > 0) { more.textContent = whole ? `↓ scroll · ${whole} more${part ? " (one cut off)" : ""}` : `↓ scroll · the rest is cut off`; more.hidden = false; el.dataset.more = String(whole + part); }
    else { more.hidden = true; delete el.dataset.more; }
  });
}
function wireChrome(opts){
  const room = document.querySelector(".room");
  /* the URL hash is <format>/<state>; a bare <state> means the control format */
  const h = (location.hash || "").replace("#", "").split("/");
  let fmt = FORMAT_KEYS.includes(h[0]) ? h[0] : FORMAT_KEYS[0], key = STATE_KEYS.includes(h[h.length - 1]) ? h[h.length - 1] : "mid";
  if (!opts.formats) fmt = FORMAT_KEYS[0];
  const bar = document.getElementById("rev");
  bar.innerHTML = `<span class="tag">${opts.tag}</span><span>${opts.sub}</span>${opts.formats ? `<span class="states fmts">${FORMAT_KEYS.map(k => `<button data-fmt="${k}" aria-pressed="${k === fmt}">${k}</button>`).join("")}</span>` : ""}<span class="states">${STATE_KEYS.map(k => `<button data-state="${k}" aria-pressed="${k === key}">${k}</button>`).join("")}</span><button class="hyp" id="hypBtn" aria-expanded="false">ⓘ hypothesis</button>`;
  const setHash = () => history.replaceState(null, "", "#" + (opts.formats ? fmt + "/" : "") + key);
  const hyp = document.getElementById("hyp"); hyp.innerHTML = opts.hypothesis; hyp.hidden = true;
  document.getElementById("hypBtn").onclick = e => { hyp.hidden = !hyp.hidden; e.currentTarget.setAttribute("aria-expanded", String(!hyp.hidden)); requestAnimationFrame(markScrollers); };
  const closeAll = () => { room.querySelectorAll(".sheet").forEach(s => { s.dataset.open = "0"; s.setAttribute("aria-hidden", "true"); });
    room.querySelectorAll("[data-sheet]").forEach(b => b.setAttribute("aria-expanded", "false")); const sc = room.querySelector(".scrim"); if (sc) sc.dataset.open = "0"; };
  const open = id => { const s = document.getElementById(id); if (!s) return; const was = s.dataset.open === "1"; closeAll(); if (was) return;
    s.dataset.open = "1"; s.setAttribute("aria-hidden", "false"); room.querySelectorAll(`[data-sheet="${id}"]`).forEach(b => b.setAttribute("aria-expanded", "true")); const sc = room.querySelector(".scrim"); if (sc) sc.dataset.open = "1"; requestAnimationFrame(markScrollers); };
  document.addEventListener("click", e => {
    const st = e.target.closest("[data-state]"); if (st) { key = st.dataset.state; bar.querySelectorAll("[data-state]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.state === key))); closeAll(); setHash(); opts.onState(key, fmt); return; }
    const fb = e.target.closest("[data-fmt]"); if (fb) { fmt = fb.dataset.fmt; bar.querySelectorAll("[data-fmt]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.fmt === fmt))); closeAll(); setHash(); opts.onState(key, fmt); return; }
    const b = e.target.closest("[data-sheet]"); if (b) { open(b.dataset.sheet); return; }
    if (e.target.closest("[data-close]") || e.target.classList.contains("scrim")) { closeAll(); return; }
    const cp = e.target.closest("[data-copy]"); if (cp) { try { navigator.clipboard && navigator.clipboard.writeText(cp.dataset.copy); } catch (_) {} const t = cp.textContent; cp.textContent = "✓ copied"; setTimeout(() => { cp.textContent = t; }, 1200); }
  });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeAll();
    const t = e.target.closest && e.target.closest("[role=button]"); if (t && (e.key === "Enter" || e.key === " ") && !e.target.closest("button")) { e.preventDefault(); t.click(); } });
  document.addEventListener("scroll", e => { if (e.target.dataset && e.target.dataset.list !== undefined) markScrollers(); }, true);
  addEventListener("resize", markScrollers);
  return {open, closeAll, key: () => key, fmt: () => fmt};
}
function fillCommon(M){
  const q = id => document.getElementById(id);
  const stale = M.S.fresh || M.S.stamp
    ? ` · <span data-tip="Board provenance\nCaptured ${M.S.fresh || "date not recorded"}${M.S.stamp ? ", snapshot " + M.S.stamp : ""}.\nIt reflects the ${M.S.consumed} picks made at that moment and is not re-read while this page is open, so a pick made since will not appear here.">as of pick #${M.S.consumed}</span>`
    : "";
  if (q("lg")) q("lg").innerHTML = `<b>${M.F.teams}-team · ${M.fmt.replace(/_/g, " ")}</b> · round ${M.S.round} of ${M.S.rounds} · you are Roster ${M.S.seat}${stale}`;
  if (q("upnow")) q("upnow").textContent = `PICK ${M.S.pick} — YOU ARE UP`;
  if (q("allRosters")) q("allRosters").innerHTML = M.allRosters();
  if (q("dbHost")) q("dbHost").innerHTML = M.boardGrid();
  requestAnimationFrame(markScrollers);
}

/* hover boxes -------------------------------------------------------------------------------
   One delegated tooltip for every [data-tip] host. Shows on hover AND on keyboard focus, which
   the native title= never did; click pins it so a long explanation can be read without holding
   the pointer still, and Escape or a scroll dismisses it. The first line of a tip renders as a
   heading, the rest as body -- the only structure available without letting hover strings carry
   markup, which they must not, because some of them interpolate vendor data. */
(function () {
  let el = null, host = null, timer = null, pinned = false;
  const box = () => (el || (el = document.body.appendChild(Object.assign(document.createElement("div"), { className: "tip" }))));

  function fill(text) {
    const b = box(); b.textContent = "";
    const lines = text.split("\n").map(s => s.trim()).filter(Boolean);
    if (lines.length > 1) {
      const h = document.createElement("span"); h.className = "th";
      h.textContent = lines[0].charAt(0).toUpperCase() + lines[0].slice(1);
      b.appendChild(h); b.appendChild(document.createTextNode(lines.slice(1).join("\n\n")));
    } else { b.textContent = text; }
    b.classList.toggle("wide", text.length > 170);
  }

  function place() {
    if (!host) return;
    const b = box(), r = host.getBoundingClientRect(), m = 8;
    b.style.left = b.style.top = "0px";            // measure unclamped, then clamp
    const w = b.offsetWidth, h = b.offsetHeight;
    let top = r.bottom + 6;
    if (top + h > innerHeight - m) top = (r.top - h - 6 >= m) ? r.top - h - 6 : Math.max(m, innerHeight - h - m);
    b.style.top = Math.round(top) + "px";
    b.style.left = Math.round(Math.min(Math.max(m, r.left), innerWidth - w - m)) + "px";
  }

  function show(h, now) {
    if (!h.dataset.tip) return;
    host = h; fill(h.dataset.tip);
    const go = () => { place(); box().classList.add("on"); };
    clearTimeout(timer); now ? go() : (timer = setTimeout(go, 130));
  }
  function hide(force) {
    if (pinned && !force) return;
    clearTimeout(timer); pinned = false; host = null;
    if (el) { el.classList.remove("on", "pinned"); }
  }

  addEventListener("mouseover", e => { const h = e.target.closest && e.target.closest("[data-tip]"); if (h && h !== host) { hide(true); show(h); } });
  addEventListener("mouseout", e => { const h = e.target.closest && e.target.closest("[data-tip]"); if (h && h === host && !pinned) hide(); });
  addEventListener("focusin", e => { const h = e.target.closest && e.target.closest("[data-tip]"); if (h) show(h, true); });
  addEventListener("focusout", () => hide());
  addEventListener("keydown", e => { if (e.key === "Escape") hide(true); });
  addEventListener("scroll", () => hide(true), true);
  addEventListener("click", e => {
    const h = e.target.closest && e.target.closest("[data-tip]");
    if (!h) { hide(true); return; }
    // Pin only what is long enough to be worth reading at leisure; short labels keep the
    // plain hover so a click on a chip or a door still does the thing the click is for.
    if ((h.dataset.tip || "").length <= 170) return;
    if (pinned && host === h) { hide(true); return; }
    pinned = false; show(h, true); pinned = true;
    const b = box(); b.classList.add("pinned");
    const n = document.createElement("span"); n.className = "pin"; n.textContent = "click again, or Esc, to dismiss";
    b.appendChild(n); place();
  });
})();
