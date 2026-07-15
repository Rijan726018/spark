"""Zero-dependency .env loader.

Reads KEY=VALUE lines from a .env file at the project root into os.environ,
without overwriting variables that are already set in the real environment.
Avoids a python-dotenv dependency.
"""
from __future__ import annotations

import os
from pathlib import Path

_LOADED = False


def load_env(path: str | os.PathLike | None = None, override: bool = False) -> None:
    global _LOADED
    if _LOADED and path is None:
        return
    env_path = Path(path) if path else (Path(__file__).resolve().parent.parent / ".env")
    if not env_path.exists():
        _LOADED = True
        return
    for raw in env_path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if not key:
            continue
        if override or key not in os.environ:
            os.environ[key] = val
    _LOADED = True
