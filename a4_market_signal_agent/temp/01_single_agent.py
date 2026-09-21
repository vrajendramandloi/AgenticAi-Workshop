"""
01_single_agent.py
==================
A single agent that researches a stock and makes a BUY/SELL/HOLD call.

Key concepts introduced here:
  • Agent  — has a role, goal, backstory, and a list of tools it can call
  • Task   — a unit of work: what to do + what good output looks like
  • Crew   — wires agents and tasks together and runs them

Run:  python 01_single_agent.py AAPL
"""

import os, sys
from crewai import Agent, Crew, LLM, Task
from tools import get_price_history, get_fundamentals, log_recommendation

# ── LLM setup ─────────────────────────────────────────────────────────────────
api_key = os.environ.get("OLLAMA_API_KEY") or sys.exit("Set OLLAMA_API_KEY first.")
os.environ["OPENAI_API_KEY"]  = api_key
os.environ["OPENAI_API_BASE"] = "https://ollama.com/v1"

llm = LLM(model="openai/gpt-oss:120b", base_url="https://ollama.com/v1",
          api_key=api_key, temperature=0.3)

# ── Agent ──────────────────────────────────────────────────────────────────────
analyst = Agent(
    role      = "Trade Analyst",
    goal      = "Research a stock and make a well-reasoned BUY, SELL, or HOLD call.",
    backstory  = "A generalist equity analyst who always grounds decisions in real data.",
    tools     = [get_price_history, get_fundamentals, log_recommendation],
    llm       = llm,
    verbose   = False,
)

# ── Task ───────────────────────────────────────────────────────────────────────
ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

task = Task(
    description     = (
        f"Research {ticker}: fetch price history (6mo) and fundamentals. "
        f"Then call Log Recommendation once with your BUY/SELL/HOLD and reasoning."
    ),
    expected_output = "Final recommendation with reasoning citing actual data.",
    agent           = analyst,
)

# ── Run ────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}\n  Single Agent Analysis — {ticker}\n{'='*60}")
result = Crew(agents=[analyst], tasks=[task], verbose=False).kickoff()
print(result)
