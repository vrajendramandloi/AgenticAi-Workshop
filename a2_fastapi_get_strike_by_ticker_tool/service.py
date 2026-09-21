"""Yahoo Finance Free API Service
================================
Asynchronous client to fetch live market quotes and calculate strike recommendations
using Yahoo Finance's free chart/quote endpoints without requiring external API keys.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

import httpx

from models import StrikeLadder, TickerPriceResponse, TickerStrikeResponse


class YahooFinanceService:
    """Service to fetch real-time market data directly from Yahoo Finance free endpoint."""

    BASE_URL = "https://query1.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=1d"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }

    def __init__(self, cache_ttl_seconds: int = 10) -> None:
        self.cache_ttl = cache_ttl_seconds
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

    def _normalize_ticker(self, ticker: str) -> str:
        """Clean and normalize ticker symbols (e.g. 'aapl' -> 'AAPL')."""
        return ticker.strip().upper()

    async def fetch_ticker_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch raw metadata from Yahoo Finance chart endpoint with TTL caching."""
        symbol = self._normalize_ticker(ticker)
        now = time.time()

        # Return cached response if within TTL
        if symbol in self._cache:
            timestamp, cached_data = self._cache[symbol]
            if now - timestamp < self.cache_ttl:
                return cached_data

        url = self.BASE_URL.format(ticker=symbol)
        async with httpx.AsyncClient(headers=self.HEADERS, timeout=10.0, follow_redirects=True) as client:
            resp = await client.get(url)

            if resp.status_code == 404:
                raise ValueError(f"Ticker symbol '{symbol}' was not found on Yahoo Finance.")
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Yahoo Finance returned HTTP {resp.status_code} for ticker '{symbol}'."
                )

            data = resp.json()

        try:
            chart = data.get("chart", {})
            results = chart.get("result")
            if not results:
                error_info = chart.get("error", {}).get("description", "No market data found.")
                raise ValueError(f"Unable to retrieve quote for '{symbol}': {error_info}")

            meta = results[0].get("meta", {})
            self._cache[symbol] = (now, meta)
            return meta
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Malformed response for ticker '{symbol}': {exc}") from exc

    async def get_price(self, ticker: str) -> TickerPriceResponse:
        """Get the current live price and basic market statistics for a ticker."""
        meta = await self.fetch_ticker_data(ticker)

        symbol = meta.get("symbol") or self._normalize_ticker(ticker)
        current_price = meta.get("regularMarketPrice")
        if current_price is None:
            # Fallback to fulldayPrice or previous close if market is closed
            current_price = meta.get("fulldayPrice") or meta.get("chartPreviousClose")

        if current_price is None:
            raise ValueError(f"Could not determine market price for ticker '{symbol}'.")

        prev_close = meta.get("chartPreviousClose")
        change = None
        pct_change = None
        if prev_close and prev_close > 0:
            change = round(current_price - prev_close, 4)
            pct_change = round((change / prev_close) * 100, 2)

        return TickerPriceResponse(
            ticker=symbol,
            name=meta.get("shortName") or meta.get("longName") or symbol,
            current_price=float(current_price),
            currency=meta.get("currency", "USD"),
            change=change,
            percent_change=pct_change,
            previous_close=prev_close,
            day_high=meta.get("regularMarketDayHigh"),
            day_low=meta.get("regularMarketDayLow"),
            fifty_two_week_high=meta.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=meta.get("fiftyTwoWeekLow"),
            volume=meta.get("regularMarketVolume"),
            exchange=meta.get("exchangeName"),
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def determine_default_step(self, price: float) -> float:
        """Dynamically infer a sensible option strike interval based on price magnitude."""
        if price <= 10:
            return 0.5
        elif price <= 25:
            return 1.0
        elif price <= 50:
            return 2.5
        elif price <= 100:
            return 5.0
        elif price <= 500:
            return 5.0 if price < 250 else 10.0
        elif price <= 1500:
            return 25.0
        elif price <= 3000:
            return 50.0
        elif price <= 10000:
            return 100.0
        else:
            return 500.0

    async def get_strikes(self, ticker: str, custom_step: Optional[float] = None) -> TickerStrikeResponse:
        """Calculate At-The-Money (ATM), ITM, and OTM strikes anchored around the live price."""
        quote = await self.get_price(ticker)
        spot = quote.current_price

        step = custom_step if (custom_step and custom_step > 0) else self.determine_default_step(spot)
        atm_strike = round(spot / step) * step

        # Generate a ladder of 5 strikes below and 5 strikes above ATM
        ladder_strikes = [round(atm_strike + (i * step), 4) for i in range(-5, 6)]

        strike_ladder = StrikeLadder(
            atm_strike=float(atm_strike),
            strike_step=float(step),
            itm_call_strike=round(atm_strike - step, 4),
            otm_call_strike=round(atm_strike + step, 4),
            itm_put_strike=round(atm_strike + step, 4),
            otm_put_strike=round(atm_strike - step, 4),
            call_strikes=ladder_strikes,
            put_strikes=ladder_strikes,
        )

        return TickerStrikeResponse(
            ticker=quote.ticker,
            name=quote.name,
            spot_price=spot,
            currency=quote.currency,
            strikes=strike_ladder,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


# Singleton instance
finance_service = YahooFinanceService()
