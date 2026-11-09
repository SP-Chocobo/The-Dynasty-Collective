"""`#357`: milestone 1 -- the read-only server, on 127.0.0.1 only.

OWNER'S RULINGS THIS IMPLEMENTS (2026-11-08/09), recorded at `#354`:

  * 127.0.0.1 ONLY. No TLS, no exposure. Authentication is its own milestone, and the passphrase
    gate is decorative without HTTPS; binding to loopback makes the patience structural instead
    of disciplinary -- there is no exposed endpoint to get impatient about.
  * SERVER-RENDERED HTML, not a JSON API. `front_claims.compose` already decides which claims
    matter, in what order, with which figures. A JSON API would force a second implementation of
    that in JavaScript, which is `#126` (one home) and `#336b` (a renderer inventing a quantity)
    by construction. There is no performance argument on the other side: composition is 0.00ms
    median, 0.04ms worst.
  * ONE PROCESS. Not for speed. `app.py` persists state to local files with no locking and no
    notion of who is asking, so a second process does not add a worker -- it adds a SECOND WRITER
    to unsynchronised files. One process is an architectural constraint that currently protects
    data integrity.

THIS SERVER WRITES NOTHING. Every handler reads. That is what makes it safe to run beside
`app.py`, which remains the only writer: `app.py` syncs and writes the snapshot, this reads it.
`test_server.py` holds that property directly rather than trusting this paragraph.

WHY THE STATUS SURFACE IS NOT A NICE-TO-HAVE. I cannot verify this against the owner's league --
`data/sleeper_snapshots/` holds nothing but a `.gitkeep`, and the committed league captures carry
settings with no rosters. So the page itself has to be the instrument, and the thing it must do
that no fixture ever needed is distinguish a STRUCTURAL absence from a FAILED READ. `#187` protects
a reader from an invented number and gives them none at all from a field that should have arrived:
a wrong Sleeper key renders as a tidy labelled em dash, indistinguishable from the contract working.
`live_source` draws that distinction; `/status` is where it is readable.

WARM-UP IS DONE ONCE AND HELD. The players universe (6,594 rows from the committed capture) and
the `DataMerger` cost ~0.9s to build and are then reused for every request -- which is the whole
reason one persistent process beats a per-request script, and the reason `compose` can be free.

Run it:  python3 server.py            (127.0.0.1:8765)
"""
from __future__ import annotations

import html
import importlib.util
import os
import json
import pathlib
import threading
import time

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.responses import HTMLResponse, PlainTextResponse, Response
from starlette.routing import Route

import front_claims as fc
import live_source as ls
import page_assets as pa

ROOT = pathlib.Path(__file__).resolve().parent
R7 = ROOT / "ui_explore" / "round7"
#: LOOPBACK BY DEFAULT, by the owner's ruling (`#354`): milestone 1 is not exposed, and binding
#: to 127.0.0.1 makes that structural rather than disciplinary -- there is no public listener to
#: get impatient about.
#:
#: THE OVERRIDE EXISTS FOR ONE REAL CASE, and it is not "make it public". cloudflared connects
#: to the origin over the loopback of ITS OWN network namespace. If the tunnel daemon and this
#: server are not in the same namespace -- cloudflared on Windows with the app in WSL, or either
#: one in Docker -- then `127.0.0.1:8765` from cloudflared's side is a DIFFERENT loopback with
#: nothing on it, and the tunnel returns 502 while the app is running perfectly. The fix is to
#: bind an address the daemon can actually reach and point the route there.
#:
#: Anything other than 127.0.0.1 is a listener something else can reach, so it is opt-in,
#: per-run, and announced on startup rather than silent.
HOST = os.environ.get("GOLDWYRM_HOST", "127.0.0.1")
PORT = int(os.environ.get("GOLDWYRM_PORT", "8765"))


def _load(name: str, path: pathlib.Path):
    """By PATH, not by name.

    `build_dashboard.py` and `build_landing.py` each exist in BOTH round5 and round7, and under
    any import that puts round5's directory on the path first, `import build_dashboard` resolves
    to the wrong one. That cost ten suite errors once already (`409b8a9`); the fix is to never
    let the name decide.
    """
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


DASH = _load("r7_dashboard_server", R7 / "build_dashboard.py")


class Engine:
    """The warm, shared, READ-ONLY engine state.

    The lock is held for the WARM-UP only, so two concurrent first requests cannot each pay the
    0.9s and race to install a half-built universe. Nothing here mutates after warm-up, so
    readers never contend -- and when milestone 3 adds a sync, `busy` is the single-flight guard
    that stops a second one starting, which is also what the status surface's "active operation"
    reports. The field exists now so the discipline is in place before the first writer is.
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.started_at = time.time()
        self.players_db: dict | None = None
        self.byes: dict | None = None
        self.merger = None
        #: `set_league_format` MUTATES the merger -- it selects a different rankings export, and
        #: that is how `rec` and `bonus_rec_te` reach a price at all (they do NOT propagate
        #: through scoring_settings). So pricing is not thread-safe on a shared merger, and ONE
        #: PROCESS DOES NOT MEAN SERIALISED WRITES once threads are involved. Every priced read
        #: takes this lock. Readers of already-rendered pages never touch it.
        self._price_lock = threading.Lock()
        self.warm_seconds: float | None = None
        self.warm_error: str | None = None
        self.busy: str | None = None
        self.last_result: str | None = None

    @property
    def warm(self) -> bool:
        return self.players_db is not None

    def ensure_warm(self) -> None:
        if self.warm or self.warm_error:
            return
        with self._lock:
            if self.warm or self.warm_error:
                return
            t0 = time.perf_counter()
            try:
                import data_merger as dm
                import run_draft_battery as rdb
                # build_players_db_from_capture, NOT build_players_db: the latter is a 764-row
                # VENDOR RECONSTRUCTION in a different id space with no eligibility, and only
                # 373 ids collide with the real universe -- coincidentally (`#201`). A live
                # roster's Sleeper ids resolve against the capture-backed db and nothing else.
                self.players_db, _prov = rdb.build_players_db_from_capture()
                self.merger = dm.DataMerger()
                self.byes = self.merger.bye_week_by_team()
                self.warm_seconds = time.perf_counter() - t0
                self.last_result = f"warm-up ok ({len(self.players_db)} players)"
            except Exception as exc:  # reported, never swallowed
                self.warm_error = f"{type(exc).__name__}: {exc}"
                self.last_result = f"warm-up FAILED -- {self.warm_error}"


ENGINE = Engine()


def _shell(title: str, body: str) -> str:
    """The status surface's own chrome. Deliberately plain: this is an instrument, not a page."""
    return (
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{html.escape(title)}</title><style>"
        ":root{--bg:#0b0d10;--fg:#e8eaed;--dim:#9aa3ad;--bad:#ff6b6b;--ok:#4ec9a0;"
        "--warn:#e0b050;--line:#232a32}"
        "@media(prefers-color-scheme:light){:root:not([data-theme=\"dark\"])"
        "{--bg:#fbfbfc;--fg:#15181c;--dim:#5b646e;--line:#dfe3e8}}"
        "body{margin:0;background:var(--bg);color:var(--fg);padding:28px 16px;"
        "font:400 15px/1.55 ui-monospace,SFMono-Regular,Menlo,monospace}"
        "main{max-width:860px;margin:0 auto}h1{font-size:1.15rem;margin:0 0 4px}"
        "h2{font-size:.82rem;letter-spacing:.09em;text-transform:uppercase;color:var(--dim);"
        "margin:26px 0 8px;font-weight:600}"
        "table{border-collapse:collapse;width:100%;font-size:.86rem}"
        "td,th{text-align:left;padding:5px 10px 5px 0;border-bottom:1px solid var(--line);"
        "vertical-align:top}th{color:var(--dim);font-weight:600}"
        ".bad{color:var(--bad);font-weight:700}.ok{color:var(--ok)}.warn{color:var(--warn)}"
        ".dim{color:var(--dim)}a{color:inherit}code{color:var(--dim)}"
        "</style></head><body><main>" + body + "</main></body></html>")


def _rows(pairs) -> str:
    return "".join(f"<tr><th>{html.escape(str(k))}</th><td>{v}</td></tr>" for k, v in pairs)


async def index(request):
    ENGINE.ensure_warm()
    snaps = ls.available_snapshots()
    fixtures = sorted(p.name for p in (ROOT / "ui_explore").glob("*_fixture.json"))
    if snaps:
        snap_html = "".join(
            f'<tr><th><a href="/league/{html.escape(s)}">{html.escape(s)}</a></th>'
            f'<td class="dim">snapshot</td></tr>' for s in snaps)
    else:
        # NOT an empty table. An empty list here means app.py has never synced, and saying so is
        # the difference between a diagnostic and a blank page.
        snap_html = ('<tr><td colspan="2" class="warn">No snapshot on disk. '
                     '<code>data/sleeper_snapshots/</code> is empty, so no league has been '
                     'synced by <code>app.py</code> yet. Sync one there, then reload.</td></tr>')
    fx_html = "".join(
        f'<tr><th><a href="/fixture/{html.escape(f)}">{html.escape(f)}</a></th>'
        f'<td class="dim">committed fixture &mdash; NOT your league</td></tr>' for f in fixtures)
    return HTMLResponse(_shell("Gold Wyrm — local", (
        "<h1>Gold Wyrm, read-only, localhost</h1>"
        '<p class="dim">This server writes nothing. <code>app.py</code> remains the only '
        "writer.</p>"
        "<h2>Your leagues</h2><table>" + snap_html + "</table>"
        "<h2>Fixtures</h2><table>" + fx_html + "</table>"
        '<h2>Diagnostics</h2><table><tr><th><a href="/status">/status</a></th>'
        '<td class="dim">engine, freshness, active operation, per-field wire check</td>'
        "</tr></table>")))


#: Extracted images, keyed by content hash. Written only by `_render`, and a hash key always maps
#: to identical bytes, so two threads racing on the same key write the same value -- which is why
#: this needs no lock. It is a cache, not state: an entry missing is a 404 on one image, and the
#: next render of that page puts it back.
ASSETS: dict[str, pa.Asset] = {}


def _render(fx, report) -> HTMLResponse:
    """Build the page, externalise its images, and put the source's verdict ABOVE it when the
    wire is wrong.

    A banner rather than a quiet field, because a failed read must not be mistakable for the
    absence contract behaving well -- which is the entire reason this module exists.
    """
    page, found = pa.externalize(DASH.build(fx))
    ASSETS.update(found)
    if report.failures:
        names = ", ".join(f.name for f in report.failures)
        banner = (
            '<div style="background:#2a0f12;color:#ffb3b3;border-bottom:2px solid #ff6b6b;'
            'padding:12px 16px;font:600 14px/1.5 ui-monospace,Menlo,monospace">'
            f"WIRED WRONG &mdash; {len(report.failures)} expected field(s) did not arrive: "
            f"{html.escape(names)}. These are NOT absences in your data; the read is at fault. "
            '<a href="/status" style="color:#fff">/status</a></div>')
        page = page.replace("<body>", "<body>" + banner, 1)
    return HTMLResponse(page)


async def league(request):
    ENGINE.ensure_warm()
    league_id = request.path_params["league_id"]
    path = ls.snapshot_path(league_id)
    if not path.exists():
        return HTMLResponse(_shell("No snapshot", (
            f"<h1>No snapshot for {html.escape(league_id)}</h1>"
            f'<p class="warn">Expected <code>{html.escape(str(path))}</code>. '
            f"<code>app.py</code> writes it on sync; this server never does.</p>"
            '<p><a href="/">back</a></p>')), status_code=404)
    if not ENGINE.warm:
        return HTMLResponse(_shell("Engine cold", (
            "<h1>Engine did not warm</h1>"
            f'<p class="bad">{html.escape(ENGINE.warm_error or "unknown")}</p>')),
            status_code=503)
    try:
        snap = json.loads(path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        return HTMLResponse(_shell("Unreadable snapshot", (
            f"<h1>Snapshot unreadable</h1><p class=\"bad\">{html.escape(str(exc))}</p>"
            '<p class="dim">Re-sync in app.py; a corrupt cache is a cache miss, not data '
            "loss.</p>")), status_code=500)
    # Priced under the lock, because `set_league_format` mutates the shared merger.
    with ENGINE._price_lock:
        ENGINE.busy = f"pricing {league_id}"
        try:
            fx, report = ls.from_snapshot(snap, ENGINE.players_db, ENGINE.byes,
                                          owner_id=request.query_params.get("owner"),
                                          merger=ENGINE.merger)
            ENGINE.last_result = f"rendered {league_id}: {report.verdict}"
        except Exception as exc:
            ENGINE.last_result = f"render FAILED for {league_id}: {type(exc).__name__}: {exc}"
            raise
        finally:
            ENGINE.busy = None
    return _render(fx, report)


async def fixture(request):
    name = request.path_params["name"]
    path = (ROOT / "ui_explore" / name).resolve()
    # Path containment, checked rather than assumed.
    if path.parent != (ROOT / "ui_explore").resolve() or not path.exists():
        return PlainTextResponse("no such fixture", status_code=404)
    fx, report = ls.from_fixture(path)
    return _render(fx, report)


async def health(request):
    """A liveness probe that does NOT warm the engine.

    Every other route calls `ensure_warm`, which builds a 6,594-player universe and a DataMerger
    -- around 450ms here and longer on a cold disk. A tunnel or proxy checking whether the origin
    is up should not pay that, and more usefully: if THIS answers through the tunnel while `/`
    does not, the problem is warm-up time or a request timeout, not connectivity. If neither
    answers, nothing is listening on this port from the tunnel's point of view.
    """
    return PlainTextResponse(
        f"ok  warm={ENGINE.warm}  uptime={ls.age_seconds(ENGINE.started_at):.0f}s  "
        f"writes=0\n")


async def asset(request):
    """Serve one content-addressed image, cached for a year and never revalidated.

    `immutable` is only honest because the NAME IS THE CONTENT HASH: change the image and the
    URL changes with it, so a stale entry is unreachable rather than wrong. The two halves are
    one decision (`#358`).
    """
    item = ASSETS.get(request.path_params["name"])
    if item is None:
        # A cold server has rendered no page yet, so it holds no assets. Saying so beats a bare
        # 404: the fix is to load the page that references it, not to hunt for a missing file.
        return PlainTextResponse(
            "no such asset in this process. Assets are extracted when a page renders; "
            "load the page first.", status_code=404)
    return Response(item.body, media_type=item.content_type,
                    headers={"Cache-Control": pa.CACHE_CONTROL})


async def status(request):
    ENGINE.ensure_warm()
    snaps = ls.available_snapshots()
    engine_rows = [
        ("engine initialized", f'<span class="ok">yes</span> &mdash; '
         f'{len(ENGINE.players_db):,} players, warm-up '
         f'{ENGINE.warm_seconds * 1000:.0f}ms' if ENGINE.warm
         else f'<span class="bad">NO</span> &mdash; {html.escape(ENGINE.warm_error or "?")}'),
        ("server uptime", f"{ls.age_seconds(ENGINE.started_at):.0f}s"),
        ("active operation", html.escape(ENGINE.busy) if ENGINE.busy
         else '<span class="dim">none</span>'),
        ("last operation result", html.escape(ENGINE.last_result or "—")),
        ("writes performed", '<span class="ok">0 &mdash; this server is read-only</span>'),
        ("leagues with a snapshot", str(len(snaps)) if snaps
         else '<span class="warn">0 &mdash; app.py has not synced</span>'),
    ]
    body = ["<h1>Status</h1><h2>Server</h2><table>" + _rows(engine_rows) + "</table>"]

    for league_id in snaps:
        try:
            snap = json.loads(ls.snapshot_path(league_id).read_text())
            with ENGINE._price_lock:
                fx, report = ls.from_snapshot(snap, ENGINE.players_db, ENGINE.byes,
                                              merger=ENGINE.merger)
        except Exception as exc:
            body.append(f'<h2>{html.escape(league_id)}</h2>'
                        f'<p class="bad">{html.escape(type(exc).__name__)}: '
                        f'{html.escape(str(exc))}</p>')
            continue
        age = ls.age_seconds(report.synced_at)
        cls = "bad" if report.failures else "ok"
        rows = "".join(
            f'<tr><th>{html.escape(r["field"])}</th>'
            f'<td class="{"bad" if r["state"] == ls.READ_FAILED else "dim"}">'
            f'{html.escape(r["state"])}</td>'
            f'<td class="dim">{html.escape(r["why"][:120])}</td></tr>'
            for r in report.as_rows())
        body.append(
            f'<h2>{html.escape(league_id)}</h2>'
            f'<p class="{cls}">{html.escape(report.verdict)}</p>'
            f'<table><tr><th>last successful sync</th><td>'
            f'{"%.0fs ago" % age if age is not None else "<span class=\'warn\'>unknown</span>"}'
            f'</td><td class="dim">data version: synced_at='
            f'{html.escape(str(report.synced_at))}</td></tr>'
            f'<tr><th>claims composed</th><td>{len(fc.compose(fx)["shown"])} shown</td>'
            f'<td class="dim">checks: '
            f'{html.escape(json.dumps(fc.checks_summary(fc.compose(fx).get("checks"))["absent"]))}'
            f' absent</td></tr>' + rows + "</table>")
    return HTMLResponse(_shell("Status", "".join(body)))


#: GZIP IS KEPT, AND MEASURED TO BE THE WRONG TRADE FOR MILESTONE 1. Starlette compresses nothing
#: by default -- the dashboard went over the wire at 226,303 bytes with `Accept-Encoding: gzip`
#: on the request and no `Content-Encoding` on the response. Turning it on, measured here:
#:
#:     plain   226,303 bytes    3.6 ms
#:     gzip    151,936 bytes   11.5-12.0 ms
#:
#: So it buys 74KB for ~8ms of CPU, and milestone 1 is LOOPBACK ONLY, where those 74KB cost
#: nothing to send. On this binding it is a net latency loss, and saying otherwise would be
#: quoting the byte count and hiding the clock.
#:
#: It stays for two reasons, both stated rather than assumed. It is the right trade the moment
#: there is a network (milestone 2), and 12ms is imperceptible either way. And the arithmetic
#: CHANGES once the real repair lands: 83% of this page is three inlined base64 images, and
#: JPEG/PNG/WebP are already compressed, so gzip is currently paying full price to recover
#: base64's inflation and nothing more. Content-address those three and the HTML drops to ~38KB,
#: where gzip reaches ~10KB for almost no CPU. THE ORDER MATTERS: content-addressing first, then
#: this is free. Doing it the other way round -- which is the order I did it in -- optimises the
#: part that cannot be compressed.
app = Starlette(
    routes=[
        Route("/", index),
        Route("/status", status),
        Route("/health", health),
        Route("/league/{league_id}", league),
        Route("/fixture/{name}", fixture),
        Route("/assets/{name}", asset),
    ],
    middleware=[Middleware(GZipMiddleware, minimum_size=1024)],
)


def main() -> int:
    import uvicorn
    where = "loopback only" if HOST in ("127.0.0.1", "localhost") else (
        f"*** BOUND TO {HOST} -- reachable by anything that can route to this host ***")
    print(f"Gold Wyrm, read-only, on http://{HOST}:{PORT}  ({where})")
    print(f"  probe:  curl -s http://{HOST}:{PORT}/health     (does not warm the engine)")
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
