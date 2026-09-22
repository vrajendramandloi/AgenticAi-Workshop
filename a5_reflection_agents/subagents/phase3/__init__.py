"""Phase 3 Subagents Package
===========================
Synthesizes all intelligence from Phase 1 and Phase 2 into the definitive
master proposal and executive draft summary.
- `finalizer_agent` (Advik): Executive editor and proposal finalizer.
"""

from .finalizer_agent import finalizer_agent, advik_agent, phase3_agent

__all__ = [
    "finalizer_agent",
    "advik_agent",
    "phase3_agent",
]
