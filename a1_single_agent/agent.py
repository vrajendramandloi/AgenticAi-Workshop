import json
import os
import urllib.parse
import urllib.request
from google.adk.agents.llm_agent import Agent

try:
    from instructions import (
        TOOL_AGENT_INSTRUCTIONS,
    )
except ImportError:
    from .instructions import (
        TOOL_AGENT_INSTRUCTIONS,
    )

from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv
    # Explicitly load root workspace .env (d:\WORK\WORKSPACE\AI\.env)
    _root_env = Path(__file__).resolve().parent.parent / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
    MODEL_NAME = os.environ.get("GOOGLE_GENAI_MODEL", "gemini-3.5-flash-lite")
    from init_tools.location_cache import location_cache
except ImportError:
    from .init_tools.location_cache import location_cache
    print("ERROR: Import Error while importing Model")


#Tool To query online Stuff.
def web_search(query: str) -> str:
    """Free web search tool with zero API keys or limits."""
    url = f"https://api.duckduckgo.com/?q={urllib.parse.quote(query)}&format=json&no_html=1&skip_disambig=1"
    req = urllib.request.Request(url, headers={"User-Agent": "RyanAgent/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("AbstractText") or f"Searched for: {query}"
    except Exception as e:
        return f"Search error: {e}"


root_agent = Agent(
    name="ryan",
    description="A Tool-using Agent to fetch information via web search and physical location",
    model=MODEL_NAME,
    tools=[web_search, location_cache.get_current_location],
    instruction=TOOL_AGENT_INSTRUCTIONS,
)
