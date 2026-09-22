"""Phase 2 Proposal Selection Agent (Tanvi)
=========================================
Receives evaluated quotations from Phase 2 Eval Agent (Ishaan) and applies strict proposal routing:
- If less than 1 proposal (0 proposals): Directly send to Advik saying "no proposal was generated our research agents are busy" (no human input).
- In case of 1 proposal: Directly send to Advik (do not take human input).
- Only in case of 2 proposals: Ask for human input to select 1 proposal.
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
    from .proposal_instructions import PROPOSAL_AGENT_INSTRUCTIONS
except ImportError:
    try:
        from proposal_instructions import PROPOSAL_AGENT_INSTRUCTIONS
    except ImportError:
        from subagents.phase2_eval_proposal.proposal_instructions import PROPOSAL_AGENT_INSTRUCTIONS

# Phase 2 Proposal & Decision Agent (Tanvi)
proposal_agent = Agent(
    name="proposal_agent",
    description=(
        "Phase 2 Proposal Selection Agent (Tanvi). Operating under Boss Agent Vicky. "
        "Enforces strict proposal routing logic: "
        "If less than 1 proposal (0 approved), directly sends to Advik saying 'no proposal was generated our research agents are busy' without taking human input. "
        "In case of 1 proposal, directly sends to Advik without taking human input. "
        "Only in case of 2 proposals, asks for human input (HITL) to select 1 proposal and forwards the selection to Advik."
    ),
    model=MODEL_NAME,
    tools=[],
    instruction=PROPOSAL_AGENT_INSTRUCTIONS,
    sub_agents=[],
)

# Aliases
tanvi_agent = proposal_agent
option_selection_agent = proposal_agent
