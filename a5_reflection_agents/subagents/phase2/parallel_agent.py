"""Phase 2: Parallel Research Squad Orchestrator
===============================================
Fans out all Phase 2 agents in parallel:
1. `statistic_agent` (Dhruv): Statistical feasibility & baseline flight/hotel analysis.
2. `luxury_research_agent` (Aarav): +10% luxury stretch, 5-7★ stays, spas, fine dining.
3. `value_research_agent` (Kabir): Same budget smart value, hidden gem places, boutique stays, transit passes.

All three agents receive the verified parameter brief from Phase 1 (Raghav)
and execute their live web_search research simultaneously on separate branches.
"""

import sys
from pathlib import Path

# Prevent bytecode generation
sys.dont_write_bytecode = True

# Ensure subagents and root are in sys.path
_current_dir = Path(__file__).resolve().parent
_a5_root = _current_dir.parent.parent
_workspace_root = _a5_root.parent

for _p in [str(_a5_root), str(_workspace_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from google.adk.agents.parallel_agent import ParallelAgent

try:
    from .statistic_agent import statistic_agent
    from .luxury_research_agent import luxury_research_agent
    from .value_research_agent import value_research_agent
except ImportError:
    from subagents.phase2.statistic_agent import statistic_agent
    from subagents.phase2.luxury_research_agent import luxury_research_agent
    from subagents.phase2.value_research_agent import value_research_agent

for _agent in [statistic_agent, luxury_research_agent, value_research_agent]:
    if getattr(_agent, "parent_agent", None) is not None:
        _agent.parent_agent = None

phase2_parallel_agent = ParallelAgent(
    name="phase2_parallel",
    description=(
        "Phase 2 Parallel Research Squad. Simultaneously executes Dhruv (feasibility & baseline costs), "
        "Aarav (+10% luxury upgrade & 5-7 star stays), and Kabir (same-budget diverse places & transit passes) "
        "in parallel branches using all specifications gathered by Raghav."
    ),
    sub_agents=[statistic_agent, luxury_research_agent, value_research_agent],
)

# Aliases
phase2_agent = phase2_parallel_agent
parallel_research_agent = phase2_parallel_agent
