"""demo_02_multi.py
=================
Three-agent sequential debate using Google ADK's `SequentialAgent`.
1. 🐂 Bull Analyst builds the BUY case citing growth catalysts.
2. 🐻 Bear Analyst builds the SELL case citing downside risks and valuation stretch.
3. 📋 Portfolio Manager weighs both cases, checks recommendation history, and commits the call.

Equivalent to CrewAI's `temp/02_multi_agent.py` ported to Google ADK.

Usage:
  python demo_02_multi.py AAPL
  python demo_02_multi.py NVDA
  python demo_02_multi.py RELIANCE.NS
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

from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from instructions import (
    BEAR_ANALYST_INSTRUCTION,
    BULL_ANALYST_INSTRUCTION,
)
from tools import (
    get_fundamentals,
    get_growth_signals,
    get_price_history,
    get_recommendation_history,
    get_risk_signals,
    log_recommendation,
)

# Portfolio Manager instruction for demo_02 (logs directly, before compliance stage)
PM_DIRECT_LOG_INSTRUCTION = """
You are the **Portfolio Manager** (Senior Trader) leading this trading desk.
Your mission is to adjudicate between the Bull and Bear cases and make a final call: **BUY**, **SELL**, or **HOLD**.

Instructions:
1. Carefully read both the Bull Analyst and Bear Analyst reports provided in the context.
2. Call `get_recommendation_history` to inspect any prior calls on this ticker.
3. Decide which side presented the superior risk-reward case based on actual data.
4. Call `log_recommendation(ticker, action, reasoning)` EXACTLY ONCE to commit your decision.
5. Conclude your verdict in this clear format:
   RECOMMENDATION: <BUY|SELL|HOLD>
   VERDICT: <3-5 sentences explaining which side won and why>
"""

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
    description="Portfolio Manager adjudicating and committing the final trade call.",
    model=MODEL_NAME,
    instruction=PM_DIRECT_LOG_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, get_recommendation_history, log_recommendation],
)

multi_desk = SequentialAgent(
    name="multi_agent_desk",
    description="Sequential debate desk: Bull -> Bear -> Portfolio Manager.",
    sub_agents=[bull, bear, manager],
)


async def run_multi_agent(ticker: str):
    print(f"\n{'='*65}\n  TradeAnalyst: Multi-Agent Sequential Debate — {ticker.upper()}\n{'='*65}\n")
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="user", app_name="demo_multi")
    runner = Runner(agent=multi_desk, session_service=session_service, app_name="demo_multi")

    prompt = f"Analyze {ticker.upper()}. Bull builds BUY case, Bear builds SELL case, Manager decides."
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    agent_headers = {
        "bull_analyst": "🐂 BULL ANALYST",
        "bear_analyst": "🐻 BEAR ANALYST",
        "portfolio_manager": "📋 PORTFOLIO MANAGER",
    }
    seen_authors = set()

    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=msg):
        author = getattr(event, "author", "")
        if author in agent_headers and author not in seen_authors:
            print(f"\n── {agent_headers[author]} " + "─" * 45)
            seen_authors.add(author)

        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                txt = getattr(part, "text", None)
                if txt:
                    print(txt.strip())


if __name__ == "__main__":
    target_ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
    asyncio.run(run_multi_agent(target_ticker))
