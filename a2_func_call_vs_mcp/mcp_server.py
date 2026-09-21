"""Model Context Protocol (MCP) Standalone Server
===============================================
Hosts the live agent tools (location, web search, stock price)
over the Model Context Protocol using JSON-RPC via stdio.

Usage:
  - Run as MCP Server for agents (stdio):
      python mcp_server.py
  - Inspect exposed tools (CLI schema demo):
      python mcp_server.py --list
"""

import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Union

# Ensure pywin32 subpaths are available on Windows if installed in custom paths
for _p in [Path(p) for p in sys.path if "PythonLibs" in p or "site-packages" in p]:
    for _sub in ["win32", "win32/lib", "pywin32_system32"]:
        _target = str(_p / _sub)
        if _target not in sys.path and (_p / _sub).exists():
            sys.path.append(_target)

# Import location cache and underlying tools
try:
    from init_tools.location_cache import location_cache
    from init_tools import location_tool
    from model.location_object import LocationObject
except ImportError:
    from .init_tools.location_cache import location_cache
    from .init_tools import location_tool
    from .model.location_object import LocationObject

# Initialize MCP Server (supports both MCP 2.x and FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
    server = MCPServer("agent-live-tools-server")
except ImportError:
    from mcp.server.fastmcp import FastMCP
    server = FastMCP("agent-live-tools-server")


@server.tool()
def get_current_location() -> str:
    """Retrieve the user's current physical location (city, area, coordinates, country).

    Returns:
        str: Parsed, structured geographic information containing city, area, country, postal code, and coordinates.
    """
    # 1. Retrieve location data from LocationCache (runs once and is cached)
    data = location_cache.get_current_location()

    # 2. If the initial response hasn't acquired hardware location yet, wait and retry once
    if not data or data.get("provider") != "Windows Hardware Location (Wi-Fi/GPS)":
        for _ in range(3):
            time.sleep(1.0)
            raw = location_tool.get_current_location()
            if raw.get("provider") == "Windows Hardware Location (Wi-Fi/GPS)":
                location_cache._cached_location = LocationObject.from_json(raw)
                data = location_cache.get_current_location()
                break

    # 3. Parse JSON / Dict response from LocationCache
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    elif not isinstance(data, dict):
        data = {}

    area = data.get("area") or ""
    city = data.get("city") or ""
    state = data.get("state") or ""
    postal_code = data.get("postal_code") or ""
    country = data.get("country") or ""
    lat = data.get("latitude") or ""
    lon = data.get("longitude") or ""
    formatted = data.get("formatted") or ""
    provider = data.get("provider") or ""

    # 4. Format parsed response cleanly for the agent and UI to avoid hallucinations
    parsed_output = (
        f"Area / Neighborhood: {area}\n"
        f"City: {city}\n"
        f"State: {state}\n"
        f"Postal Code: {postal_code}\n"
        f"Country: {country}\n"
        f"Coordinates: {lat}, {lon}\n"
        f"Formatted Address: {formatted}\n"
        f"Provider: {provider}"
    )
    return parsed_output


@server.tool()
def web_search(query: str) -> str:
    """Search the web for up-to-date facts, current news, and information.

    Args:
        query: Search query keywords (e.g. 'latest Python release').

    Returns:
        str: Text summary of search results.
    """
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
    req = urllib.request.Request(url, headers={"User-Agent": "RyanAgent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("AbstractText") or f"Searched for: {query}"
    except Exception as e:
        return f"Search error: {e}"


@server.tool()
def get_stock_price(tickers: str) -> str:
    """Retrieve live stock prices for one or multiple tickers (e.g. BSE, RELIANCE, CONCOR, AAPL).

    Calls the local FastAPI ticker service (http://127.0.0.1:8001/price/{ticker}).
    Note:
      - For Indian stocks (NSE), append '.NS' (e.g. 'CONCOR.NS', 'RELIANCE.NS', 'BSE.NS').
      - For US / Global stocks, do not append '.NS' (e.g. 'AAPL', 'NVDA', 'MSFT').
      - The tool also automatically checks '.NS' as fallback if an unsuffixed symbol is not found.

    Args:
        tickers: Comma-separated or space-separated list of ticker symbols (e.g. 'BSE, RELIANCE, CONCOR, AAPL' or 'AAPL').

    Returns:
        str: Live prices formatted with 1 security per line with full company name, price, and currency.
    """
    symbols = [s.strip().upper() for s in re.split(r'[,;\s]+', tickers) if s.strip()]
    if not symbols:
        return "No ticker symbols provided."

    results = []
    base_api_url = "http://127.0.0.1:8001/price"

    for sym in symbols:
        candidates = [sym]
        # If no exchange suffix is provided, also queue .NS as fallback for Indian equities
        if "." not in sym and "-" not in sym:
            candidates.append(f"{sym}.NS")

        found = False
        last_error = ""

        for cand in candidates:
            url = f"{base_api_url}/{urllib.parse.quote(cand)}"
            req = urllib.request.Request(url, headers={"User-Agent": "MCP-Agent/1.0"})
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    name = (data.get("name") or cand).strip()
                    price = data.get("current_price")
                    currency = (data.get("currency") or "USD").strip()
                    ticker_code = (data.get("ticker") or cand).strip()
                    
                    if isinstance(price, (int, float)):
                        formatted_price = f"{price:.2f}"
                    else:
                        formatted_price = str(price)

                    results.append(f"{name} ({ticker_code}): {formatted_price} {currency}")
                    found = True
                    break
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    last_error = f"{sym}: Ticker not found"
                    continue
                last_error = f"{sym}: HTTP Error {e.code}"
            except urllib.error.URLError:
                last_error = f"{sym}: Service unavailable at {base_api_url} (Ensure FastAPI service is running on port 8001)"
            except TimeoutError:
                last_error = f"{sym}: Request timed out connecting to {base_api_url}"
            except Exception as e:
                last_error = f"{sym}: Error ({e})"

        if not found:
            results.append(last_error or f"{sym}: Price unavailable")

    return "\n".join(results)












if __name__ == "__main__":
    if "--list" in sys.argv:
        print("=== MCP Server: Registered Tools ===")
        if hasattr(server, "_tool_manager"):
            for tool in server._tool_manager.list_tools():
                print(f"- Tool Name: {tool.name}")
                print(f"  Description: {tool.description.strip()}")
                print(f"  Schema: {tool.parameters}\n")
        else:
            print("Server initialized with tools: get_current_location, web_search, get_stock_price")
    else:
        # Run standard MCP server over stdio
        server.run(transport="stdio")
