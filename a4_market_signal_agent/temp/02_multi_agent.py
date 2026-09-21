"""
02_multi_agent.py
=================
Three agents debate a stock before a final call is made.

New concepts introduced here:
  • Role specialization — each agent has different tools and a different angle
  • context=[]          — passes one task's output as input to the next task
  • Sequential process  — tasks run in order: Bull → Bear → Manager

Run:  python 02_multi_agent.py AAPL
"""

import os, sys
from crewai import Agent, Crew, LLM, Process, Task
from tools import (get_price_history, get_fundamentals,
                   get_growth_signals, get_risk_signals,
                   get_recommendation_history, log_recommendation)

# ── LLM setup ─────────────────────────────────────────────────────────────────
api_key = os.environ.get("OLLAMA_API_KEY") or sys.exit("Set OLLAMA_API_KEY first.")
os.environ["OPENAI_API_KEY"]  = api_key
os.environ["OPENAI_API_BASE"] = "https://ollama.com/v1"

llm = LLM(model="openai/gpt-oss:120b", base_url="https://ollama.com/v1",
          api_key=api_key, temperature=0.3)

ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

# ── Agents ─────────────────────────────────────────────────────────────────────
bull = Agent(
    role="Bull Analyst",
    goal=f"Make the strongest honest BUY case for {ticker}.",
    backstory="A growth-focused analyst who hunts for upside using real data.",
    tools=[get_price_history, get_fundamentals, get_growth_signals],
    llm=llm, verbose=False, allow_delegation=False,
)

bear = Agent(
    role="Bear Analyst",
    goal=f"Make the strongest honest SELL case for {ticker}.",
    backstory="A skeptical short-side analyst who focuses on risk and downside.",
    tools=[get_price_history, get_fundamentals, get_risk_signals],
    llm=llm, verbose=False, allow_delegation=False,
)

manager = Agent(
    role="Portfolio Manager",
    goal=f"Weigh both cases and commit to a final call on {ticker}.",
    backstory="A seasoned PM who reads both reports, spot-checks key numbers, then decides.",
    tools=[get_price_history, get_fundamentals, get_recommendation_history, log_recommendation],
    llm=llm, verbose=False, allow_delegation=False,
)

# ── Tasks ──────────────────────────────────────────────────────────────────────
bull_task = Task(
    description     = f"Research {ticker} (6mo). Use all three of your tools. Make the BUY case.",
    expected_output = "4-6 sentences citing real numbers. End with the strongest reason to buy.",
    agent           = bull,
)

bear_task = Task(
    description     = f"Research {ticker} (6mo). Use all three of your tools. Make the SELL case.",
    expected_output = "4-6 sentences citing real numbers. End with the strongest reason to sell.",
    agent           = bear,
)

manager_task = Task(
    description     = (
        f"You have both analyst reports for {ticker}. "
        f"Verify 1-2 decisive numbers, check history, then call Log Recommendation once. "
        f"Write a 3-5 sentence verdict naming which side won and why."
    ),
    expected_output = "Recommendation: <BUY|SELL|HOLD>\nVerdict: <3-5 sentences>",
    agent           = manager,
    context         = [bull_task, bear_task],   # ← manager receives both reports
)

# ── Run ────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}\n  Multi-Agent Desk — {ticker}\n{'='*60}")
crew   = Crew(agents=[bull, bear, manager], tasks=[bull_task, bear_task, manager_task],
              process=Process.sequential, verbose=False)
crew.kickoff()

print("\n── 🐂 BULL ──────────────────────────────────────────────")
print(bull_task.output.raw)
print("\n── 🐻 BEAR ──────────────────────────────────────────────")
print(bear_task.output.raw)
print("\n── 📋 MANAGER ───────────────────────────────────────────")
print(manager_task.output.raw)
