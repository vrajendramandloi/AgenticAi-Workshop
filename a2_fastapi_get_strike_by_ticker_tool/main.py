"""FastAPI Service: Live Ticker Price & Strike Tool
===================================================
A high-performance, asynchronous REST API serving real-time asset prices and
calculated option strike ladders using Yahoo Finance's free endpoints.

Usage:
  - Bring up server via uvicorn:
      uvicorn main:app --host 127.0.0.1 --port 8001 --reload
  - Or run directly:
      python main.py
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import FastAPI, HTTPException, Path as PathParam, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from models import ErrorResponse, TickerPriceResponse, TickerStrikeResponse
from service import finance_service

app = FastAPI(
    title="Live Ticker Price & Strike API",
    description=(
        "FastAPI service retrieving real-time stock/crypto prices and strike recommendations "
        "using Yahoo Finance free API without authentication keys."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for external AI agents, UI dashboards, and local tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", summary="Root Health & Directory")
async def root() -> Dict[str, Any]:
    """Welcome endpoint providing service status, available endpoints, and sample queries."""
    return {
        "status": "online",
        "service": "Live Ticker Price & Strike API",
        "docs": "/docs",
        "endpoints": {
            "get_live_price": "/price/{ticker}",
            "get_strike_ladder": "/strike/{ticker}?step={optional_step}",
            "get_full_quote": "/quote/{ticker}",
            "health": "/health",
        },
        "samples": [
            "/price/AAPL",
            "/price/NVDA",
            "/price/RELIANCE.NS",
            "/price/BTC-USD",
            "/strike/AAPL",
            "/strike/SPY?step=5",
        ],
    }


@app.get("/health", summary="Health Check")
async def health_check() -> Dict[str, str]:
    """Simple health probe for monitoring uptime."""
    return {"status": "healthy"}


@app.get(
    "/price/{ticker}",
    response_model=TickerPriceResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get Live Ticker Price",
)
async def get_price(
    ticker: str = PathParam(..., description="Stock or asset symbol, e.g. AAPL, MSFT, RELIANCE.NS, BTC-USD")
) -> TickerPriceResponse:
    """Fetch real-time regular market price, day change, and 52-week statistics for a given ticker."""
    try:
        return await finance_service.get_price(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch price for {ticker}: {e}")


@app.get(
    "/strike/{ticker}",
    response_model=TickerStrikeResponse,
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Get Live Price & Strike Ladder",
)
async def get_strike(
    ticker: str = PathParam(..., description="Stock or asset symbol, e.g. AAPL, TSLA, NIFTY"),
    step: Optional[float] = Query(
        None,
        gt=0,
        description="Optional custom strike interval. If omitted, an interval is chosen based on price scale.",
    ),
) -> TickerStrikeResponse:
    """Fetch live spot price and calculate At-The-Money (ATM), ITM, and OTM strike recommendations."""
    try:
        return await finance_service.get_strikes(ticker, custom_step=step)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate strike for {ticker}: {e}")


@app.get(
    "/quote/{ticker}",
    summary="Get Full Raw Metadata Quote",
)
async def get_quote(
    ticker: str = PathParam(..., description="Stock or asset symbol, e.g. AAPL, GOOGL")
) -> Dict[str, Any]:
    """Return comprehensive market metadata directly from Yahoo Finance."""
    try:
        return await finance_service.fetch_ticker_data(ticker)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch quote for {ticker}: {e}")


if __name__ == "__main__":
    import uvicorn
    # Default to port 8001 to avoid conflicts with other local dev servers on 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=True)
