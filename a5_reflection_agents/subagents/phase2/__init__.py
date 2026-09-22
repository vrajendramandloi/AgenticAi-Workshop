"""Phase 2 Subagents Package
============================
Specialized statistical feasibility, market research & quality evaluation squad:
- `statistic_agent` (Dhruv): Core feasibility, baseline flight & hotel research, budget viability.
- `luxury_research_agent` (Aarav): Research 1 - Luxury upgrade with +10%–25% budget stretch (5-7 star stays, spas, fine dining).
- `value_research_agent` (Kabir): Research 2 - Smart value, alternative places to visit, and travel passes within budget (90%–100%).
- `eval_agent` (Ishaan): Quality & Budget Auditor. Checks feasibility, audits +10%–25% luxury bounds and <=100% value bounds, and routes to Proposal Agent.
- `phase2_parallel_agent`: Runs all three agents concurrently in parallel branches.
"""

from .statistic_agent import statistic_agent, dhruv_agent
from .luxury_research_agent import luxury_research_agent, research1_agent, aarav_agent
from .value_research_agent import value_research_agent, research2_agent, kabir_agent
from .parallel_agent import phase2_parallel_agent, phase2_agent, parallel_research_agent
from .eval_agent import eval_agent, ishaan_agent, quality_eval_agent, phase2_evaluator

__all__ = [
    "statistic_agent",
    "dhruv_agent",
    "luxury_research_agent",
    "research1_agent",
    "aarav_agent",
    "value_research_agent",
    "research2_agent",
    "kabir_agent",
    "phase2_parallel_agent",
    "phase2_agent",
    "parallel_research_agent",
    "eval_agent",
    "ishaan_agent",
    "quality_eval_agent",
    "phase2_evaluator",
]
