/* ============================================================================================
   ROUND 2 CORE, revised after ADJUDICATION_R2.md — one model per board state, from states.json,
   no invented fields, no invented thresholds.

   The contract:
   - who · why · what else · at what cost. Rank 1 is "the board's first by value", and the margin
     to the next name is printed beside it. No "tie" is ever asserted (ADJ-R2 §3: ambiguities is
     empty in every state; a tie badge was client-invented).
   - the engine's own words only: cliff.tier 1:1; necessity_label 1:1; depth basis labels verbatim.
   - a measured value never renders as an absence (ADJ-R2 §5): denial 0.0 prints 0.0, horizon
     prints its number at any magnitude, depth prints a digit only under basis "measured".
     There are no visibility cut-points in this file.
   - across positions the comparison is value NOW (the board's order) and the TWO-TURN TOTAL,
     him now + the other position at my next turn (position_next_turn_value, on the payload).
     Their difference is the forfeit arithmetic ADJ §6 asked for, shown as totals, never as an
     "order" ranking with a leader (ADJ-R2 §2, §8). Within a position the wait cost is identical,
     so the comparison rests on value, the measured drop, and the working.
   - late: displacement_adj (measured) is the negativity; the sentence is produced here, once.
   - the rail reads names only for picks <= consumed.
   ============================================================================================ */
const RAIL = D.rail, STATES = D.states, STATE_KEYS = ["early", "mid", "late"];
const STATE_LABEL = {early: "1.06 · empty roster", mid: "4.07 · round four", late: "11.06 · 7 left"};
const num = x => typeof x === "number" && isFinite(x);
const f1  = x => num(x) ? x.toFixed(1) : "—";
const sgn = x => num(x) ? (x > 0 ? "+" : "") + x.toFixed(1) : "—";
const pad = n => String(n).padStart(2, "0");
const pc  = p => "var(--" + (p || "k").toLowerCase() + ")";
const cap = s => s ? s[0].toUpperCase() + s.slice(1) : s;
const POS  = {QB: "quarterback", RB: "running back", WR: "receiver", TE: "tight end"};
const PLUR = {QB: "quarterbacks", RB: "running backs", WR: "receivers", TE: "tight ends"};
const LINEUP_ORDER = ["QB", "RB", "WR", "TE"];       // stable; never re-sorted by cost
const FLEXIBLE = new Set(["RB", "WR", "TE"]);
const ORD = ["first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth"];
const ordw = i => ORD[i] || `${i + 1}th`;
const TIER_WORD = {HIGH: "a sharp drop", MEDIUM: "a moderate drop", LOW: "no cliff"};   // 1:1 from cliff.tier
const TIER_SHORT = {HIGH: "sharp drop", MEDIUM: "moderate drop", LOW: "no cliff"};
const NEC_WORD = {"MUST TAKE": "must take", "STRONG ACTION": "strong action", "PREFERRED": "preferred", "CLOSE CALL": "a close call", "LOW URGENCY": "low urgency", "DOESN'T MATTER MUCH": "doesn't matter much"};
/* verbatim from lineup_optimizer.EXPOSURE_BASIS_LABELS and draft_strategy.DENIAL_BASIS_LABELS */
const DEPTH_LABEL = {
  measured: "measured against your own lineup",
  vacant: "not measured — you hold no starter at this position to insure",
  no_surplus: "measured, but it is a starter's whole value rather than a backup's job — some starter here has no cover, so this is not a depth price and is not charged as one",
  not_applicable: "not measured — this position has no startable slot in this league",
  roster_partial: "not charged — a player you drafted could not be priced, so a spare who may cover this position was left out of the solve and the exposure it measured is NOT the 0.0 shown here"};
const DENIAL_LABEL = {measured: "measured against every rival board that could price him", no_intervening_rival: "no rival had a pick before your next turn", no_rival_priced: "no rival's board could price him, so nothing was measured"};

function norm(c){
  return {id: String(c.player_id), name: c.name, pos: c.position, team: c.team, rank: c.rank,
    tav: c.team_acquisition_value, uv: c.universal_value, need: c.need_bonus, bpa: c.bpa, proj: c.projected_points,
    cliff: c.positional_cliff || null, forfeit: c.positional_forfeit, nextTurn: c.position_next_turn_value, run: !!c.position_run_detected,
    depth: c.depth_exposure, depthBasis: c.depth_basis, denial: c.denial_value, denialBasis: c.denial_basis, denialTeam: c.denial_team == null ? null : String(c.denial_team),
    takeProb: c.rival_premium_take_probability, horizon: c.time_horizon_adj, injury: c.injury_status, availBasis: c.availability_basis,
    disp: c.displacement_adj, dispBasis: c.displacement_basis, necLabel: c.necessity_label, forces: c.forces || [], fills: !!c.fills_required_slot};
}
function slotRoster(picks, slots){
  const left = picks.slice();
  return slots.map(slot => {
    let i = left.findIndex(p => p.pos === slot);
    if (i < 0 && slot === "FLEX") i = left.findIndex(p => FLEXIBLE.has(p.pos));
    if (i < 0 && slot === "BN")   i = left.length ? 0 : -1;
    return {slot, p: i < 0 ? null : left.splice(i, 1)[0]};
  });
}
/* ------------------------------------------------------------------ the model for one state */
function model(key){
  const S = STATES[key];
  const C = S.candidates.map(norm).sort((a, b) => a.rank - b.rank);
  const byId = {}; C.forEach(c => byId[c.id] = c);
  const NOW = S.consumed, ONCLOCK = NOW + 1;
  const KNOWN = RAIL.filter(p => p.no <= NOW);
  const NEXTP = RAIL.find(p => p.mine && p.no > ONCLOCK) || null, NEXT = NEXTP ? NEXTP.no : null;
  const PREVP = KNOWN.filter(p => p.mine).slice(-1)[0] || null;
  const BETWEEN = NEXT ? RAIL.filter(p => p.no > ONCLOCK && p.no < NEXT) : [];
  console.assert(BETWEEN.length === S.intervening, "rail span and intervening disagree", key);
  const SINCE = PREVP ? KNOWN.filter(p => p.no > PREVP.no) : KNOWN;
  const countBy = arr => { const o = {}; arr.forEach(p => o[p.pos] = (o[p.pos] || 0) + 1); return o; };
  const sinceBy = countBy(SINCE), takenBy = countBy(KNOWN), RECENT = KNOWN.slice(-6), recentBy = countBy(RECENT);
  const ROSTER = slotRoster(S.myPicks, S.slots), STARTERS = ROSTER.filter(r => r.slot !== "BN"), BENCH = ROSTER.filter(r => r.slot === "BN");
  const openStarters = pos => STARTERS.filter(r => r.slot === pos && !r.p).length;
  const openFlex = STARTERS.filter(r => r.slot === "FLEX" && !r.p).length;
  const heldAt = pos => S.myPicks.filter(p => p.pos === pos);
  const SEATS = [...new Set(RAIL.map(p => p.seat))].sort((a, b) => Number(a) - Number(b));
  const BY_SEAT = {}; SEATS.forEach(s => BY_SEAT[s] = KNOWN.filter(p => p.seat === s));
  const seatHoles = seat => slotRoster(BY_SEAT[seat], S.slots).filter(x => x.slot !== "BN" && !x.p).map(x => x.slot);
  const RIVALS = []; BETWEEN.forEach(p => { let r = RIVALS.find(x => x.seat === p.seat);
    if (!r) { r = {seat: p.seat, picks: [], holes: seatHoles(p.seat)}; RIVALS.push(r); } r.picks.push(p.no); });
  const rivalFor = c => RIVALS.find(r => r.seat === c.denialTeam) || null;
  const FORFEIT = {}, NEXTVAL = {}; C.forEach(c => { if (num(c.forfeit) && !(c.pos in FORFEIT)) FORFEIT[c.pos] = c.forfeit; if (num(c.nextTurn) && !(c.pos in NEXTVAL)) NEXTVAL[c.pos] = c.nextTurn; });
  const PRESENT = LINEUP_ORDER.filter(p => C.some(c => c.pos === p));
  const atPos = pos => C.filter(c => c.pos === pos);
  const atPosBpa = pos => atPos(pos).slice().sort((a, b) => b.bpa - a.bpa);
  const posBest = pos => atPos(pos)[0] || null;
  const posRank = c => atPos(c.pos).findIndex(x => x.id === c.id);
  function cliffNext(c){
    const l = atPosBpa(c.pos), i = l.findIndex(x => x.id === c.id), n = l[i + 1] || null;
    if (n && c.cliff && Math.abs((c.bpa - n.bpa) - c.cliff.gap) > 0.02) return null;   // payload does not reproduce the gap → do not name
    return n;
  }
  const bpaAhead = c => { const l = atPosBpa(c.pos), i = l.findIndex(x => x.id === c.id); return l.slice(0, i); };
  function slotFor(c){
    const open = openStarters(c.pos), held = heldAt(c.pos);
    if (open > 0 && held.length === 0) return {kind: "vacant", slot: c.pos, label: `${c.pos} · empty today`};
    if (open > 0) return {kind: "second", slot: c.pos + (held.length + 1), beside: held[0], label: `${c.pos}${held.length + 1} · beside ${short(held[0].name)}`};
    if (openFlex > 0 && FLEXIBLE.has(c.pos)) return {kind: "flex", slot: "FLEX", holder: held[0], label: `FLEX · ${held.map(h => short(h.name)).join(", ")} hold${held.length === 1 ? "s" : ""} ${c.pos}`};
    return {kind: "bench", slot: "BN", label: "Bench · your starters are set"};
  }
  const slotIndexFor = c => { const sf = slotFor(c); let lit = false;
    return STARTERS.findIndex(r => { if (lit || r.p) return false; const hit = (sf.kind !== "bench" && sf.kind !== "flex" && r.slot === c.pos) || (sf.kind === "flex" && r.slot === "FLEX"); if (hit) lit = true; return hit; }); };
  function depthText(c){   // a digit ONLY under measured; otherwise the engine's own label
    if (c.depthBasis === "measured") return {n: f1(c.depth), why: DEPTH_LABEL.measured};
    return {n: null, why: DEPTH_LABEL[c.depthBasis] || `basis "${c.depthBasis}" has no label`};
  }
  const PCTX = {};
  LINEUP_ORDER.forEach(pos => { const best = posBest(pos);
    PCTX[pos] = {pos, best, slot: slotFor({pos}), taken: takenBy[pos] || 0, since: sinceBy[pos] || 0, recent: recentBy[pos] || 0,
      run: atPos(pos).some(c => c.run), forfeit: FORFEIT[pos], nextTurn: NEXTVAL[pos]}; });
  const CTX = {};
  C.forEach(c => { const best = posBest(c.pos);
    CTX[c.id] = {c, rank: posRank(c), best, gapToBest: c.tav - best.tav, cliffNext: cliffNext(c), ahead: bpaAhead(c),
      tier: c.cliff ? c.cliff.tier : null, gap: c.cliff ? c.cliff.gap : null, rival: rivalFor(c), depth: depthText(c), slot: slotFor(c)}; });
  const RUNNER = C[1] || null;    // the margin the board's first holds over the next name
  return {key, S, C, byId, NOW, ONCLOCK, KNOWN, NEXTP, NEXT, PREVP, BETWEEN, SINCE, sinceBy, takenBy, RECENT, ROSTER, STARTERS, BENCH,
    SEATS, BY_SEAT, seatHoles, RIVALS, FORFEIT, NEXTVAL, PRESENT, atPos, atPosBpa, posBest, cliffNext, slotFor, slotIndexFor, PCTX, CTX, heldAt, RUNNER};
}
let M = null;

/* ---- names: initial + surname, keeping particles (A. St. Brown ≠ A.J. Brown, both on the early board) ---- */
const PARTICLES = new Set(["st.", "st", "van", "von", "de", "del", "della", "di", "da", "la", "le", "du", "mac", "mc"]);
const short = n => { const w = (n || "").split(" "); if (w.length < 2) return n;
  let i = w.length - 1; while (i > 1 && PARTICLES.has(w[i - 1].toLowerCase())) i--;
  return w[0][0] + ". " + w.slice(i).join(" "); };
const takeText = p => !num(p) ? "—" : p >= 0.01 ? `about ${Math.round(p * 100)}%` : "under 1%";
const tierWord = c => TIER_WORD[(c.cliff || {}).tier] || "no cliff measured";
const necWord = c => NEC_WORD[c.necLabel] || (c.necLabel || "").toLowerCase();
const readChip = c => `<span class="read" title="The board's necessity label for this pick, rendered as it was given. It is not a value score.">the board's read: <b>${necWord(c)}</b></span>`;
/* the margin: what the board's first holds over the next name, or what a subject trails by */
function marginHTML(c){
  const lead = M.C[0];
  if (c.id === lead.id) return M.RUNNER ? `<span class="d up">the board's first by value · ${short(M.RUNNER.name)} ${f1(lead.tav - M.RUNNER.tav)} behind</span>` : `<span class="d up">the board's only name</span>`;
  return `<span class="d down">${f1(c.tav - lead.tav)} vs ${short(lead.name)}, the board's first</span>`;
}
/* ---- late: the one named measured quantity behind a negative value (ADJ-R2 §1) ---- */
function displacementHTML(c){
  if (!num(c.disp) || c.disp === 0 || c.dispBasis !== "measured") return "";
  return `<p class="disp">Your starters are set, so he would sit — <b>${f1(c.disp)}</b> of his ${f1(c.tav)} is the measured cost of displacing a starter you already have; the rest of him is <b>${f1(c.tav - c.disp)}</b>.</p>`;
}
/* ---- facts about a POSITION, said once, scoped to this board ---- */
function positionFacts(pos){
  const P = M.PCTX[pos], out = [], say = (text, kind) => out.push({text, kind});
  if (P.slot.kind === "vacant")      say(`You have no ${POS[pos]}; one taken here starts at once.`, "slot");
  else if (P.slot.kind === "second") say(`A ${POS[pos]} here starts beside ${short(P.slot.beside.name)}.`, "slot");
  else if (P.slot.kind === "flex")   say(`${P.slot.holder ? short(P.slot.holder.name) + " holds" : "You hold"} ${pos}; another ${POS[pos]} starts only at FLEX.`, "slot");
  else                               say(`Your starters are set; a ${POS[pos]} would sit.`, "slot");
  if (P.taken === 0)                 say(`No ${POS[pos]} has been drafted by anyone yet.`, "pool");
  else if (P.run)                    say(`A run on ${PLUR[pos]}: ${P.recent} of the last six picks.`, "run");
  if (num(P.forfeit)) say(`Wait on ${PLUR[pos]} and the position gives about <b>${f1(P.forfeit)}</b> less at #${M.NEXT}.`, "wait");
  else say(`No ${POS[pos]} is among the ${M.C.length} this board rates here, so no wait cost is measured.`, "wait");
  return out;
}
/* ---- facts about a PLAYER: only what separates him from the others at his position ---- */
function playerFacts(id){
  const k = M.CTX[id], c = k.c, pos = POS[c.pos], out = [], say = (text, kind) => out.push({text, kind});
  if (k.rank > 0) say(`${cap(ordw(k.rank))} ${pos} on the board, <b>${f1(-k.gapToBest)}</b> behind ${short(k.best.name)}.`, "rank");
  else say(`The best ${pos} left on the board.`, "rank");
  if (k.cliffNext) say(`Behind him: ${tierWord(c)} — ${short(k.cliffNext.name)} is <b>${f1(k.gap)}</b> lower, in the order the drop was measured.`, "cliff");
  else say(`No ${pos} behind him in the order the drop was measured${k.ahead.length ? ` (${k.ahead.map(a => short(a.name)).join(", ")} ${k.ahead.length === 1 ? "is" : "are"} ahead of him there)` : ""}; the drop measured behind him (${tierWord(c)}, ${f1(k.gap)}) is to a player below this board.`, "cliff");
  if (c.denialTeam && k.rival) say(`Roster ${k.rival.seat} (picks #${k.rival.picks.join(", #")}) is the rival named for him — ${takeText(c.takeProb)} to take him before #${M.NEXT}.`, "rival");
  if (c.injury) say(`Listed ${c.injury}; ${c.availBasis === "immaterial_designation" ? "judged immaterial" : "not counted in his value"}.`, "injury");
  if (k.depth.n) say(`Depth insurance measured at <b>${k.depth.n}</b>.`, "depth");
  return out;
}
function playerFactsCompact(id){
  const k = M.CTX[id], c = k.c, out = [];
  if (c.denialTeam && k.rival) out.push(`Rival named: Roster ${k.rival.seat} · ${takeText(c.takeProb)}`);
  if (c.injury) out.push(`Listed ${c.injury}${c.availBasis === "immaterial_designation" ? " · judged immaterial" : ""}`);
  if (k.depth.n) out.push(`Depth insurance measured: <b>${k.depth.n}</b>`);
  return out;
}
/* ---- compare(a, b): the relation ---- */
function compare(aId, bId){
  const a = M.byId[aId], b = M.byId[bId];
  const r = {a, b, dv: a.tav - b.tav, same: a.pos === b.pos};
  r.valueLeader = r.dv >= 0 ? a : b;
  if (r.same) {
    const l = M.atPosBpa(a.pos), ia = l.findIndex(x => x.id === aId), ib = l.findIndex(x => x.id === bId);
    r.measuredAhead = ia < ib ? a : b; r.places = Math.abs(ia - ib); r.adjacent = r.places === 1;
    r.dropBetween = r.adjacent ? r.measuredAhead.cliff : null;
    r.dh = (a.horizon || 0) - (b.horizon || 0);
  } else {
    /* two turns: him now + the other position at my next turn. position_next_turn_value is on the payload;
       forfeit(P) == tav(best P) − next_turn(P), so the difference of the totals is the forfeit arithmetic. */
    r.aNext = M.NEXTVAL[b.pos]; r.bNext = M.NEXTVAL[a.pos];
    r.measured = num(r.aNext) && num(r.bNext);
    r.aTotal = r.measured ? a.tav + r.aNext : null;   // A now, then B's position at #NEXT
    r.bTotal = r.measured ? b.tav + r.bNext : null;
    r.dTotal = r.measured ? r.aTotal - r.bTotal : null;
  }
  return r;
}
/* the compact form: value NOW (bright) and the two-turn totals (quieter), magnitudes always shown */
function edgeHTML(subjId, altId){
  const r = compare(subjId, altId), A = short(r.a.name), B = short(r.b.name);
  const v = `<span class="edge" title="value to your roster, now — what the board orders on"><span class="n">${sgn(Math.abs(r.dv))}</span> now, ${r.valueLeader === r.a ? A : B}</span>`;
  if (r.same) return v + (r.adjacent ? ` <span class="edge q" title="the drop measured between them, within ${r.a.pos}"><span class="n">${f1(r.dropBetween.gap)}</span> ${TIER_SHORT[r.dropBetween.tier]} between, measured</span>` : ` <span class="edge q"><span class="n">${r.places}</span> places apart in the measured order</span>`);
  if (!r.measured) return v + ` <span class="edge q">two-turn total not measured for ${r.a.pos === undefined ? "" : "one position"}</span>`;
  return v + ` <span class="edge q" title="${A} now + ${POS[r.b.pos]} at #${M.NEXT} (≈${f1(r.aNext)}) = ${f1(r.aTotal)}; ${B} now + ${POS[r.a.pos]} at #${M.NEXT} (≈${f1(r.bNext)}) = ${f1(r.bTotal)}"><span class="n">${sgn(Math.abs(r.dTotal))}</span> over two turns, ${r.dTotal >= 0 ? A : B}</span>`;
}
/* the two-turn totals written out, one line */
function twoTurnText(subjId, altId){
  const r = compare(subjId, altId), A = short(r.a.name), B = short(r.b.name);
  if (r.same) return `Same position, so waiting costs the same either way.`;
  if (!r.measured) return `One of the two positions has no measured value at #${M.NEXT} on this board.`;
  return `<b>${A}</b> now + ${r.b.pos} at #${M.NEXT} ≈ <b>${f1(r.aTotal)}</b> · <b>${B}</b> now + ${r.a.pos} at #${M.NEXT} ≈ <b>${f1(r.bTotal)}</b>`;
}
function alternatives(id, n){
  const c = M.byId[id], out = [];
  M.C.filter(x => x.pos !== c.pos && M.posBest(x.pos).id === x.id).forEach(x => out.push(x));
  const nxt = M.atPos(c.pos).find(x => x.rank > c.rank) || M.atPos(c.pos).find(x => x.id !== c.id); if (nxt) out.push(nxt);
  out.sort((x, y) => y.tav - x.tav);
  return n ? out.slice(0, n) : out;
}
/* ---- atoms ---- */
function face(c, size){
  const init = (c.name || "").split(" ").map(w => w[0]).slice(0, 2).join("");
  return `<span class="face ${size || ""} pos-${c.pos}" title="${c.name}">${init}<img alt="" loading="lazy" src="https://sleepercdn.com/content/nfl/players/${c.id}.jpg" onerror="this.remove()"></span>`;
}
const pill = pos => `<span class="pill" style="background:${pc(pos)}">${pos}</span>`;
const withheldChip = () => `<span class="wh" title="Computed, then held back: it failed its calibration check against real drafts. The count of picks stands in for it.">withheld</span>`;
const lockChip = () => `<span class="lock" title="A user-set freeze timer warns before a late billed call. Nothing has been recorded yet, so no lock is recommended."><b>call lock</b> not set</span>`;
const billed = (id, label) => `<button class="btn billed" data-sheet="${id}" aria-expanded="false"><span class="dot"></span>${label} <small>billed · on the clock</small></button>`;
const copyBtn = (c, brief) => `<button class="copy" data-copy="${c.name}" title="Copies “${c.name}”. You make the pick in Sleeper; this room reads it back. Nothing here spends a pick.">copy “${brief ? short(c.name) : c.name}”</button>`;
function waitText(){ return `<b>${M.S.intervening} picks</b> until you choose again · your next turn is <i>#${M.NEXT}</i>`; }
function sinceText(){ const o = M.sinceBy, ks = Object.keys(o).sort((a, b) => o[b] - o[a]);
  return M.PREVP ? `since your last turn (#${M.PREVP.no}): ${ks.map(k => `${o[k]} ${k}`).join(" · ")} left the board` : `before your first turn: ${ks.map(k => `${o[k]} ${k}`).join(" · ")} went`; }
/* every measured quantity, with its basis in the engine's words; nothing gated, nothing zeroed */
function workingHTML(c){
  const k = M.CTX[c.id];
  const row = (l, v, abs) => `<div class="wrow"><span class="l">${l}</span><span class="v ${abs ? "abs" : ""}">${v}</span></div>`;
  return `<details class="work"><summary>the working</summary>
    ${row("Value for any roster + for your needs", `${f1(c.uv)} + ${f1(c.need)}`)}
    ${row(`Displacement in your lineup (${c.dispBasis})`, f1(c.disp))}
    ${row(`Dynasty horizon, inside his value`, sgn(c.horizon))}
    ${k.depth.n ? row("Depth insurance", `${k.depth.n} <small>· ${k.depth.why}</small>`) : row("Depth insurance", k.depth.why, true)}
    ${row(`Kept from rivals (${DENIAL_LABEL[c.denialBasis] || c.denialBasis})`, `${f1(c.denial)}${c.denialTeam ? ` · Roster ${c.denialTeam} · ${takeText(c.takeProb)}` : ""}`)}
    ${row("Chance he lasts to #" + M.NEXT, withheldChip(), true)}
    ${row("Designation", c.injury || "none", !c.injury)}
    ${row("The board's read", necWord(c))}
  </details>`;
}
/* ---- roster renderers; marks: [{c, tag, color}] light the slot each would fill ---- */
function markText(m){ return `${m.tag ? `<span class="ab" style="background:${m.color || "var(--gold-b)"}">${m.tag}</span>` : "←"} ${short(m.c.name)}`; }
function rosterListHTML(marks){
  marks = (marks || []).filter(m => m && m.c);
  const lit = {}; marks.forEach(m => { const i = M.slotIndexFor(m.c); if (i >= 0) (lit[i] = lit[i] || []).push(m); });
  const benchMarks = marks.filter(m => M.slotFor(m.c).kind === "bench");
  const prime = i => lit[i] && lit[i].some(m => !m.tag);
  return M.STARTERS.map((r, i) => `<div class="slot ${r.p ? "" : "open"} ${!r.p && r.slot !== "FLEX" ? "need" : ""} ${lit[i] ? (prime(i) ? "fills" : "fills sec") : ""}"><span class="s">${r.slot}</span>${r.p ? `${pill(r.p.pos)}<span class="p" title="${r.p.name}">${short(r.p.name)}</span><span class="at">${r.p.rnd}.${pad(r.p.inr)}</span>` : `<span class="p">${lit[i] ? lit[i].map(markText).join(" · ") : "open"}</span>`}</div>`).join("")
    + `<div class="slot bn ${benchMarks.length ? (benchMarks.some(m => !m.tag) ? "fills" : "fills sec") : ""}" style="margin-top:4px"><span class="s">BN</span><span class="p">${M.BENCH.filter(r => r.p).length} of ${M.BENCH.length} filled${benchMarks.length ? " · " + benchMarks.map(markText).join(" · ") : ""}</span></div>`;
}
function rosterStripHTML(marks){
  marks = (marks || []).filter(m => m && m.c);
  const lit = {}; marks.forEach(m => { const i = M.slotIndexFor(m.c); if (i >= 0) (lit[i] = lit[i] || []).push(m); });
  const benchMarks = marks.filter(m => M.slotFor(m.c).kind === "bench");
  return M.STARTERS.map((r, i) => `<span class="slotc ${r.p ? "" : "open"} ${!r.p && r.slot !== "FLEX" ? "need" : ""} ${lit[i] ? "fills" : ""}"><span class="s">${r.slot}</span>${r.p ? `${pill(r.p.pos)}${short(r.p.name)}` : lit[i] ? lit[i].map(markText).join(" · ") : "open"}</span>`).join("")
    + `<span class="slotc ${benchMarks.length ? "fills" : "open"}"><span class="s">BN</span>${M.BENCH.filter(r => r.p).length} of ${M.BENCH.length}${benchMarks.length ? " · " + benchMarks.map(markText).join(" · ") : ""}</span>`;
}
/* ---- candidate list row; the delta is always against the SUBJECT, said in the header of every list ---- */
function crowHTML(c, subj, opts){
  opts = opts || {}; const k = M.CTX[c.id], d = subj && subj.id !== c.id && !opts.noDelta ? sgn(c.tav - subj.tav) : "";
  const sub = opts.lean ? (c.injury ? `<small><i class="q" title="${c.injury}">${c.injury[0]}</i></small>` : "") : `<small>${c.team} · ${Math.round(c.proj)} pts${k.tier === "HIGH" ? " · " + TIER_SHORT[k.tier] + " behind" : ""}${c.injury ? ` · <i>${c.injury}</i>` : ""}</small>`;
  return `<div class="crow ${opts.cls || ""}" data-id="${c.id}" role="button" tabindex="0" aria-selected="${!!subj && subj.id === c.id}"><span class="rk">${c.rank}</span>${pill(c.pos)}<span class="n" title="${c.name} · ${c.team}">${short(c.name)}${sub}</span><span class="v">${f1(c.tav)}${d ? `<small>${d}</small>` : ""}</span>${opts.extra || ""}</div>`;
}
const listCaption = (shown, total) => shown < total ? `showing ${shown} of ${total} · scroll for the rest` : `all ${total}`;
/* a list never shows a half row: its height snaps to whole rows, and the caption says how many */
function snapList(L, cols){
  L.style.maxHeight = ""; const rows = [...L.querySelectorAll(".crow")]; if (!rows.length) return 0;
  const rh = rows[0].getBoundingClientRect().height || 31, avail = L.getBoundingClientRect().height, per = Math.max(1, Math.floor(avail / rh));
  L.style.maxHeight = (per * rh) + "px";
  return Math.min(rows.length, per * (cols || 1));
}
/* ---- rails. Names are read only from KNOWN. ---- */
function pastBox(p){ return `<div class="pk past ${p.mine ? "mine" : ""}" data-no="${p.no}" role="button" tabindex="0" title="${p.name} — ${p.mine ? "you" : "Roster " + p.seat}"><div class="c"><span>${p.rnd}.${pad(p.inr)}</span><span>#${p.no}</span></div><div class="nm">${short(p.name)}</div><div class="sd">${p.mine ? "YOU" : "Roster " + p.seat}</div></div>`; }
function nowBox(){ const p = RAIL[M.NOW]; return `<div class="pk now mine"><div class="c"><span>${p.rnd}.${pad(p.inr)}</span><span>#${p.no}</span></div><div class="nm">YOU ARE UP</div><div class="sd">YOU</div></div>`; }
function nextBox(){ const p = M.NEXTP; return p ? `<div class="pk next"><div class="c"><span>${p.rnd}.${pad(p.inr)}</span><span>#${p.no}</span></div><div class="nm">YOUR NEXT</div><div class="sd">${M.S.intervening} picks away</div></div>` : ""; }
function railSpanHTML(){
  const seats = [...new Set(M.BETWEEN.map(p => p.seat))];
  const rivals = [...new Set(M.C.map(c => c.denialTeam).filter(Boolean))].filter(s => seats.includes(s));
  const span = `<div class="span" title="The ${M.S.intervening} picks between your turns: every wait cost on this screen is measured across exactly these."><div class="c"><span>#${M.ONCLOCK + 1}–#${M.NEXT - 1}</span><span>${M.S.intervening} picks</span></div><div class="nm">${M.S.intervening} picks before you choose again</div><div class="sd">rosters ${seats.join(", ")}${rivals.length ? ` · named rival${rivals.length > 1 ? "s" : ""}: ${rivals.join(", ")}` : ""}</div></div>`;
  return M.KNOWN.map(pastBox).join("") + nowBox() + span + nextBox();
}
function railTicksHTML(){
  const rivals = new Set(M.C.map(c => c.denialTeam).filter(Boolean));
  const tick = (p, after) => `<div class="tick ${rivals.has(p.seat) && !after ? "rival" : ""} ${after ? "after" : ""}" title="#${p.no} · Roster ${p.seat}${rivals.has(p.seat) && !after ? " · named as a rival" : ""}"><div class="c">#${p.no}</div><div class="sd">Roster ${p.seat}</div></div>`;
  const after = M.NEXT ? RAIL.filter(p => p.no > M.NEXT && p.no <= M.NEXT + 4) : [];
  return M.KNOWN.map(pastBox).join("") + nowBox() + M.BETWEEN.map(p => tick(p, false)).join("") + nextBox() + after.map(p => tick(p, true)).join("");
}
function wireRail(scrollEl){
  const recentre = instant => { const nxt = scrollEl.querySelector(".pk.next") || scrollEl.querySelector(".pk.now"); if (!nxt) return;
    const left = nxt.offsetLeft + nxt.offsetWidth - scrollEl.clientWidth + 48;
    scrollEl.scrollTo({left: Math.max(0, left), behavior: instant === true ? "auto" : "smooth"}); };
  const toPrev = () => { const n = [...scrollEl.querySelectorAll(".pk.mine.past")].pop(); if (n) scrollEl.scrollTo({left: Math.max(0, n.offsetLeft - 20), behavior: "smooth"}); };
  scrollEl.addEventListener("wheel", e => { if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) { e.preventDefault(); scrollEl.scrollLeft += e.deltaY; } }, {passive: false});
  let down = false, x0 = 0, l0 = 0;
  scrollEl.addEventListener("pointerdown", e => { down = true; x0 = e.clientX; l0 = scrollEl.scrollLeft; scrollEl.classList.add("drag"); });
  addEventListener("pointerup", () => { down = false; scrollEl.classList.remove("drag"); });
  scrollEl.addEventListener("pointermove", e => { if (down) scrollEl.scrollLeft = l0 - (e.clientX - x0); });
  return {recentre, toPrev};
}
function pickDetailHTML(no){
  const p = RAIL[no - 1];
  return `<span class="k">${p.rnd}.${pad(p.inr)}</span>${pill(p.pos)}<b>${p.name}</b><span>${p.team || ""}</span><span class="k">by</span><span>${p.mine ? "you" : "Roster " + p.seat}</span>${p.mine ? `<span style="color:var(--violet-b)">◇ no verdict recorded on this pick</span>` : ""}<button class="x" data-clear="1">close ✕</button>`;
}
/* ---- sheets ---- */
function allRostersHTML(){
  const ORDER = ["QB", "RB", "WR", "TE", "K", "DEF"];
  return M.SEATS.map(seat => { const byPos = {}; M.BY_SEAT[seat].forEach(p => (byPos[p.pos] = byPos[p.pos] || []).push(p));
    return `<div class="rcard ${seat === M.S.seat ? "me" : ""}"><h4>${seat === M.S.seat ? "You" : "Roster " + seat}<span class="note">${M.BY_SEAT[seat].length} picks</span></h4>
      ${ORDER.filter(q => byPos[q]).map(q => `<div class="ln">${pill(q)}<span class="n">${byPos[q].map(p => short(p.name)).join(" · ")}</span></div>`).join("") || `<div class="ln note">no picks yet</div>`}
      <div class="ln holes"><span class="k">open</span><span class="n">${M.seatHoles(seat).join(" · ") || "—"}</span></div></div>`; }).join("");
}
function boardGridHTML(){
  const rounds = [...new Set(RAIL.map(p => p.rnd))].sort((a, b) => a - b);
  let html = `<div class="dbh"></div>` + M.SEATS.map(x => `<div class="dbh">${x === M.S.seat ? "YOU" : x}</div>`).join("");
  rounds.forEach(r => { html += `<div class="dbh" style="align-self:center">R${r}</div>`;
    M.SEATS.forEach(x => { const p = RAIL.find(q => q.rnd === r && q.seat === x); if (!p) { html += `<div class="dbc"></div>`; return; }
      const future = p.no > M.NOW;
      html += `<div class="dbc ${p.mine ? "mine" : ""} ${future ? "future" : ""} ${p.no === M.ONCLOCK ? "now" : ""}">${future ? `<span class="q">${p.rnd}.${pad(p.inr)}</span>` : `<span class="p" style="color:${pc(p.pos)}">${p.pos}</span><span class="p">${short(p.name)}</span>`}</div>`; }); });
  return `<div class="dbwrap"><div class="dbgrid" style="grid-template-columns:44px repeat(${M.SEATS.length},minmax(58px,1fr))">${html}</div></div>`;
}
function squadHTML(about){
  return `<div class="gate">You are on the clock, so a call is allowed. Three provider calls, billed.</div>
    <div class="chair"><div class="who" style="color:var(--gold-b)">What a debate does</div><p>Three chairs argue <b>${about}</b> — one for, one against, one to settle it. They read the same facts shown here and are told to invent nothing.</p></div>
    <div class="chair"><div class="who" style="color:var(--violet-b)">Where it lands</div><p>The verdict attaches to the player you actually take and reads back from your roster. A player you pass on gets no verdict.</p></div>
    <p class="note">No chair text is shown: it would be an invented model opinion dressed as a real one. This room runs fully with no provider at all.</p>`;
}
function wireSheets(root){
  const closeAll = () => { root.querySelectorAll(".sheet").forEach(s => { s.dataset.open = "0"; s.setAttribute("aria-hidden", "true"); });
    root.querySelectorAll("[data-sheet]").forEach(b => b.setAttribute("aria-expanded", "false")); const sc = root.querySelector(".scrim"); if (sc) sc.dataset.open = "0"; };
  const openSheet = id => { const s = root.querySelector("#" + id); if (!s) return; const was = s.dataset.open === "1"; closeAll();
    if (!was) { s.dataset.open = "1"; s.setAttribute("aria-hidden", "false"); root.querySelectorAll(`[data-sheet="${id}"]`).forEach(b => b.setAttribute("aria-expanded", "true")); const sc = root.querySelector(".scrim"); if (sc) sc.dataset.open = "1"; } };
  root.addEventListener("click", e => { const b = e.target.closest("[data-sheet]"); if (b) { openSheet(b.dataset.sheet); return; }
    if (e.target.closest("[data-close]") || e.target.classList.contains("scrim")) closeAll(); });
  document.addEventListener("keydown", e => { if (e.key === "Escape") closeAll(); });
  return {openSheet, closeAll};
}
function copyName(name, btn){
  const done = () => { const t = btn.textContent; btn.textContent = "copied"; setTimeout(() => btn.textContent = t, 1200); };
  if (navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(name).then(done, done); else done();
}
function fillChrome(){
  const lg = document.getElementById("lg"); if (lg) lg.innerHTML = `<b>12-team PPR Dynasty</b> · round ${M.S.round} of ${M.S.rounds} · seat ${M.S.seat}`;
  const up = document.getElementById("upnow"); if (up) up.innerHTML = `PICK ${M.S.pick} — <span class="who">YOU</span> ARE UP`;
  const w = document.getElementById("wait"); if (w) w.innerHTML = waitText();
  const t = document.getElementById("tags"); if (t) t.innerHTML = lockChip();
  const ar = document.getElementById("allRosters"); if (ar) ar.innerHTML = allRostersHTML();
  const db = document.getElementById("dbHost"); if (db) db.innerHTML = boardGridHTML();
}
function setState(key, first){
  if (!STATES[key]) key = "mid";
  M = model(key);
  document.querySelectorAll("[data-state]").forEach(b => b.setAttribute("aria-pressed", String(b.dataset.state === key)));
  if (!first && location.hash !== "#" + key) history.replaceState(null, "", "#" + key);
  fillChrome();
  if (typeof render === "function") render(true);
}
function stateButtonsHTML(){ return STATE_KEYS.map(k => `<button data-state="${k}" aria-pressed="false">${STATE_LABEL[k]}</button>`).join(""); }
function boot(){
  const sb = document.getElementById("states"); if (sb) sb.innerHTML = stateButtonsHTML();
  document.addEventListener("click", e => { const b = e.target.closest("[data-state]"); if (b) setState(b.dataset.state); });
  addEventListener("hashchange", () => setState(location.hash.slice(1)));
  setState((location.hash || "#mid").slice(1), true);
}
