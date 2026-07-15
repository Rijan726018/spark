"""
Deprecated shim — imports forwarded to engines.indicators (the canonical source).
Update your imports to: from engines.indicators import <function>
"""
from engines.indicators import (  # noqa: F401
    bollinger_bands,
    cumulative_volume_delta,
    detect_cvd_divergence,
)
