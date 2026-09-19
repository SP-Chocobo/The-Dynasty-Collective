"""#102: one read-modify-write discipline for every JSON store in this app.

TWO FAILURES, BOTH DEMONSTRATED before anything here was written -- §7.8's rule is that this
programme does not make production changes for undemonstrated failures, and one half of #102 was
recorded as undemonstrated.

  1. LOST UPDATE (already demonstrated in the audit; re-run against today's code, still live).
     Every store did load -> mutate -> write_text with no lock. Tab A writes an objective, tab B
     reads, tab A writes a second, tab B saves its stale view -- tab A's second objective is
     gone. §16.9 widened it from per-league stores to GLOBAL ones: save_alias/remove_alias are
     the same shape on player_aliases.json, which feeds valuation. Re-demonstrated there too.

  2. TORN READ -- newly demonstrated here, and it is the WORSE half. One process rewriting a
     718 KB store while three read it, on a real filesystem, through the same Path.read_text /
     write_text calls every store used: of 98,405 reads, 3,920 were clean. 2,529 raised
     JSONDecodeError and 91,956 read an EMPTY FILE, because write_text truncates before it
     writes.

     The amplifier is the shape every _load in this tree already had:

         except (json.JSONDecodeError, OSError):
             return []

     A transient read error becomes an empty store, and the next ordinary write PERSISTS that.
     Measured end to end: a store holding five objectives, given one torn read, holds exactly one
     after the next add_todo -- the new one. Four are gone, silently, with no race between two
     writers required. One writer mid-write and one reader is enough.

THE MECHANISM, and why it is one mechanism rather than two.

`os.replace` is atomic: a reader sees the complete old file or the complete new file, never a
prefix. That removes failure 2 at its source rather than teaching every reader to cope with it.
The lock then removes failure 1, by making load-and-write one indivisible step -- which is why
`mutate` LOADS for you. A caller cannot accidentally read outside the lock, because it never
reads at all.

Two lock layers, both needed and covering different cases:
  * a process-wide threading.Lock, because Streamlit serves many browser tabs from ONE process,
    so the common multi-tab case is threads and not processes at all; and
  * an OS file lock on a sidecar `.lock` file, for genuinely separate processes (a second
    `streamlit run`, a phone and a laptop against a synced directory).
The sidecar is not incidental: the data file's inode is replaced on every write, so a lock held
on it would protect a file that no longer exists.

WHAT IS DELIBERATELY NOT SOLVED. A lock is advisory and a network filesystem may not honour it;
LOCKING names what actually engaged so a caller can report the truth rather than assume the
strong case. And a store that arrives already corrupt -- from a crash before this module existed,
or a disk error -- is NOT overwritten: `mutate` skips its write and leaves the damaged bytes in
place. Losing the one item being added beats losing everything already there, and the file stays
recoverable instead of being replaced by a one-element store.
"""

from __future__ import annotations

import functools
import json
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any

try:                                              # POSIX
    import fcntl
    LOCKING = "fcntl"
except ImportError:                               # pragma: no cover - Windows
    fcntl = None
    try:
        import msvcrt
        LOCKING = "msvcrt"
    except ImportError:                           # pragma: no cover - neither
        msvcrt = None
        LOCKING = "threads-only"

# One lock per path, and one lock guarding the registry itself. Keyed by path string so two
# spellings of the same file cannot take two different locks.
#
# RLock, and a per-thread depth count for the FILE lock, because these stores call each other:
# a public function holds the lock for its whole body (see the `atomic` decorator) and the _load
# and _save inside it may take it again. A plain Lock deadlocks on the second acquire, and flock
# on a SECOND descriptor for the same file deadlocks even though the same thread holds it -- so
# the depth count is not belt-and-braces, it is what makes nesting work at all.
_locks: dict[str, threading.RLock] = {}
_registry_lock = threading.Lock()
_depth = threading.local()

# Stores that could not be parsed and were therefore NOT overwritten. A dict rather than a
# counter so a consumer can name the file to the user -- an unreadable store the app silently
# works around is the same "looks handled" failure an unread annotation is.
_unreadable: dict[str, str] = {}


def _thread_lock(path: Path) -> threading.RLock:
    key = str(path)
    with _registry_lock:
        lock = _locks.get(key)
        if lock is None:
            lock = _locks[key] = threading.RLock()
        return lock


def _held(path: Path) -> dict:
    counts = getattr(_depth, "counts", None)
    if counts is None:
        counts = _depth.counts = {}
    return counts


@contextmanager
def _file_lock(path: Path):
    """An exclusive OS lock held on `<path>.lock` for the duration of the block.

    The sidecar exists because `write` replaces the data file: a lock taken on its inode would
    outlive the file it was protecting. Total -- if the platform has no lock primitive, or the
    filesystem refuses one, the block still runs under the thread lock rather than failing the
    user's write outright.
    """
    key = str(path)
    counts = _held(path)
    if counts.get(key):
        # Already held by this thread further up the stack. Re-taking the OS lock on a second
        # descriptor would block on ourselves forever.
        counts[key] += 1
        try:
            yield
        finally:
            counts[key] -= 1
        return
    lock_path = path.with_name(path.name + ".lock")
    handle = None
    try:
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        handle = open(lock_path, "a+b")
        if LOCKING == "fcntl":
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        elif LOCKING == "msvcrt":                 # pragma: no cover - Windows
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
    except Exception:                             # noqa: BLE001 - advisory, never fatal
        if handle is not None:
            handle.close()
            handle = None
    counts[key] = 1
    try:
        yield
    finally:
        counts[key] -= 1
        if handle is not None:
            try:
                if LOCKING == "fcntl":
                    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                elif LOCKING == "msvcrt":         # pragma: no cover - Windows
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            except Exception:                     # noqa: BLE001
                pass
            handle.close()


@contextmanager
def locked(path: Path):
    """Both lock layers, in a fixed order, for a block that touches `path`."""
    with _thread_lock(path), _file_lock(path):
        yield


#: What `unreadable_stores()` reports for a damaged store. One spelling, because three sites
#: wrote it out by hand and a UI that matched on the text would have been matching on whichever
#: of them happened to run.
UNREADABLE_REASON = "could not be parsed -- left untouched rather than overwritten"


def _parse(path: Path, default: Any) -> tuple[Any, bool]:
    """(value, readable). `readable` is False only when the file exists, is NOT empty, and does
    not parse -- the one case where returning the default would be a claim rather than a fact.

    An absent file and an empty file are both legitimately "nothing stored yet"; a file with
    bytes in it that are not JSON is damage, and this module refuses to let a later write
    overwrite it. That is the same distinction this codebase draws everywhere else between an
    absence and a value.
    """
    try:
        raw = path.read_text()
    except FileNotFoundError:
        return default, True
    except OSError:
        return default, False
    if not raw.strip():
        return default, True
    try:
        return json.loads(raw), True
    except json.JSONDecodeError:
        return default, False


def read_state(path: Path, default: Any) -> tuple[Any, bool]:
    """(value, readable) -- `read` with the one bit `read` throws away.

    A caller that must tell DAMAGE from ABSENCE needs this, and the alternative is what
    outcome_record did: hand-roll a second `json.loads` beside this module, get the same
    `None` for both states, and never arm the damage mark that stops the next write
    destroying the file (#52 phase 7.5). A second parser that is supposed to agree with this
    one is the drift class this module exists to end -- so the distinction is published here
    rather than re-derived there.

    `readable` is False only for a file that exists, holds bytes, and does not parse. Absent
    and empty are both honestly "nothing stored yet" and come back readable.
    """
    with locked(path):
        value, readable = _parse(path, default)
    _note_readability(path, readable)
    return value, readable


def read(path: Path, default: Any) -> Any:
    """One store's contents, or `default`. Takes the lock so a read cannot land mid-write.

    Still returns the default for an unreadable file -- callers are fail-soft by design and a
    read is not the place to start raising -- but records it in `unreadable_stores()` so the
    condition can be surfaced, and so `mutate` knows not to overwrite it. A caller that needs
    to tell those two apart asks `read_state`.
    """
    return read_state(path, default)[0]


def _note_readability(path: Path, readable: bool) -> None:
    """Arm or clear the damage mark for one store. One place, because `read_state` and
    `mutate` must not be able to disagree about what damage means."""
    if readable:
        # A store that parsed is not damaged, whatever an earlier read of it concluded -- a
        # mark that outlived its cause would keep refusing writes to a file that is now fine.
        _unreadable.pop(str(path), None)
    else:
        _unreadable[str(path)] = UNREADABLE_REASON


def write(path: Path, data: Any) -> bool:
    """Replace `path` with `data`, atomically. Returns whether the bytes actually landed.

    The temp file is created in the SAME directory on purpose: os.replace is only atomic within
    one filesystem, and a temp directory elsewhere would silently degrade to a copy.

    RETURNS A BOOL because this function can decline, and used to decline in silence (#52
    phase 7.5). Refusing to overwrite a damaged store is right; saying nothing about it is not
    -- this module's own `unreadable_stores` docstring makes the argument: "a store the app
    quietly works around is exactly the failure that looks handled." Measured downstream:
    `upload_batches.record` returned a batch id for a batch that never reached disk and could
    not be found by that id, while the UI reported success and the user's stated as-of date was
    gone.

    Additive by construction: every one of the callers that ignore the result keeps its exact
    behaviour, and a caller that must report success to a person can now ask.
    """
    with locked(path):
        # The guard that makes the read/write pair as safe as `mutate`. A store this process
        # has found unparseable is NOT replaced: the alternative writes a one-element file over
        # whatever was recoverable, which is precisely how a transient torn read became
        # permanent data loss. The mark clears itself as soon as the file parses again.
        if str(path) in _unreadable:
            return False
        _write_unlocked(path, data)
        return True


def replace_atomically(path: Path, text: str) -> None:
    """Replace `path` with `text` so no reader ever sees a prefix. NO STORE SEMANTICS.

    The mechanism this module's docstring measures -- write a sibling temp file, then
    `os.replace`, which is atomic within one filesystem -- published on its own for callers
    that need the atomicity and must NOT have the rest.

    THE DISTINCTION IS THE WHOLE REASON THIS IS SEPARATE (#52 phase 7.5 / J-13). `write` above
    refuses to overwrite a store it has found damaged, because for a STORE the damaged bytes
    are the only copy and losing them is unrecoverable. A CACHE is the opposite: it is
    re-fetchable by definition, so a corrupt one SHOULD be replaced by a fresh fetch, and
    giving it the store's protection would make a corrupt cache permanently un-refreshable --
    a worse bug than the one being fixed, installed by the fix.

    So this does no locking, keeps no damage mark, and consults none. It is the atomicity and
    nothing else. A caller holding durable data wants `write` or `mutate`; a caller holding a
    rebuildable copy of someone else's data wants this.

    Takes TEXT rather than an object on purpose: the ~10 MB players cache is written compact,
    and routing it through `write`'s `json.dumps(indent=2)` would inflate it by ~30% for a file
    no person reads.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp.write_text(text)
    os.replace(tmp, path)


def _write_unlocked(path: Path, data: Any) -> None:
    replace_atomically(path, json.dumps(data, indent=2))


@contextmanager
def mutate(path: Path, default: Any):
    """Load, yield for mutation, write back -- the whole read-modify-write under one lock.

    This is the API the stores use, and it takes the load away from the caller ON PURPOSE. The
    lost update was never a missing lock so much as a load that happened outside one; a caller
    that cannot read separately cannot reintroduce it.

    Yields a MUTABLE value (list or dict). Mutate it in place; rebinding the name inside the
    block writes nothing, the same way it would with any other context manager.

    Skips the write entirely when the existing file could not be parsed. The mutation is lost --
    deliberately, and it is the smaller loss: the alternative replaces a damaged store with a
    one-element one and destroys whatever was recoverable.
    """
    with locked(path):
        value, readable = _parse(path, default)
        yield value
        if readable:
            _write_unlocked(path, value)
        else:
            _unreadable[str(path)] = UNREADABLE_REASON


def atomic(path_for):
    """Run the whole decorated function under one lock on the store it touches.

    `path_for(*args, **kwargs) -> Path` names the file from the call's own arguments, since the
    per-league stores derive their path from a league_id argument and the global ones ignore it.

    This is the shape the existing stores take, and it is chosen over rewriting each of them
    around `mutate` for one reason: the lost update was a LOAD THAT HAPPENED OUTSIDE A LOCK, and
    a decorator on the public function puts the load and the save inside the same one without
    touching the body in between. New code should prefer `mutate`, which makes the mistake
    unavailable rather than merely fixed.
    """
    def decorate(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with locked(Path(path_for(*args, **kwargs))):
                return func(*args, **kwargs)
        return wrapper
    return decorate


def unreadable_stores() -> dict[str, str]:
    """Every store this process found unparseable, path -> what happened. For the UI to surface:
    a store the app quietly works around is exactly the failure that looks handled."""
    return dict(_unreadable)


def clear_unreadable() -> None:
    """For tests, and for a UI that has shown the notice and does not want to repeat it."""
    _unreadable.clear()
