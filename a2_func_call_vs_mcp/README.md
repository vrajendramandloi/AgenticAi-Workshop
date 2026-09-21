# Project 2: Function Calling vs. Model Context Protocol (MCP)

This project demonstrates the core architectural differences between **Native Function Calling (In-Process)** and **Model Context Protocol (Client-Server)** using live tools:
1. `get_current_location` (Hardware/IP Geolocation)
2. `web_search` (DuckDuckGo search)

---

## 1. The Core Architectural Difference

```
NATIVE FUNCTION CALLING (In-Process):
┌──────────────────────────────────────────────┐
│                  Python Process               │
│  ┌────────────┐    direct in-memory pointer  │
│  │ LLM Agent  │ ───────────────────────────> │ Python Functions
│  └────────────┘                              │ (location, search)
└──────────────────────────────────────────────┘
* High Coupling: Trapped in this single Python application.


MODEL CONTEXT PROTOCOL (MCP) (Client-Server):
┌────────────────────┐   JSON-RPC over stdio   ┌────────────────────────────────┐
│ LLM Agent (Client) │ <=====================> │ Standalone MCP Server Process  │
└────────────────────┘                         │ (mcp_server.py)                │
                                               │ - get_current_location         │
                                               │ - web_search                   │
                                               └────────────────────────────────┘
                                                               ▲
                                 Can also be plugged into ────┤
                                 - Claude Desktop / Cursor IDE
                                 - Antigravity IDE / VS Code
                                 - Node.js / Go / Rust Agents
```

---

## 2. File Organization in this Project

- **`mcp_server.py`**: Standalone MCP Server exposing the tools over stdio (JSON-RPC).
- **`agent.py`**: The ADK Agent powered exclusively by MCP via `McpToolset`.
- **`init_tools/`**: Internal location acquisition tools and cache.

---

## 3. How to Demonstrate to Your Audience

### Step 1: Show the Standalone MCP Server Schemas
Demonstrate that the tools run as an independent server with zero agent coupling:
```powershell
python mcp_server.py --list
```

### Step 2: Run the Pure MCP Agent Web Server
```powershell
python -m google.adk.cli web .
```
Ask: *"Where am I and search for the latest news in my city"*
Notice the agent does not have any local tool functions in its memory—it communicates directly with `mcp_server.py` over stdio!

---

## 4. Summary Comparison Table

| Feature | Native Function Calling | Model Context Protocol (MCP) |
| :--- | :--- | :--- |
| **Architecture** | In-Process Python Function pointers | Client-Server JSON-RPC protocol |
| **Coupling** | Tightly coupled to Python app | Decoupled (Language-Agnostic) |
| **Tool Location** | Same memory space as Agent | Standalone Process / Remote Server |
| **Reusability** | Locked to this Python agent | Universal (Claude, Cursor, Any Agent) |
| **Discovery** | Python AST / reflection | Standard `tools/list` protocol |
| **Security** | Runs with full agent privileges | Can run in Docker / isolated sandbox |
