"""Phase 3: Finalizer Agent (Advik)
==================================
Receives details from value_research_agent (Kabir): if budget is not appropriate,
outputs "No Trip possible" with shortfall details and curated alternative destinations.
Else, waits for the response from proposal_agent (Tanvi) with whichever proposal
the user selects, then prepares the final master draft for the user and Vicky,
completing the overall task.
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
    from tools.html_export_tool import generate_beautiful_proposal_html
except ImportError:
    try:
        from ...tools.html_export_tool import generate_beautiful_proposal_html
    except ImportError:
        generate_beautiful_proposal_html = None

try:
    from .p3_instructions import PHASE3_FINALIZER_INSTRUCTIONS
except ImportError:
    try:
        from p3_instructions import PHASE3_FINALIZER_INSTRUCTIONS
    except ImportError:
        from subagents.phase3.p3_instructions import PHASE3_FINALIZER_INSTRUCTIONS

finalizer_tools = [generate_beautiful_proposal_html] if generate_beautiful_proposal_html else []

# Phase 3 Finalizer Agent
finalizer_agent = Agent(
    name="advik",
    description=(
        "Phase 3 Finalizer Agent (Advik). Operating under Boss Agent Vicky. "
        "Receives pipeline intelligence: if budget is not appropriate (from Kabir), outputs 'No Trip possible'. "
        "From proposal_agent (Tanvi): if 0 proposals received, outputs 'no proposal was generated our research agents are busy' with alternatives; "
        "if 1 proposal received, prepares the final master draft directly without human input; "
        "if 2 proposals, prepares the final master draft using whichever proposal the user selected. "
        "For approved master proposals, generates a beautiful downloadable HTML proposal file (using generate_beautiful_proposal_html) "
        "for the user and Boss Agent Vicky. Completes the overall task."
    ),
    model=MODEL_NAME,
    tools=finalizer_tools,
    instruction=PHASE3_FINALIZER_INSTRUCTIONS,
)

# Aliases for flexible imports across multi-agent workflows
phase3_agent = finalizer_agent
advik_agent = finalizer_agent
