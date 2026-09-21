"""
tools.py — shared tool definitions for the TradeAnalyst workshop.
All agents import from here. Tools are decorated with @tool so CrewAI
can pass them to any agent automatically.
"""

import datetime
import json
from pathlib import Path

import yfinance as yf
from crewai.tools import tool

HISTORY_FILE = Path(__file__).parent / "history.json"

# ── Shared ────────────────────────────────────────────────────────────────────

@tool("Get Price History")
def get_price_history(ticker: str, period: str = "6mo") -> str:
    """Historical prices for a ticker: current price, high/low, % change,
    50 and 200-day moving averages. Period: 1mo 3mo 6mo 1y 2y."""
    try:
        closes = yf.Ticker(ticker).history(period=period)["Close"]
        if closes.empty:
            return f"No data for {ticker}."
        cur = float(closes.iloc[-1])
        return json.dumps({
            "current_price":            round(cur, 2),
            "period_high":              round(float(closes.max()), 2),
            "period_low":               round(float(closes.min()), 2),
            "pct_change":               round((cur - float(closes.iloc[0])) / float(closes.iloc[0]) * 100, 2),
            "ma_50":                    round(float(closes.tail(50).mean()), 2) if len(closes) >= 50 else None,
        })
    except Exception as e:
        return f"Error: {e}"


@tool("Get Fundamentals")
def get_fundamentals(ticker: str) -> str:
    """Key fundamentals: trailing/forward P/E, PEG, market cap, beta,
    profit margin, revenue growth."""
    try:
        i = yf.Ticker(ticker).info
        return json.dumps({
            "company":          i.get("longName"),
            "sector":           i.get("sector"),
            "trailing_pe":      i.get("trailingPE"),
            "forward_pe":       i.get("forwardPE"),
            "peg_ratio":        i.get("pegRatio"),
            "beta":             i.get("beta"),
            "profit_margin":    round(i["profitMargins"] * 100, 2) if i.get("profitMargins") else None,
            "revenue_growth":   round(i["revenueGrowth"]  * 100, 2) if i.get("revenueGrowth")  else None,
            "market_cap":       i.get("marketCap"),
        })
    except Exception as e:
        return f"Error: {e}"


# ── Bull-specific ─────────────────────────────────────────────────────────────

@tool("Get Growth Signals")
def get_growth_signals(ticker: str) -> str:
    """Upside signals: analyst target, upside %, recommendation, EPS growth,
    free cash flow, return on equity."""
    try:
        i = yf.Ticker(ticker).info
        cur    = i.get("currentPrice") or i.get("regularMarketPrice")
        target = i.get("targetMeanPrice")
        return json.dumps({
            "analyst_target":       target,
            "upside_pct":           round((target - cur) / cur * 100, 2) if target and cur else None,
            "analyst_rating":       i.get("recommendationKey"),
            "eps_growth":           round(i["earningsGrowth"] * 100, 2) if i.get("earningsGrowth") else None,
            "return_on_equity":     round(i["returnOnEquity"] * 100, 2) if i.get("returnOnEquity") else None,
            "free_cashflow":        i.get("freeCashflow"),
            "forward_eps":          i.get("forwardEps"),
        })
    except Exception as e:
        return f"Error: {e}"


# ── Bear-specific ─────────────────────────────────────────────────────────────

@tool("Get Risk Signals")
def get_risk_signals(ticker: str) -> str:
    """Downside signals: drawdown from 52w high, short interest, debt/equity,
    governance risk score, operating margins."""
    try:
        i   = yf.Ticker(ticker).info
        cur = i.get("currentPrice") or i.get("regularMarketPrice")
        wh  = i.get("fiftyTwoWeekHigh")
        return json.dumps({
            "drawdown_from_52w_high":   round((cur - wh) / wh * 100, 2) if cur and wh else None,
            "short_ratio":              i.get("shortRatio"),
            "short_pct_of_float":       round(i["shortPercentOfFloat"] * 100, 2) if i.get("shortPercentOfFloat") else None,
            "debt_to_equity":           i.get("debtToEquity"),
            "governance_risk":          i.get("governanceRisk"),
            "operating_margin":         round(i["operatingMargins"] * 100, 2) if i.get("operatingMargins") else None,
        })
    except Exception as e:
        return f"Error: {e}"


# ── Manager-only ──────────────────────────────────────────────────────────────

@tool("Get Recommendation History")
def get_recommendation_history(ticker: str = "") -> str:
    """Past BUY/SELL/HOLD calls by this desk, optionally filtered by ticker."""
    if not HISTORY_FILE.exists():
        return "No history yet."
    records = json.loads(HISTORY_FILE.read_text())
    if ticker:
        records = [r for r in records if r["ticker"] == ticker.upper()]
    return json.dumps(records[-5:], indent=2) if records else "No prior calls."


def compute_confidence(ticker: str, action: str) -> int:
    """
    Data-driven confidence score (1–5).
    BUY criteria  (+1 each): price > ma50, revenue growth > 15%, analyst upside > 10%, PEG < 3, margin > 5%
    SELL criteria (+1 each): price < ma50, drawdown > 15%, short ratio > 3, PEG > 4, forward P/E > 100
    HOLD: always 3.
    """
    if action == "HOLD":
        return 3
    try:
        i       = yf.Ticker(ticker).info
        closes  = yf.Ticker(ticker).history(period="6mo")["Close"]
        cur     = float(closes.iloc[-1])
        ma50    = float(closes.tail(50).mean()) if len(closes) >= 50 else None
        target  = i.get("targetMeanPrice")
        score   = 0
        if action == "BUY":
            if ma50 and cur > ma50:                                  score += 1
            if (i.get("revenueGrowth") or 0) > 0.15:                score += 1
            if target and (target - cur) / cur > 0.10:              score += 1
            if (i.get("pegRatio") or 99) < 3:                       score += 1
            if (i.get("profitMargins") or 0) > 0.05:                score += 1
        elif action == "SELL":
            if ma50 and cur < ma50:                                  score += 1
            wh = i.get("fiftyTwoWeekHigh")
            if wh and (cur - wh) / wh < -0.15:                      score += 1
            if (i.get("shortRatio") or 0) > 3:                      score += 1
            if (i.get("pegRatio") or 0) > 4:                        score += 1
            if (i.get("forwardPE") or 0) > 100:                     score += 1
        return max(1, min(5, score))
    except Exception:
        return 3


@tool("Log Recommendation")
def log_recommendation(ticker: str, action: str, reasoning: str) -> str:
    """Save the desk's final BUY/SELL/HOLD. Confidence is computed from live data.
    Call EXACTLY ONCE. Reasoning must weigh both bull and bear arguments."""
    action = action.upper()
    confidence  = compute_confidence(ticker, action)
    price       = float(yf.Ticker(ticker).history(period="1d")["Close"].iloc[-1])
    records     = json.loads(HISTORY_FILE.read_text()) if HISTORY_FILE.exists() else []
    entry = {
        "timestamp":  datetime.datetime.now().isoformat(timespec="seconds"),
        "ticker":     ticker.upper(),
        "action":     action,
        "confidence": confidence,
        "price":      price,
        "reasoning":  reasoning,
    }
    records.append(entry)
    HISTORY_FILE.write_text(json.dumps(records, indent=2))
    return json.dumps({"logged": True, "action": action, "confidence": f"{confidence}/5", "price": price})
