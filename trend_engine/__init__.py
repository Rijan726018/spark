"""trend_engine — daily content-idea generator from live trend signals.

Pulls momentum signals (Google Trends realtime + YouTube Data API), ranks what's
rising in a creator's niche, and turns the top signals into ready-to-shoot ideas.
"""
from .env import load_env

# Load .env (if present) before anything reads os.environ.
load_env()

from .pipeline import run

__version__ = "0.1.0"
__all__ = ["run"]
