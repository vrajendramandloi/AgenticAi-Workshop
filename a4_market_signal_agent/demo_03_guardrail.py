"""demo_03_guardrail.py
======================
Institutional 4-Agent Sequential Trading Desk with Compliance Guardrail using Google ADK.

Workflow:
1. 🐂 Bull Analyst: Researches market data and formulates an evidence-backed BUY thesis.
2. 🐻 Bear Analyst: Uncovers downside risks, short interest, and builds a SELL thesis.
3. 📋 Portfolio Manager: Weighs both cases and formulates a proposed trade action (BUY/SELL/HOLD).
4. 🛡️ Compliance Officer: Evaluates proposal against deterministic desk rules:
   - VETO if Beta > 2.5 (desk volatility cap)
   - VETO if BUY with Forward P/E > 200 (valuation guardrail)
   - REFER if algorithmic confidence < 2/5 (insufficient signal conviction)
   - REFER if ticker was called in past 3 days (cooling-off rule)
   - APPROVE otherwise (commits audit log to history.json)

Equivalent to CrewAI's `temp/03_guardrail.py` ported to native Google ADK.

Usage:
  python demo_03_guardrail.py AAPL
  python demo_03_guardrail.py NVDA
  python demo_03_guardrail.py TSLA
  python demo_03_guardrail.py RELIANCE.NS
"""

import asyncio
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Ensure pywin32 subpaths are available on Windows if installed in custom paths
for _p in [Path(p) for p in sys.path if "PythonLibs" in p or "site-packages" in p]:
    for _sub in ["win32", "win32/lib", "pywin32_system32"]:
        _target = str(_p / _sub)
        if _target not in sys.path and (_p / _sub).exists():
            sys.path.append(_target)

from dotenv import find_dotenv, load_dotenv

_root_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(dotenv_path=_root_env)
else:
    load_dotenv(find_dotenv())

MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")

from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from instructions import (
    BEAR_ANALYST_INSTRUCTION,
    BULL_ANALYST_INSTRUCTION,
    COMPLIANCE_OFFICER_INSTRUCTION,
    PORTFOLIO_MANAGER_INSTRUCTION,
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

# Define Desk Agents
bull = Agent(
    name="bull_analyst",
    description="Bull Analyst formulating the evidence-backed BUY case.",
    model=MODEL_NAME,
    instruction=BULL_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_growth_signals],
)

bear = Agent(
    name="bear_analyst",
    description="Bear Analyst formulating the downside SELL case.",
    model=MODEL_NAME,
    instruction=BEAR_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_risk_signals],
)

manager = Agent(
    name="portfolio_manager",
    description="Portfolio Manager weighing both cases and proposing a trade action for compliance review.",
    model=MODEL_NAME,
    instruction=PORTFOLIO_MANAGER_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_recommendation_history],
)

compliance = Agent(
    name="compliance_officer",
    description="Compliance Officer enforcing deterministic risk guardrails before logging.",
    model=MODEL_NAME,
    instruction=COMPLIANCE_OFFICER_INSTRUCTION,
    tools=[run_compliance_check, log_compliant_recommendation],
)

# Wire 4-agent sequential pipeline
guardrail_desk = SequentialAgent(
    name="guardrail_trade_desk",
    description="Institutional Trade Analysis Desk with Compliance Guardrail.",
    sub_agents=[bull, bear, manager, compliance],
)


async def run_guardrail_desk(ticker: str):
    print(f"\n{'='*70}\n  TradeAnalyst: 4-Agent Desk + Compliance Guardrail — {ticker.upper()}\n{'='*70}\n")
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="user", app_name="demo_guardrail")
    runner = Runner(agent=guardrail_desk, session_service=session_service, app_name="demo_guardrail")

    prompt = (
        f"Analyze security {ticker.upper()}.\n"
        f"1. Bull Analyst: Research 6-month data and present the BUY thesis.\n"
        f"2. Bear Analyst: Research downside risks and present the SELL thesis.\n"
        f"3. Portfolio Manager: Weigh both sides and propose ACTION and REASONING (do NOT log directly).\n"
        f"4. Compliance Officer: Run compliance check on the PM's proposal. If APPROVE, log it. If VETO/REFER, explain why."
    )
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    agent_headers = {
        "bull_analyst": "🐂 BULL ANALYST (BUY THESIS)",
        "bear_analyst": "🐻 BEAR ANALYST (SELL THESIS)",
        "portfolio_manager": "📋 PORTFOLIO MANAGER (TRADE PROPOSAL)",
        "compliance_officer": "🛡️ COMPLIANCE OFFICER (RISK AUDIT & LOGGING)",
    }
    seen_authors = set()

    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=msg):
        author = getattr(event, "author", "")
        if author in agent_headers and author not in seen_authors:
            print(f"\n── {agent_headers[author]} " + "─" * 35)
            seen_authors.add(author)

        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                txt = getattr(part, "text", None)
                if txt:
                    print(txt.strip())


if __name__ == "__main__":
    target_ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
    asyncio.run(run_guardrail_desk(target_ticker))
