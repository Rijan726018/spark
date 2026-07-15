"""
ConfigLoader — unified algo config access layer.

Priority order:
  1. algo_configs.json  (preferred: fast load, diffable, no Python import)
  2. algo_configs.py    (legacy fallback while migration is in progress)

Run scripts/migrate_configs_to_json.py once to generate algo_configs.json.
After that, algo_configs.py can be removed.
"""
import importlib.util
import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger("nexus.config_loader")

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_JSON_PATH    = _PROJECT_ROOT / "algo_configs.json"
_PY_PATH      = _PROJECT_ROOT / "algo_configs.py"


def _normalize(cfg: dict) -> dict:
    """Coerce a raw config dict into the canonical shape the API expects."""
    return {
        "id":           str(cfg.get("id", "000")).zfill(3),
        "name":         str(cfg.get("name", "Unnamed")),
        "symbol":       str(cfg.get("market", cfg.get("symbol", "ES"))).replace("=F", ""),
        "tf":           str(cfg.get("timeframe", cfg.get("tf", "5m"))),
        "desc":         str(cfg.get("description", cfg.get("desc", ""))),
        "category":     str(cfg.get("category", "General")),
        "status":       str(cfg.get("status", "LIVE")),
        "win_rate":     float(cfg.get("win_rate", 55.0)),
        "profit_factor": float(cfg.get("profit_factor", 1.5)),
        "max_dd":       float(cfg.get("max_dd", 0.05)),
        "csv_path":     str(cfg.get("csv", cfg.get("csv_path", "")) or ""),
        "engine":       str(cfg.get("engine", "")),
        "params":       cfg.get("params", {}),
    }


def load_configs() -> list[dict]:
    """Return the full list of normalized algo configs."""
    if _JSON_PATH.exists():
        return _load_from_json(_JSON_PATH)
    if _PY_PATH.exists():
        return _load_from_py(_PY_PATH)
    logger.error("Neither algo_configs.json nor algo_configs.py found at %s", _PROJECT_ROOT)
    return []


def _load_from_json(path: Path) -> list[dict]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        configs = [_normalize(c) for c in raw]
        logger.info("Loaded %d algo configs from %s", len(configs), path.name)
        return configs
    except Exception as exc:
        logger.error("Failed to parse %s: %s", path, exc)
        return []


def _load_from_py(path: Path) -> list[dict]:
    try:
        spec = importlib.util.spec_from_file_location("algo_configs", path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        raw = getattr(mod, "ALGO_CONFIGS", [])
        configs = [_normalize(c) for c in raw]
        logger.info(
            "Loaded %d algo configs from algo_configs.py (run scripts/migrate_configs_to_json.py to migrate)",
            len(configs),
        )
        return configs
    except Exception as exc:
        logger.warning("Could not load algo_configs.py: %s", exc)
        return []
