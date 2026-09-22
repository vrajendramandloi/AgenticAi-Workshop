"""Tools Package for a5_reflection_agents
======================================
Exposes thread-safe tools for multi-agent workflows:
- `web_search`: Thread-safe, rate-limited, and cached web search tool.
- `ThreadSafeWebSearch`: Class providing thread-safe search with metrics.
"""

from .web_search_tool import web_search, ThreadSafeWebSearch, default_web_search
from .init_tools.location_cache import location_cache, get_current_location
from .calculation_tools import calculate_budget_breakdown, exit_loop
from .html_export_tool import generate_beautiful_proposal_html

__all__ = [
    "web_search",
    "ThreadSafeWebSearch",
    "default_web_search",
    "location_cache",
    "get_current_location",
    "calculate_budget_breakdown",
    "exit_loop",
    "generate_beautiful_proposal_html",
]

