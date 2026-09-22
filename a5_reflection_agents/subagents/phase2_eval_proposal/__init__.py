"""Phase 2 Eval Proposal Package
================================
Client-facing proposal presentation and option selection module.
- `proposal_agent` (Tanvi): Presents vetted options and prompts user for decision.
"""

from .proposal_agent import proposal_agent, tanvi_agent, option_selection_agent

__all__ = [
    "proposal_agent",
    "tanvi_agent",
    "option_selection_agent",
]
