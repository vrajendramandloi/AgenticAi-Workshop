"""Thread-Safe Web Search Tool
============================
Thread-safe web search tool designed for concurrent multi-agent architectures
(e.g., Google ADK agents running in parallel or asynchronous workflows).

Features:
- Thread-safe rate limiting and request synchronization via threading.Lock
- Thread-safe LRU/TTL caching to prevent redundant requests across agents
- Multi-field extraction from DuckDuckGo (AbstractText, RelatedTopics, Definitions)
- Resilient error handling with safe fallbacks and timeouts
"""

import json
import logging
import sys
import threading
import time
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

# Prevent bytecode generation
sys.dont_write_bytecode = True

logger = logging.getLogger("ThreadSafeWebSearch")


class ThreadSafeWebSearch:
    """
    Thread-safe, rate-limited, and cached web search provider for concurrent agents.
    """

    def __init__(
        self,
        user_agent: str = "VickyMultiAgent/2.0 (Windows; ThreadSafe)",
        timeout_seconds: float = 6.0,
        min_request_interval_seconds: float = 0.35,
        cache_ttl_seconds: float = 300.0,
        max_cache_size: int = 256,
    ):
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.min_request_interval = min_request_interval_seconds
        self.cache_ttl = cache_ttl_seconds
        self.max_cache_size = max_cache_size

        # Synchronization primitives
        self._lock = threading.Lock()
        self._last_request_time = 0.0

        # In-memory thread-safe cache: query_key -> (timestamp, result_string)
        self._cache: Dict[str, tuple[float, str]] = {}

        # Concurrency metrics
        self._total_queries = 0
        self._cache_hits = 0
        self._failed_queries = 0

    def _normalize_query(self, query: str) -> str:
        """Strip punctuation and extra whitespace for consistent cache hits."""
        return " ".join(query.strip().lower().split())

    def _get_from_cache(self, normalized_key: str) -> Optional[str]:
        """Check cache under lock with TTL expiration."""
        with self._lock:
            if normalized_key in self._cache:
                timestamp, cached_result = self._cache[normalized_key]
                if time.time() - timestamp < self.cache_ttl:
                    self._cache_hits += 1
                    return cached_result
                # Expired
                del self._cache[normalized_key]
        return None

    def _put_into_cache(self, normalized_key: str, result: str) -> None:
        """Store result in cache, maintaining max capacity."""
        with self._lock:
            if len(self._cache) >= self.max_cache_size:
                # Evict oldest 20%
                sorted_keys = sorted(self._cache.keys(), key=lambda k: self._cache[k][0])
                for k in sorted_keys[: max(1, self.max_cache_size // 5)]:
                    self._cache.pop(k, None)
            self._cache[normalized_key] = (time.time(), result)

    def _enforce_rate_limit(self) -> None:
        """Ensure minimum delay between consecutive outbound network calls across all threads."""
        with self._lock:
            now = time.time()
            elapsed = now - self._last_request_time
            if elapsed < self.min_request_interval:
                time.sleep(self.min_request_interval - elapsed)
            self._last_request_time = time.time()
            self._total_queries += 1

    def search(self, query: str) -> str:
        """
        Execute a thread-safe web search query.

        Args:
            query: The search term or topic string.

        Returns:
            A clean, informative string containing facts, summaries, or abstracts.
        """
        if not query or not query.strip():
            return "Search error: Empty search query provided."

        clean_query = query.strip()
        cache_key = self._normalize_query(clean_query)

        # 1. Check thread-safe cache
        cached = self._get_from_cache(cache_key)
        if cached is not None:
            return cached

        # 2. Enforce cross-thread rate limiting
        self._enforce_rate_limit()

        # 3. Build HTTP request
        encoded_query = urllib.parse.quote(clean_query)
        url = (
            f"https://api.duckduckgo.com/?q={encoded_query}&format=json"
            f"&no_html=1&skip_disambig=1"
        )
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json",
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8", errors="replace"))

            # 4. Extract meaningful content
            result_parts: List[str] = []

            # Abstract / Direct Answer
            abstract = data.get("AbstractText", "").strip()
            if abstract:
                result_parts.append(abstract)

            # Definition
            definition = data.get("Definition", "").strip()
            if definition and definition not in result_parts:
                result_parts.append(f"Definition: {definition}")

            # Answer
            direct_answer = data.get("Answer", "").strip()
            if direct_answer and direct_answer not in result_parts:
                result_parts.append(f"Answer: {direct_answer}")

            # Related Topics fallback (often contains rich results when AbstractText is empty)
            if not result_parts:
                related = data.get("RelatedTopics", [])
                snippets = []
                for item in related:
                    if isinstance(item, dict) and "Text" in item:
                        text = item["Text"].strip()
                        if text:
                            snippets.append(text)
                    elif isinstance(item, dict) and "Topics" in item:
                        for sub_item in item["Topics"]:
                            if isinstance(sub_item, dict) and "Text" in sub_item:
                                snippets.append(sub_item["Text"].strip())
                    if len(snippets) >= 3:
                        break

                if snippets:
                    result_parts.append("\n".join(f"- {s}" for s in snippets))

            # Final result assembly
            if result_parts:
                final_result = "\n\n".join(result_parts)
            else:
                heading = data.get("Heading", "").strip()
                if heading:
                    final_result = f"Topic Overview ({heading}): No extensive article found, but query is recognized."
                else:
                    final_result = f"Searched online for '{clean_query}'. No direct summary was returned."

            # Cache and return
            self._put_into_cache(cache_key, final_result)
            return final_result

        except urllib.error.HTTPError as e:
            with self._lock:
                self._failed_queries += 1
            return f"Search HTTP error ({e.code}): {e.reason} for query '{clean_query}'"

        except urllib.error.URLError as e:
            with self._lock:
                self._failed_queries += 1
            return f"Search network error: {e.reason}"

        except TimeoutError:
            with self._lock:
                self._failed_queries += 1
            return f"Search timed out after {self.timeout_seconds}s for query '{clean_query}'"

        except Exception as e:
            with self._lock:
                self._failed_queries += 1
            return f"Search unexpected error: {str(e)}"

    def get_stats(self) -> Dict[str, Any]:
        """Return thread-safe telemetry metrics."""
        with self._lock:
            return {
                "total_queries": self._total_queries,
                "cache_hits": self._cache_hits,
                "failed_queries": self._failed_queries,
                "cached_items": len(self._cache),
            }


# Singleton instance for multi-agent sharing
default_web_search = ThreadSafeWebSearch()


# Functional tool interface compatible with Google ADK Agent(tools=[web_search])
def web_search(query: str) -> str:
    """
    Thread-safe web search tool for autonomous AI agents.
    Queries online sources for real-time information, definitions, news, and facts.
    Thread-safe and optimized for concurrent multi-agent pipelines.

    Args:
        query: Concise search query (e.g., 'Switzerland train pass prices 2026', 'current weather Zurich').

    Returns:
        Factual text summary or search snippets retrieved online.
    """
    return default_web_search.search(query)
