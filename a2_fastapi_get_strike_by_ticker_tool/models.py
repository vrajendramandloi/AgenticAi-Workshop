"""Pydantic Models for Ticker Price and Strike API
=================================================
Structured schemas for request validation and response serialization.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class TickerPriceResponse(BaseModel):
    """Schema for live ticker price response."""
    ticker: str = Field(..., description="Stock or asset symbol, e.g. AAPL, NVDA, RELIANCE.NS")
    name: Optional[str] = Field(None, description="Company or asset name")
    current_price: float = Field(..., description="Current live regular market price")
    currency: str = Field("USD", description="Trading currency, e.g. USD, INR, EUR")
    change: Optional[float] = Field(None, description="Absolute change from previous close")
    percent_change: Optional[float] = Field(None, description="Percentage change from previous close")
    previous_close: Optional[float] = Field(None, description="Previous trading day closing price")
    day_high: Optional[float] = Field(None, description="Intraday high price")
    day_low: Optional[float] = Field(None, description="Intraday low price")
    fifty_two_week_high: Optional[float] = Field(None, description="52-week highest price")
    fifty_two_week_low: Optional[float] = Field(None, description="52-week lowest price")
    volume: Optional[int] = Field(None, description="Regular market trading volume")
    exchange: Optional[str] = Field(None, description="Exchange name, e.g. NMS, NSE")
    timestamp: str = Field(..., description="ISO 8601 formatted timestamp of quote retrieval")


class StrikeLadder(BaseModel):
    """Calculated option strike ladder around spot price."""
    atm_strike: float = Field(..., description="At-The-Money (ATM) strike closest to spot price")
    strike_step: float = Field(..., description="Calculated or specified strike step interval")
    itm_call_strike: float = Field(..., description="Immediate In-The-Money (ITM) call strike (ATM - step)")
    otm_call_strike: float = Field(..., description="Immediate Out-Of-The-Money (OTM) call strike (ATM + step)")
    itm_put_strike: float = Field(..., description="Immediate In-The-Money (ITM) put strike (ATM + step)")
    otm_put_strike: float = Field(..., description="Immediate Out-Of-The-Money (OTM) put strike (ATM - step)")
    call_strikes: List[float] = Field(default_factory=list, description="Ladder of strikes above and below spot")
    put_strikes: List[float] = Field(default_factory=list, description="Ladder of strikes above and below spot")


class TickerStrikeResponse(BaseModel):
    """Schema for strike recommendation and live price."""
    ticker: str = Field(..., description="Asset symbol")
    name: Optional[str] = Field(None, description="Company or asset name")
    spot_price: float = Field(..., description="Live spot price used to anchor strike selection")
    currency: str = Field("USD", description="Trading currency")
    strikes: StrikeLadder = Field(..., description="Detailed strike breakdown")
    timestamp: str = Field(..., description="Timestamp of calculation")


class ErrorResponse(BaseModel):
    """Standardized error response schema."""
    success: bool = False
    error: str = Field(..., description="Detailed error description")
    ticker: Optional[str] = Field(None, description="Requested ticker if applicable")
