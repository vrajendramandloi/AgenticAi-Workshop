# Live Ticker Price & Strike FastAPI Service

A fast, lightweight, and dependency-light REST API built with **FastAPI** to retrieve live stock/crypto market prices and calculate option strike ladders using Yahoo Finance's free endpoints (no API key required).

---

## 🚀 How to Bring Up the Service

### Option 1: Direct Python Command (Recommended)
Runs on `http://127.0.0.1:8001`:
```powershell
cd d:\WORK\WORKSPACE\AI\a2_fastapi_get_strike_by_ticker_tool
python main.py
```

### Option 2: Using Uvicorn CLI
```powershell
cd d:\WORK\WORKSPACE\AI\a2_fastapi_get_strike_by_ticker_tool
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

> **Note**: Port `8001` is used by default so it does not conflict with existing services running on port `8000` (e.g. ADK Web Server).

---

## 📖 Interactive API Documentation

Once the server is running, open in your browser:
- **Swagger UI**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)

---

## 🔌 API Endpoints & Examples

### 1. Get Live Price
`GET /price/{ticker}`

Retrieve current price, percentage change, day high/low, and 52-week statistics.

**Examples**:
- `http://127.0.0.1:8001/price/AAPL` (Apple Inc.)
- `http://127.0.0.1:8001/price/NVDA` (Nvidia)
- `http://127.0.0.1:8001/price/RELIANCE.NS` (NSE India)
- `http://127.0.0.1:8001/price/BTC-USD` (Bitcoin)

**Sample Response (`GET /price/AAPL`)**:
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "current_price": 338.98,
  "currency": "USD",
  "change": 2.85,
  "percent_change": 0.85,
  "previous_close": 336.13,
  "day_high": 340.15,
  "day_low": 336.50,
  "fifty_two_week_high": 341.25,
  "fifty_two_week_low": 164.08,
  "volume": 48219400,
  "exchange": "NMS",
  "timestamp": "2026-09-22T02:40:00.000000Z"
}
```

---

### 2. Get Live Price & Strike Ladder
`GET /strike/{ticker}?step={optional_step}`

Calculates:
- **ATM Strike** (At-The-Money closest strike)
- **ITM / OTM Calls & Puts**
- **Full 11-strike ladder** around current spot price

**Examples**:
- `http://127.0.0.1:8001/strike/AAPL` (Automatic step detection)
- `http://127.0.0.1:8001/strike/SPY?step=5` (Custom strike interval of 5)

**Sample Response (`GET /strike/AAPL`)**:
```json
{
  "ticker": "AAPL",
  "name": "Apple Inc.",
  "spot_price": 338.98,
  "currency": "USD",
  "strikes": {
    "atm_strike": 340.0,
    "strike_step": 10.0,
    "itm_call_strike": 330.0,
    "otm_call_strike": 350.0,
    "itm_put_strike": 350.0,
    "otm_put_strike": 330.0,
    "call_strikes": [290.0, 300.0, 310.0, 320.0, 330.0, 340.0, 350.0, 360.0, 370.0, 380.0, 390.0],
    "put_strikes": [290.0, 300.0, 310.0, 320.0, 330.0, 340.0, 350.0, 360.0, 370.0, 380.0, 390.0]
  },
  "timestamp": "2026-09-22T02:40:00.000000Z"
}
```

---

### 3. Full Quote Metadata
`GET /quote/{ticker}`

Returns complete raw metadata block from Yahoo Finance (trading period, valid ranges, timezone, etc.).

---

### 4. Health Check
`GET /health`

Returns `{"status": "healthy"}`.

---

## 🛠️ Project Structure

```
a2_fastapi_get_strike_by_ticker_tool/
│
├── main.py             # FastAPI entry point & route definitions
├── service.py          # Yahoo Finance free async HTTP client & strike math
├── models.py           # Pydantic schemas for data validation
├── requirements.txt    # Package dependencies
└── README.md           # Documentation & usage guide
```
