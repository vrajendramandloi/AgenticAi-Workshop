"""
03_guardrail.py
===============
Adds a Compliance agent that reviews the Manager's decision BEFORE it is logged.
The Compliance agent can APPROVE, VETO, or REFER the call.

New concept introduced here:
  • Guardrail agent — a downstream agent that validates, not decides
  • Structured output — compliance returns a machine-readable verdict
  • Conditional logging — only the compliance agent logs the final call

Guardrail rules (transparent and auditable):
  VETO  if beta > 2.5              (too volatile for desk policy)
  VETO  if BUY with forward P/E > 200  (valuation guardrail)
  REFER if confidence < 2          (insufficient conviction)
  REFER if same ticker called in last 3 days  (cooling-off period)
  APPROVE otherwise

Run:  python 03_guardrail.py AAPL
"""

import json, os, sys, datetime
from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool
from tools import (get_price_history, get_fundamentals,
                   get_growth_signals, get_risk_signals,
                   get_recommendation_history, compute_confidence,
                   HISTORY_FILE)
import yfinance as yf

# ── LLM setup ─────────────────────────────────────────────────────────────────
api_key = os.environ.get("OLLAMA_API_KEY") or sys.exit("Set OLLAMA_API_KEY first.")
os.environ["OPENAI_API_KEY"]  = api_key
os.environ["OPENAI_API_BASE"] = "https://ollama.com/v1"

llm = LLM(model="openai/gpt-oss:120b", base_url="https://ollama.com/v1",
          api_key=api_key, temperature=0.2)   # lower temp for compliance = more deterministic

ticker = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

# ── Compliance tools ───────────────────────────────────────────────────────────

@tool("Run Compliance Check")
def run_compliance_check(ticker: str, action: str, reasoning: str) -> str:
    """
    Validate a proposed BUY/SELL/HOLD against desk risk rules.
    Returns verdict (APPROVE/VETO/REFER), the triggered rule if any, and
    the computed confidence score. Call this before logging anything.
    """
    action     = action.upper()
    confidence = compute_confidence(ticker, action)

    try:
        info    = yf.Ticker(ticker).info
        beta    = info.get("beta") or 0
        fwd_pe  = info.get("forwardPE") or 0
    except Exception:
        beta, fwd_pe = 0, 0

    # Check cooling-off period
    recent_call = False
    if HISTORY_FILE.exists():
        records = json.loads(HISTORY_FILE.read_text())
        for r in reversed(records):
            if r["ticker"] == ticker:
                age = (datetime.datetime.now() -
                       datetime.datetime.fromisoformat(r["timestamp"])).days
                if age < 3:
                    recent_call = True
                break

    # Apply rules in priority order
    if beta > 2.5:
        verdict, rule = "VETO",   f"Beta {beta:.2f} exceeds desk limit of 2.5"
    elif action == "BUY" and fwd_pe > 200:
        verdict, rule = "VETO",   f"Forward P/E {fwd_pe:.0f} exceeds BUY limit of 200"
    elif confidence < 2:
        verdict, rule = "REFER",  f"Confidence {confidence}/5 below minimum threshold of 2"
    elif recent_call:
        verdict, rule = "REFER",  f"{ticker} was called within the last 3 days (cooling-off period)"
    else:
        verdict, rule = "APPROVE", "All checks passed"

    return json.dumps({
        "verdict":    verdict,
        "rule":       rule,
        "confidence": confidence,
        "beta":       beta,
        "forward_pe": fwd_pe,
    })


@tool("Log Compliant Recommendation")
def log_compliant_recommendation(ticker: str, action: str, reasoning: str,
                                  compliance_verdict: str, compliance_rule: str) -> str:
    """Log the final recommendation ONLY after compliance has approved it.
    Includes the compliance verdict and rule in the audit trail."""
    action     = action.upper()
    confidence = compute_confidence(ticker, action)
    price      = float(yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1])
    records    = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else []
    entry = {
        "timestamp":          datetime.datetime.now().isoformat(timespec="seconds"),
        "ticker":             ticker,
        "action":             action,
        "confidence":         confidence,
        "price":              price,
        "reasoning":          reasoning,
        "compliance_verdict": compliance_verdict,
        "compliance_rule":    compliance_rule,
    }
    records.append(entry)
    HISTORY_FILE.write_text(json.dumps(records, indent=2))
    return f"Logged {action} {ticker} | compliance={compliance_verdict} | confidence={confidence}/5"


# ── Agents (Bull and Bear unchanged) ──────────────────────────────────────────
bull = Agent(
    role="Bull Analyst", goal=f"Make the strongest honest BUY case for {ticker}.",
    backstory="Growth-focused analyst. Uses real data only.",
    tools=[get_price_history, get_fundamentals, get_growth_signals],
    llm=llm, verbose=False, allow_delegation=False,
)
bear = Agent(
    role="Bear Analyst", goal=f"Make the strongest honest SELL case for {ticker}.",
    backstory="Skeptical short-side analyst. Focuses on risk and downside.",
    tools=[get_price_history, get_fundamentals, get_risk_signals],
    llm=llm, verbose=False, allow_delegation=False,
)
manager = Agent(
    role="Portfolio Manager", goal=f"Weigh both cases and propose a final call on {ticker}.",
    backstory="Experienced PM. Proposes a decision — compliance reviews it before it logs.",
    tools=[get_price_history, get_fundamentals, get_recommendation_history],
    llm=llm, verbose=False, allow_delegation=False,
)
compliance = Agent(
    role="Compliance Officer",
    goal="Validate the PM's proposed decision against desk risk rules. APPROVE, VETO, or REFER.",
    backstory=(
        "A risk officer who applies four non-negotiable rules before any trade is logged. "
        "You do not form opinions on the stock — you only enforce the rules."
    ),
    tools=[run_compliance_check, log_compliant_recommendation],
    llm=llm, verbose=False, allow_delegation=False,
)

# ── Tasks ──────────────────────────────────────────────────────────────────────
bull_task = Task(
    description     = f"Research {ticker} (6mo). Use all your tools. Make the BUY case.",
    expected_output = "4-6 sentences with real numbers. Strongest reason to buy at the end.",
    agent           = bull,
)
bear_task = Task(
    description     = f"Research {ticker} (6mo). Use all your tools. Make the SELL case.",
    expected_output = "4-6 sentences with real numbers. Strongest reason to sell at the end.",
    agent           = bear,
)
manager_task = Task(
    description     = (
        f"Read both analyst reports for {ticker}. Propose a BUY, SELL, or HOLD with reasoning. "
        f"Do NOT log it — compliance will review it first. "
        f"Output format: ACTION: <action>\nREASONING: <reasoning>"
    ),
    expected_output = "ACTION: <BUY|SELL|HOLD>\nREASONING: <paragraph weighing both cases>",
    agent           = manager,
    context         = [bull_task, bear_task],
)
compliance_task = Task(
    description     = (
        f"Extract the ACTION and REASONING from the PM's proposal for {ticker}. "
        f"Run Compliance Check with those values. "
        f"If APPROVE: call Log Compliant Recommendation to record the decision. "
        f"If VETO or REFER: explain the rule triggered and do NOT log anything."
    ),
    expected_output = (
        "Verdict: <APPROVE|VETO|REFER>\n"
        "Rule: <which rule was triggered or 'all checks passed'>\n"
        "Outcome: <one sentence — logged / blocked / escalated>"
    ),
    agent           = compliance,
    context         = [manager_task],
)

# ── Run ────────────────────────────────────────────────────────────────────────
print(f"\n{'='*60}\n  TradeAnalyst Desk + Guardrail — {ticker}\n{'='*60}")
crew = Crew(
    agents  = [bull, bear, manager, compliance],
    tasks   = [bull_task, bear_task, manager_task, compliance_task],
    process = Process.sequential,
    verbose = False,
)
crew.kickoff()

print("\n── 🐂 BULL ──────────────────────────────────────────────")
print(bull_task.output.raw)
print("\n── 🐻 BEAR ──────────────────────────────────────────────")
print(bear_task.output.raw)
print("\n── 📋 MANAGER PROPOSAL ──────────────────────────────────")
print(manager_task.output.raw)
print("\n── 🛡️  COMPLIANCE ────────────────────────────────────────")
print(compliance_task.output.raw)
