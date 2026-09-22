"""Phase 1: Quotation Agent (Raghav) - Human-in-the-Loop (HITL)
============================================================
First-line gatekeeper agent operating under Boss Agent Vicky.
Its sole responsibility is to receive initial user queries, analyze them
against required parameter pillars, and interactively query the human (HITL)
for any missing information before any downstream agents begin execution.
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
except ImportError:
    from ...tools.web_search_tool import web_search

try:
    from tools.init_tools.location_cache import location_cache
except ImportError:
    try:
        from init_tools.location_cache import location_cache
    except ImportError:
        from ...tools.init_tools.location_cache import location_cache

try:
    from .p1_instructions import PHASE1_QUOTATION_INSTRUCTIONS
except ImportError:
    try:
        from p1_instructions import PHASE1_QUOTATION_INSTRUCTIONS
    except ImportError:
        from subagents.phase1.p1_instructions import PHASE1_QUOTATION_INSTRUCTIONS


try:
    from subagents.phase2 import eval_agent
except ImportError:
    try:
        from ..phase2 import eval_agent
    except ImportError:
        eval_agent = None

if eval_agent and getattr(eval_agent, "parent_agent", None) is not None:
    eval_agent.parent_agent = None

# Phase 1 Quotation & Information Gathering Agent
quotation_agent = Agent(
    name="raghav",
    description=(
        "Phase 1 Quotation & Information Gathering Agent (Raghav). Front-line gatekeeper operating under Boss Agent Vicky. "
        "Responsible strictly for interacting with the human (HITL) to collect EVERY required parameter (destination, budget, duration, travelers, departure city, visa status). "
        "NEVER assume or guess missing values. Keep asking the human across multiple turns until 100% of information is obtained. "
        "Strictly prohibited from transferring to Phase 2 until all details are explicitly confirmed by the human. "
        "POST OBTAINING ALL DETAILS: Auto-starts Phase 2 immediately by calling transfer_to_agent(agent_name='eval_agent') in the exact same turn without waiting for user input."
    ),
    model=MODEL_NAME,
    tools=[web_search, location_cache.get_current_location],
    instruction=PHASE1_QUOTATION_INSTRUCTIONS,
    sub_agents=[eval_agent] if eval_agent else [],
)

# Aliases for flexible imports across multi-agent workflows
phase1_agent = quotation_agent
raghav_agent = quotation_agent

