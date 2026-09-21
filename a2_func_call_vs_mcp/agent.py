"""Project 2: Model Context Protocol (MCP) Agent
==============================================
Demonstrates an autonomous AI agent powered completely by the Model Context
Protocol (MCP).

Architecture:
- The Agent acts as an MCP Client.
- The tools (location, web search, stock price) are hosted in an isolated,
  independent process (`mcp_server.py`).
- The Agent connects over standard JSON-RPC (stdio) and discovers tools
  dynamically at runtime without importing them into memory.
"""

import os
import sys
from pathlib import Path
from google.adk.agents.llm_agent import Agent

# Ensure pywin32 subpaths are available on Windows if installed in custom paths
for _p in [Path(p) for p in sys.path if "PythonLibs" in p or "site-packages" in p]:
    for _sub in ["win32", "win32/lib", "pywin32_system32"]:
        _target = str(_p / _sub)
        if _target not in sys.path and (_p / _sub).exists():
            sys.path.append(_target)

# Load environment configuration from workspace root (.env)
from dotenv import load_dotenv, find_dotenv
_root_env = Path(__file__).resolve().parent.parent / ".env"
if _root_env.exists():
    load_dotenv(dotenv_path=_root_env)
else:
    load_dotenv(find_dotenv())

MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")

try:
    from instructions import TOOL_AGENT_INSTRUCTIONS
except ImportError:
    from .instructions import TOOL_AGENT_INSTRUCTIONS

# =========================================================================
# MODEL CONTEXT PROTOCOL (MCP) TOOLSET
# =========================================================================
# The agent does NOT import Python tool functions directly into memory.
# Instead, it connects to an independent MCP server process via stdio.
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset,
    StdioConnectionParams,
    StdioServerParameters,
)

_server_script = str(Path(__file__).resolve().parent / "mcp_server.py")
mcp_toolset = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=sys.executable,
            args=[_server_script],
        )
    )
)

root_agent = Agent(
    name="mark",
    description="Tool-using Agent powered exclusively by Model Context Protocol (MCP)",
    model=MODEL_NAME,
    tools=[mcp_toolset],
    instruction=TOOL_AGENT_INSTRUCTIONS,
)
