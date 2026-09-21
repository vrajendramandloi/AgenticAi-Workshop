"""demo_parallel_trader.py
========================
Demonstrates Google ADK ParallelAgent + SequentialAgent Workflow:
1. 🐂 Bull Analyst and 🐻 Bear Analyst execute IN PARALLEL (concurrently).
2. Both submit independent research summaries to session state.
3. 📋 Trader Agent receives both summaries, thoroughly reviews upside vs downside,
   and issues the final decisive call (BUY/SELL/HOLD) on the stock.

Usage:
  python demo_parallel_trader.py AAPL
  python demo_parallel_trader.py NVDA
  python demo_parallel_trader.py RELIANCE.NS
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

# Ensure pywin32 subpaths are available on Windows
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

from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from instructions import (
    BEAR_ANALYST_INSTRUCTION,
    BULL_ANALYST_INSTRUCTION,
    TRADER_AGENT_INSTRUCTION,
)
from tools import (
    get_fundamentals,
    get_growth_signals,
    get_price_history,
    get_recommendation_history,
    get_risk_signals,
)

# 1. Bull Analyst (Independent BUY research)
bull = LlmAgent(
    name="bull_analyst",
    description="Bull Analyst researching growth, momentum, and building BUY thesis.",
    model=MODEL_NAME,
    instruction=BULL_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_growth_signals],
    output_key="bull_analysis_summary",
)

# 2. Bear Analyst (Independent SELL research)
bear = LlmAgent(
    name="bear_analyst",
    description="Bear Analyst researching downside risks, valuation stretch, and SELL thesis.",
    model=MODEL_NAME,
    instruction=BEAR_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_risk_signals],
    output_key="bear_analysis_summary",
)

# 3. Parallel Stage: Bull and Bear run concurrently
parallel_analysts = ParallelAgent(
    name="parallel_analysts",
    description="Runs Bull and Bear analysts concurrently in parallel.",
    sub_agents=[bull, bear],
)

# 4. Trader Agent: Adjudicates after receiving both analyses
trader = LlmAgent(
    name="trader_agent",
    description="Senior Trader reviewing both parallel reports and issuing the final trade action.",
    model=MODEL_NAME,
    instruction=TRADER_AGENT_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_recommendation_history],
    output_key="trader_decision",
)

# 5. Outer Pipeline: Parallel Fan-Out -> Trader Fan-In
desk = SequentialAgent(
    name="parallel_to_trader_desk",
    description="Parallel Bull/Bear Research -> Trader Adjudication Pipeline.",
    sub_agents=[parallel_analysts, trader],
)


async def run_parallel_trade_desk(ticker: str):
    print(f"\n{'='*70}\n  MarketSignal: Parallel (Bull || Bear) -> Trader Review — {ticker.upper()}\n{'='*70}\n")
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="user", app_name="demo_parallel")
    runner = Runner(agent=desk, session_service=session_service, app_name="demo_parallel")

    prompt = (
        f"Research and evaluate security {ticker.upper()}.\n"
        f"1. Bull Analyst and Bear Analyst: Execute in parallel and gather data.\n"
        f"2. Trader Agent: Review both reports, weigh upside vs downside, and declare the final call (BUY, SELL, or HOLD)."
    )
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    agent_headers = {
        "bull_analyst": "🐂 BULL ANALYST (PARALLEL BRANCH)",
        "bear_analyst": "🐻 BEAR ANALYST (PARALLEL BRANCH)",
        "trader_agent": "📋 SENIOR TRADER (POST-REVIEW DECISION)",
    }
    seen_authors = set()

    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=msg):
        author = getattr(event, "author", "")
        if author in agent_headers and author not in seen_authors:
            print(f"\n── {agent_headers[author]} " + "─" * 30)
            seen_authors.add(author)

        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                txt = getattr(part, "text", None)
                if txt:
                    print(txt.strip())


if __name__ == "__main__":
    target_ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
    asyncio.run(run_parallel_trade_desk(target_ticker))
