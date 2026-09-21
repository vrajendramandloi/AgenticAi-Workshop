try:
    from instructions import (
        ADMIN_EVALUATION_INSTRUCTION,
        CAMPAIGN_FINALIZER_INSTRUCTION,
        CAMPAIGN_ORCHESTRATOR_INSTRUCTION,
        MARKET_RESEARCH_INSTRUCTION,
        SALES_AGENT_INSTRUCTION,
    )
except ImportError:
    from .instructions import (
        ADMIN_EVALUATION_INSTRUCTION,
        CAMPAIGN_FINALIZER_INSTRUCTION,
        CAMPAIGN_ORCHESTRATOR_INSTRUCTION,
        MARKET_RESEARCH_INSTRUCTION,
        SALES_AGENT_INSTRUCTION,
    )

import os
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools import google_search


from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv
    # Explicitly load root workspace .env (d:\WORK\WORKSPACE\AI\.env)
    _root_env = Path(__file__).resolve().parent.parent / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
    MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")
except ImportError:
    print("ERROR: Import Error while importing Model")

market_research_agent = LlmAgent(
    name="market_researcher",
    model=MODEL_NAME,
    instruction=MARKET_RESEARCH_INSTRUCTION,
    output_key="market_research_summary",
)
# 2. Sales Strategist Specialist
sales_agent = LlmAgent(
    name="sales_strategist",
    model=MODEL_NAME,
    instruction=SALES_AGENT_INSTRUCTION,
    output_key="sales_strategy_summary",
)
# 3. Office Setup & Admin Evaluation Specialist
admin_eval_agent = LlmAgent(
    name="office_admin_evaluator",
    model=MODEL_NAME,
    instruction=ADMIN_EVALUATION_INSTRUCTION,
    output_key="admin_evaluation_summary",
)

# 4. Campaign Finalizer Agent 
campaign_finalizer_agent = LlmAgent(
    name="finalizer_agent",
    model=MODEL_NAME,
    instruction=CAMPAIGN_FINALIZER_INSTRUCTION,
    output_key="campaign_finalizer_summary",
)

campaign_orchestrator = SequentialAgent(
    name="campaign_orchestrator",
    description=CAMPAIGN_ORCHESTRATOR_INSTRUCTION,
    sub_agents=[
        market_research_agent,
        sales_agent,
        admin_eval_agent,
        campaign_finalizer_agent
    ],
)

root_agent = campaign_orchestrator


