"""Model Context Protocol (MCP) Standalone Server
===============================================
Hosts the live agent tools (location, web search)
over the Model Context Protocol using JSON-RPC via stdio.

Usage:
  - Run as MCP Server for agents (stdio):
      python mcp_server.py
  - Inspect exposed tools (CLI schema demo):
      python mcp_server.py --list
"""

import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict

# Ensure pywin32 subpaths are available on Windows if installed in custom paths
for _p in [Path(p) for p in sys.path if "PythonLibs" in p or "site-packages" in p]:
    for _sub in ["win32", "win32/lib", "pywin32_system32"]:
        _target = str(_p / _sub)
        if _target not in sys.path and (_p / _sub).exists():
            sys.path.append(_target)

# Import location cache
try:
    from init_tools.location_cache import location_cache
except ImportError:
    from .init_tools.location_cache import location_cache

# Initialize MCP Server (supports both MCP 2.x and FastMCP)
try:
    from mcp.server.mcpserver import MCPServer
    server = MCPServer("agent-live-tools-server")
except ImportError:
    from mcp.server.fastmcp import FastMCP
    server = FastMCP("agent-live-tools-server")


@server.tool()
def get_current_location() -> Dict[str, Any]:
    """Retrieve the user's current physical location (city, area, coordinates, country).

    Returns:
        dict: Geographic information containing city, area, country, and coordinates.
    """
    return location_cache.get_current_location()


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


if __name__ == "__main__":
    if "--list" in sys.argv:
        print("=== MCP Server: Registered Tools ===")
        if hasattr(server, "_tool_manager"):
            for tool in server._tool_manager.list_tools():
                print(f"- Tool Name: {tool.name}")
                print(f"  Description: {tool.description.strip()}")
                print(f"  Schema: {tool.parameters}\n")
        else:
            print("Server initialized with tools: get_current_location, web_search")
    else:
        # Run standard MCP server over stdio
        server.run(transport="stdio")
