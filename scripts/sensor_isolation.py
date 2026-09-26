#!/usr/bin/env python3
"""Keep computational sensors side-effect free on the repository checkout.

Several sensors smoke-test real office CLIs (``vf_control_plane.py handoff``,
``vf_organic_growth.py brief --write``, ``vf_retro_signals.py --write``, the
commission matrix, ...). Those CLIs legitimately write their canonical outputs
when an operator or workflow runs them, but a *sensor* run must only read: it
must never leave refreshed HANDOFF/growth-brief/retro-signals files or new
state files behind for an agent to commit by accident.

``preserve_repo_files`` snapshots the exact bytes (and mtimes) of the listed
repo-relative files/directories before the sensor body runs and restores them
afterwards, even when the sensor fails (``SystemExit``). Files created inside a
preserved directory during the run are removed; files deleted are recreated.
The snapshot is taken at sensor start, so state written by an earlier workflow
step (e.g. ``vf_control_plane.py watchdog``) is kept exactly as it was.

Nothing here changes what a sensor asserts; it only undoes its writes.
"""
from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator

SKIP_DIRS = {"__pycache__", ".git"}


def _walk(path: Path) -> Iterator[Path]:
    if path.is_file():
        yield path
        return
    if not path.is_dir():
        return
    for dirpath, dirnames, filenames in os.walk(path):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def _snapshot(root: Path, rels: Iterable[str]) -> tuple[dict[Path, tuple[bytes, int]], list[Path], set[Path]]:
    files: dict[Path, tuple[bytes, int]] = {}
    dirs: list[Path] = []
    absent_files: set[Path] = set()
    for rel in rels:
        target = (root / rel).resolve()
        if target.is_dir():
            dirs.append(target)
        elif not target.exists():
            # Preserve absence: a listed file that does not exist must not be created.
            absent_files.add(target)
            continue
        for f in _walk(target):
            try:
                st = f.stat()
                files[f] = (f.read_bytes(), st.st_mtime_ns)
            except OSError:
                continue
    return files, dirs, absent_files


def _restore(files: dict[Path, tuple[bytes, int]], dirs: list[Path], absent_files: set[Path]) -> None:
    for f, (data, mtime_ns) in files.items():
        try:
            if not f.is_file() or f.read_bytes() != data:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(data)
            os.utime(f, ns=(mtime_ns, mtime_ns))
        except OSError:
            continue
    for d in dirs:
        for f in list(_walk(d)):
            if f not in files:
                try:
                    f.unlink()
                except OSError:
                    pass
        # Remove directories created during the run (deepest first), keep pre-existing ones.
        for dirpath, dirnames, _ in sorted(os.walk(d), key=lambda t: len(t[0]), reverse=True):
            p = Path(dirpath)
            if p == d or any(part in SKIP_DIRS for part in p.parts):
                continue
            if not any(k.is_relative_to(p) for k in files) and not any(p.iterdir()):
                try:
                    p.rmdir()
                except OSError:
                    pass
    for f in absent_files:
        try:
            if f.is_file():
                f.unlink()
        except OSError:
            pass


@contextmanager
def preserve_repo_files(root: Path, rels: Iterable[str]) -> Iterator[None]:
    """Restore ``rels`` (repo-relative files/dirs under ``root``) after the block."""
    files, dirs, absent_files = _snapshot(Path(root).resolve(), list(rels))
    try:
        yield
    finally:
        _restore(files, dirs, absent_files)
