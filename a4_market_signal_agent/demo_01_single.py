"""demo_01_single.py
==================
Single-agent baseline using Google ADK.
Researches a stock, analyzes price history & fundamentals, and commits a recommendation.

Equivalent to CrewAI's `temp/01_single_agent.py` ported cleanly to Google ADK.

Usage:
  python demo_01_single.py AAPL
  python demo_01_single.py NVDA
  python demo_01_single.py RELIANCE.NS
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
from google.adk.runners import Runner
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.genai import types

from tools import get_fundamentals, get_price_history, log_recommendation

SINGLE_ANALYST_INSTRUCTION = """
You are a Senior Equity Research Analyst.
Your goal is to research the requested stock using real data and make a well-reasoned BUY, SELL, or HOLD call.

Instructions:
1. Call `get_price_history` to inspect the 6-month price performance and 50-day moving average.
2. Call `get_fundamentals` to examine valuation (P/E, PEG) and financial health (revenue growth, margins).
3. Synthesize your findings into a concise 4-6 sentence report citing real numbers.
4. Call `log_recommendation` EXACTLY ONCE to commit your final call and reasoning.
5. End your response with your final verdict:
   RECOMMENDATION: <BUY|SELL|HOLD>
   REASONING: <summary rationale>
"""

analyst = Agent(
    name="analyst",
    description="Generalist equity research analyst.",
    model=MODEL_NAME,
    instruction=SINGLE_ANALYST_INSTRUCTION,
    tools=[get_price_history, get_fundamentals, log_recommendation],
)


async def run_single_agent(ticker: str):
    print(f"\n{'='*65}\n  TradeAnalyst: Single Agent Analysis — {ticker.upper()}\n{'='*65}\n")
    session_service = InMemorySessionService()
    session = await session_service.create_session(user_id="user", app_name="demo_single")
    runner = Runner(agent=analyst, session_service=session_service, app_name="demo_single")

    prompt = f"Research {ticker.upper()} (6mo). Check price history and fundamentals. Commit your recommendation."
    msg = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])

    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=msg):
        if hasattr(event, "content") and event.content:
            for part in event.content.parts:
                txt = getattr(part, "text", None)
                if txt:
                    print(txt.strip())


if __name__ == "__main__":
    target_ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"
    asyncio.run(run_single_agent(target_ticker))
