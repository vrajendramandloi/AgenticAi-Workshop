"""Phase 2: Statistic & Feasibility Agent (Dhruv)
==============================================
Conducts live budget feasibility analysis using at most 5 calls to web_search
to gather flight and hotel information.
Assumes the cost of all other activities equals the combined total of flight + hotel
(Overall Cost = 2 * (Flight + Hotel)).
Statistics is successful if overall cost <= budget; only fails if overall cost exceeds budget.
Reports structured findings back to Eval Agent (Ishaan).
"""

import os
import sys
from pathlib import Path

# Prevent bytecode generation
sys.dont_write_bytecode = True

# Ensure subagents, tools, and a5_reflection_agents root are in sys.path
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
    from tools.web_search_tool import web_search
except (ImportError, ModuleNotFoundError):
    try:
        from a5_reflection_agents.tools.web_search_tool import web_search
    except (ImportError, ModuleNotFoundError):
        from tools.web_search_tool import web_search

try:
    from .p2_instructions import PHASE2_STATISTIC_INSTRUCTIONS
except ImportError:
    try:
        from p2_instructions import PHASE2_STATISTIC_INSTRUCTIONS
    except ImportError:
        from subagents.phase2.p2_instructions import PHASE2_STATISTIC_INSTRUCTIONS


# Phase 2 Statistic & Feasibility Agent (Dhruv)
statistic_agent = Agent(
    name="dhruv",
    description=(
        "Phase 2 Statistic & Feasibility Agent (Dhruv). Operating under Boss Agent Vicky. "
        "Performs live budget feasibility analysis using at most 5 calls to web_search to gather flight and hotel costs. "
        "Assumes the cost of all other activities equals the combined total of flight + hotel (overall cost = 2 * (flight + hotel)). "
        "If overall cost is within budget, marks feasibility as successful ([FEASIBILITY_STATUS: BUDGET_FEASIBLE]); "
        "only fails ([FEASIBILITY_STATUS: BUDGET_LOW]) if overall cost exceeds budget. Reports findings back to Eval Agent."
    ),
    model=MODEL_NAME,
    tools=[web_search],
    instruction=PHASE2_STATISTIC_INSTRUCTIONS,
    sub_agents=[],
)

# Aliases for flexible imports across multi-agent workflows
phase2_agent = statistic_agent
dhruv_agent = statistic_agent


