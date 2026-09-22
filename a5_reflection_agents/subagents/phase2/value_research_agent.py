"""Phase 2: Value Research Agent (Kabir) - Research 2
===================================================
Mandatory creates a proposal at-max 10% below budget ($B * 0.90 <= Cost <= B * 1.00).
It must NOT cross the budget.
Includes at-least 1 hotel and 3 visiting places, and at-max 2 hotels and 5 visiting places.
Researches boutique stays, smart travel passes, and authentic hidden gems.
Strictly gathers web research information in at most 3 to 5 web searches total.
Supports up to 2 iterations for proposal rectification before cancellation.
Reports value research findings back to Eval Agent (Ishaan) or passes directly to Advik if budget is inappropriate.
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
    from a5_reflection_agents.tools.web_search_tool import web_search

try:
    from .p2_instructions import PHASE2_VALUE_RESEARCH_INSTRUCTIONS
except ImportError:
    try:
        from p2_instructions import PHASE2_VALUE_RESEARCH_INSTRUCTIONS
    except ImportError:
        from subagents.phase2.p2_instructions import PHASE2_VALUE_RESEARCH_INSTRUCTIONS

# Phase 2 Research Agent 2: Value & Diverse Places (Kabir)
value_research_agent = Agent(
    name="kabir",
    description=(
        "Phase 2 Research Agent 2 (Kabir). Mandatory creates a proposal at-max 10% below budget (90%–100%), "
        "never crossing the budget. Includes at-least 1 hotel and 3 places to visit, and at-max 2 hotels and 5 places to visit. "
        "Researches boutique hotels, cost-effective travel passes, and unique alternate places/hidden gems using web_search, "
        "gathering all information in maximum 3 to 5 web searches total. "
        "If budget is not appropriate for the requested trip, sends details directly to Advik (finalizer_agent) to output 'No Trip possible'. "
        "Supports up to 2 iterations for proposal rectification before cancellation."
    ),
    model=MODEL_NAME,
    tools=[web_search],
    instruction=PHASE2_VALUE_RESEARCH_INSTRUCTIONS,
    sub_agents=[],
)

# Aliases for flexible imports across multi-agent workflows
research2_agent = value_research_agent
kabir_agent = value_research_agent
