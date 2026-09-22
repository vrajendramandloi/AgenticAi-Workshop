import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

# Prevent bytecode generation
sys.dont_write_bytecode = True

# Ensure workspace root and a5 root are in sys.path
_current_dir = Path(__file__).resolve().parent
_workspace_root = _current_dir.parent

for _p in [str(_current_dir), str(_workspace_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from dotenv import load_dotenv, find_dotenv
    _root_env = _workspace_root / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
except ImportError:
    pass

# Synchronize API keys across Google GenAI and ADK conventions
if os.environ.get("GOOGLE_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
    os.environ["GEMINI_API_KEY"] = os.environ["GOOGLE_API_KEY"]
if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]

MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")

from google.adk.agents.llm_agent import Agent

try:
    from instructions import TOOL_AGENT_INSTRUCTIONS
except ImportError:
    from .instructions import TOOL_AGENT_INSTRUCTIONS

try:
    from tools.init_tools.location_cache import location_cache
except ImportError:
    from .tools.init_tools.location_cache import location_cache

try:
    from subagents.phase1.quotation_agent import quotation_agent
except ImportError:
    from .subagents.phase1.quotation_agent import quotation_agent

try:
    from subagents.phase2 import (
        statistic_agent,
        luxury_research_agent,
        value_research_agent,
        phase2_parallel_agent,
        eval_agent,
    )
except ImportError:
    try:
        from .subagents.phase2 import (
            statistic_agent,
            luxury_research_agent,
            value_research_agent,
            phase2_parallel_agent,
            eval_agent,
        )
    except ImportError:
        statistic_agent = None
        luxury_research_agent = None
        value_research_agent = None
        phase2_parallel_agent = None
        eval_agent = None

try:
    from subagents.phase2_eval_proposal import proposal_agent
except ImportError:
    try:
        from .subagents.phase2_eval_proposal import proposal_agent
    except ImportError:
        proposal_agent = None

try:
    from subagents.phase3 import finalizer_agent
except ImportError:
    try:
        from .subagents.phase3 import finalizer_agent
    except ImportError:
        finalizer_agent = None

try:
    from tools.web_search_tool import web_search
except ImportError:
    from .tools.web_search_tool import web_search


# Root Boss Agent: Vicky
if quotation_agent and getattr(quotation_agent, "parent_agent", None) is not None:
    quotation_agent.parent_agent = None

root_agent = Agent(
    name="Vicky",
    description=(
        "Boss / Lead Orchestrator agent who leads a team of specialized subagents, "
        "delegates tasks, and collaborates directly with Vrajendra."
    ),
    model=MODEL_NAME,
    tools=[web_search, location_cache.get_current_location],
    instruction=TOOL_AGENT_INSTRUCTIONS,
    sub_agents=[quotation_agent] if quotation_agent else [],
)

# Export aliases for multi-agent runners and test scripts
vicky_agent = root_agent
kuhu_agent = root_agent
boss_agent = root_agent
query_analysis_agent = quotation_agent
phase1_agent = quotation_agent
phase2_agent = eval_agent
eval_agent = eval_agent
ishaan_agent = eval_agent
phase2_parallel_agent = phase2_parallel_agent
statistic_agent = statistic_agent
luxury_research_agent = luxury_research_agent
value_research_agent = value_research_agent
proposal_agent = proposal_agent
tanvi_agent = proposal_agent
phase3_agent = finalizer_agent
finalizer_agent = finalizer_agent
advik_agent = finalizer_agent



