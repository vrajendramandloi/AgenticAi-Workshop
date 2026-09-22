"""Phase 2: Evaluation Agent (Ishaan) - Quality, Feasibility & Budget Auditor
========================================================================
Audits Dhruv's baseline feasibility analysis:
- If Dhruv reports budget is low/insufficient, DOES NOT accept any input from
  luxury or value research agents, terminates research immediately and routes to Advik.
Validates quotations from Aarav (luxury) and Kabir (value) using calculation_tools (validate_budget):
- Aarav: Mandatory 10%–20% above budget (or eval-prescribed range), 1–2 hotels, 5–7 places, max 3 iterations.
- Kabir: Mandatory at-max 10% below budget (never cross budget), 1–2 hotels, 3–5 places, max 2 iterations.
- If non-compliant after maximum iterations, cancels the proposal and moves on.
Sends surviving approved quotations (0, 1, or 2) to Proposal Agent (Tanvi).
"""

import os
import sys
from pathlib import Path

# Prevent bytecode generation
sys.dont_write_bytecode = True

# Ensure subagents, tools, and a5 root are in sys.path
_current_dir = Path(__file__).resolve().parent
_a5_root = _current_dir.parent.parent
_workspace_root = _a5_root.parent

for _p in [str(_a5_root), str(_workspace_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Load environment variables
try:
    from dotenv import find_dotenv, load_dotenv
    _root_env = _workspace_root / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
except ImportError:
    pass

# Synchronize API keys for google-genai and ADK
if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")

from google.adk.agents.llm_agent import Agent

try:
    from tools.calculation_tools import calculate_budget_breakdown, validate_budget
except (ImportError, ModuleNotFoundError):
    try:
        from a5_reflection_agents.tools.calculation_tools import calculate_budget_breakdown, validate_budget
    except (ImportError, ModuleNotFoundError):
        calculate_budget_breakdown = None
        validate_budget = None

try:
    from .p2_instructions import PHASE2_EVAL_INSTRUCTIONS
except ImportError:
    try:
        from p2_instructions import PHASE2_EVAL_INSTRUCTIONS
    except ImportError:
        from subagents.phase2.p2_instructions import PHASE2_EVAL_INSTRUCTIONS

# Import peer and subordinate agents
try:
    from .statistic_agent import statistic_agent
except ImportError:
    from subagents.phase2.statistic_agent import statistic_agent

try:
    from .luxury_research_agent import luxury_research_agent
except ImportError:
    from subagents.phase2.luxury_research_agent import luxury_research_agent

try:
    from .value_research_agent import value_research_agent
except ImportError:
    from subagents.phase2.value_research_agent import value_research_agent

try:
    from subagents.phase2_eval_proposal import proposal_agent
except ImportError:
    try:
        from ..phase2_eval_proposal import proposal_agent
    except ImportError:
        proposal_agent = None

try:
    from subagents.phase3 import finalizer_agent
except ImportError:
    try:
        from ..phase3 import finalizer_agent
    except ImportError:
        finalizer_agent = None

# Reset parent references to maintain single-parent ADK compliance across re-imports
eval_subagents = []
for _ag in [statistic_agent, luxury_research_agent, value_research_agent, proposal_agent, finalizer_agent]:
    if _ag:
        if getattr(_ag, "parent_agent", None) is not None:
            _ag.parent_agent = None
        eval_subagents.append(_ag)

eval_tools = [t for t in [validate_budget, calculate_budget_breakdown] if t is not None]

# Phase 2 Evaluation Specialist & Quality Auditor (Ishaan)
eval_agent = Agent(
    name="eval_agent",
    description=(
        "Phase 2 Quality, Feasibility & Budget Evaluation Specialist (Ishaan). Operating under Boss Agent Vicky. "
        "AUTO-STARTS Phase 2 immediately post Raghav hand-off by calling transfer_to_agent(agent_name='dhruv') for baseline feasibility. "
        "Strict gatekeeper: if Dhruv reports budget is low/insufficient, does NOT accept any input from Aarav or Kabir, "
        "cancels research immediately and delegates directly to Advik. "
        "Otherwise auto-orchestrates research with Aarav (luxury: 10%–20% above budget or eval-decided range, 1–2 hotels, 5–7 places, max 3 iterations) "
        "and Kabir (value: at-max 10% below budget, never cross budget, 1–2 hotels, 3–5 places, max 2 iterations) using validate_budget. "
        "Cancels non-compliant proposals after their iteration limit. Sends approved quotations (0, 1, or 2) directly to Proposal Agent (Tanvi)."
    ),
    model=MODEL_NAME,
    tools=eval_tools,
    instruction=PHASE2_EVAL_INSTRUCTIONS,
    sub_agents=eval_subagents,
)

# Aliases
ishaan_agent = eval_agent
quality_eval_agent = eval_agent
phase2_evaluator = eval_agent
