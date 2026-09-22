import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Prevent __pycache__ bytecode generation in this project
sys.dont_write_bytecode = True

# Ensure tools directory and a5_reflection_agents root are in sys.path
_tools_dir = Path(__file__).resolve().parent.parent
_agent_root = _tools_dir.parent
for _p in [str(_tools_dir), str(_agent_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from ..model.location_object import LocationObject
except (ImportError, ValueError):
    try:
        from model.location_object import LocationObject
    except ImportError:
        from tools.model.location_object import LocationObject

try:
    from . import location_tool
except (ImportError, ValueError):
    try:
        import location_tool
    except ImportError:
        from tools.init_tools import location_tool



class LocationCache:
    _cached_location: Optional[LocationObject] = None
    _instance: Optional["LocationCache"] = None

    def __new__(cls) -> "LocationCache":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            raw_result = location_tool.get_current_location()
            cls._instance._cached_location = LocationObject.from_json(raw_result)
        return cls._instance

    def __init__(self) -> None:
        # Prevent re-fetching when __new__ returns the existing singleton instance
        pass

    @property
    def location(self) -> Optional[LocationObject]:
        return self._cached_location

    @property
    def city(self) -> Optional[str]:
        return self._cached_location.city if self._cached_location else None

    @property
    def area(self) -> Optional[str]:
        return self._cached_location.area if self._cached_location else None

    @property
    def road(self) -> Optional[str]:
        return self._cached_location.road if self._cached_location else None

    @property
    def landmark(self) -> Optional[str]:
        return self._cached_location.landmark if self._cached_location else None

    @property
    def formatted(self) -> Optional[str]:
        return self._cached_location.formatted if self._cached_location else None

    @property
    def display_name(self) -> Optional[str]:
        return self._cached_location.display_name if self._cached_location else None

    @property
    def coordinates(self) -> Optional[Tuple[str, str]]:
        return self._cached_location.coordinates if self._cached_location else None

    def get_current_location(self) -> Dict[str, Any]:
        """Get the user's current physical location (city, area, road, landmark, coordinates)."""
        return self._cached_location.to_dict() if self._cached_location else {}


# Singleton instance for the agent session (pre-initialized on import)
location_cache = LocationCache()

# Module-level tool function pointing to the pre-initialized singleton's method
get_current_location = location_cache.get_current_location


if __name__ == "__main__":
    l1 = LocationCache()
    l2 = LocationCache()

    print("=== Simple Location Cache ===")
    print("Same instance:", l1 is l2)
    print("City:", l1.city)
    print("Area:", l1.area)
    print("Road:", l1.road)
    print("Landmark:", l1.landmark)
    print("Coordinates:", l1.coordinates)
    print("Formatted:", l1.formatted)
    print("Dict data:", l1.get_current_location())
