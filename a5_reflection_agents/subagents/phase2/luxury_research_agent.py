"""Phase 2: Luxury Research Agent (Aarav) - Research 1
=====================================================
Mandatory creates a proposal 10%–20% above budget ($B * 1.10 <= Cost <= B * 1.20)
with at-least 1 hotel and 5 visiting places, and at-max 2 hotels and 7 visiting places,
unless Eval Agent provides a specific budget range to fit in, in which case produces
a proposal strictly in that decided range.
Researches high-end luxury upgrades (5-star to 7-star hotels, premier spas, gourmet dining).
Strictly gathers web research information in at most 3 to 5 web searches total.
Supports up to 3 iterations for proposal rectification before cancellation.
Reports luxury research findings back to Eval Agent (Ishaan).
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
    from .p2_instructions import PHASE2_LUXURY_RESEARCH_INSTRUCTIONS
except ImportError:
    try:
        from p2_instructions import PHASE2_LUXURY_RESEARCH_INSTRUCTIONS
    except ImportError:
        from subagents.phase2.p2_instructions import PHASE2_LUXURY_RESEARCH_INSTRUCTIONS

# Phase 2 Research Agent 1: Luxury Upgrade & +10%–20% Stretch (Aarav)
luxury_research_agent = Agent(
    name="aarav",
    description=(
        "Phase 2 Research Agent 1 (Aarav). Mandatory creates a luxury proposal 10%–20% above budget, "
        "including at-least 1 hotel and 5 places to visit, and at-max 2 hotels and 7 places to visit, "
        "unless Eval Agent provides a specific budget range to fit in, in which case produces a proposal "
        "strictly in that decided range. Researches 5-star to 7-star hotels, spas, and gourmet dining using web_search, "
        "gathering all information in maximum 3 to 5 web searches total. "
        "Supports up to 3 iterations for proposal rectification before cancellation."
    ),
    model=MODEL_NAME,
    tools=[web_search],
    instruction=PHASE2_LUXURY_RESEARCH_INSTRUCTIONS,
    sub_agents=[],
)

# Aliases for flexible imports across multi-agent workflows
research1_agent = luxury_research_agent
aarav_agent = luxury_research_agent
