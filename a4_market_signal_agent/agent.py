"""Project 3: Sequential Multi-Agent Trading Desk (Google ADK)
============================================================
Implements an institutional trade analysis workflow using Google ADK's `SequentialAgent`.

Pipeline Stages (Sequential Process):
1. 🐂 Bull Analyst: Researches stock and formulates evidence-backed BUY case.
2. 🐻 Bear Analyst: Inspects downside, short interest, and builds SELL case.
3. 📋 Portfolio Manager: Weighs both reports and proposes BUY/SELL/HOLD decision.
4. 🛡️  Compliance Officer: Enforces risk guardrails (Beta, P/E, cooling-off) and logs approved calls.
"""

import os
import sys
from pathlib import Path

# Ensure pywin32 subpaths are available on Windows if installed in custom paths
for _p in [Path(p) for p in sys.path if "PythonLibs" in p or "site-packages" in p]:
    for _sub in ["win32", "win32/lib", "pywin32_system32"]:
        _target = str(_p / _sub)
        if _target not in sys.path and (_p / _sub).exists():
            sys.path.append(_target)

# Load environment configuration from workspace root (.env)
from dotenv import find_dotenv, load_dotenv

_root_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(dotenv_path=_root_env)
else:
    load_dotenv(find_dotenv())

MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

try:
    from instructions import (
        BEAR_ANALYST_INSTRUCTION,
        BULL_ANALYST_INSTRUCTION,
        COMPLIANCE_OFFICER_INSTRUCTION,
        PORTFOLIO_MANAGER_INSTRUCTION,
        TRADER_AGENT_INSTRUCTION,
    )
    from tools import (
        get_fundamentals,
        get_growth_signals,
        get_price_history,
        get_recommendation_history,
        get_risk_signals,
        log_compliant_recommendation,
        run_compliance_check,
    )
except ImportError:
    from .instructions import (
        BEAR_ANALYST_INSTRUCTION,
        BULL_ANALYST_INSTRUCTION,
        COMPLIANCE_OFFICER_INSTRUCTION,
        PORTFOLIO_MANAGER_INSTRUCTION,
        TRADER_AGENT_INSTRUCTION,
    )
    from .tools import (
        get_fundamentals,
        get_growth_signals,
        get_price_history,
        get_recommendation_history,
        get_risk_signals,
        log_compliant_recommendation,
        run_compliance_check,
    )

# ── 1. Bull Analyst Agent (Runs concurrently) ────────────────────────────────
bull_analyst = LlmAgent(
    name="bull_analyst",
    description="Growth-focused equity analyst independently researching upside catalysts and building the BUY case.",
    model=MODEL_NAME,
    instruction=BULL_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_growth_signals],
    output_key="bull_analysis_summary",
)

# ── 2. Bear Analyst Agent (Runs concurrently) ────────────────────────────────
bear_analyst = LlmAgent(
    name="bear_analyst",
    description="Skeptical short-side analyst independently researching downside risks, valuation stretch, and the SELL case.",
    model=MODEL_NAME,
    instruction=BEAR_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_risk_signals],
    output_key="bear_analysis_summary",
)

# ── 3. Parallel Analysts (Fan-Out Stage) ─────────────────────────────────────
# Bull and Bear execute at the SAME TIME on parallel branches
parallel_analysts = ParallelAgent(
    name="parallel_analysts",
    description="Runs Bull Analyst and Bear Analyst in parallel to independently analyze upside and downside simultaneously.",
    sub_agents=[bull_analyst, bear_analyst],
)

# ── 4. Trader Agent (Fan-In / Adjudication Stage) ────────────────────────────
# Trader waits for both parallel analyses, reviews all details, and decides
trader_agent = LlmAgent(
    name="trader_agent",
    description="Lead Trader who thoroughly reviews both Bull and Bear summaries and determines the final stock decision (BUY/SELL/HOLD).",
    model=MODEL_NAME,
    instruction=TRADER_AGENT_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_recommendation_history],
    output_key="trader_decision",
)
# Backwards compatibility alias
portfolio_manager = trader_agent

# ── 5. Compliance Officer Agent (Risk Guardrail) ─────────────────────────────
compliance_officer = LlmAgent(
    name="compliance_officer",
    description="Compliance and Risk Guardrail validating the Trader's decision against desk rules before logging.",
    model=MODEL_NAME,
    instruction=COMPLIANCE_OFFICER_INSTRUCTION,
    tools=[run_compliance_check, log_compliant_recommendation],
)

# ── Master Desk Pipeline ─────────────────────────────────────────────────────
# 1. Parallel Analysts (Bull || Bear)
# 2. Trader reviews all details and decides what to do with the stock
# 3. Compliance validates and logs
root_agent = SequentialAgent(
    name="market_signal_desk",
    description="Market Signal Desk: (Bull || Bear in Parallel) -> Trader Review & Call -> Compliance Guardrail.",
    sub_agents=[parallel_analysts, trader_agent, compliance_officer],
)
