import json
import sys
from typing import Any, Optional, Tuple, Union

# Prevent __pycache__ bytecode generation in this project
sys.dont_write_bytecode = True


def _to_str(val: Any) -> Optional[str]:
    """Convert present value to string, leave None as None."""
    if val is None:
        return None
    if isinstance(val, bool):
        return "true" if val else "false"
    return str(val)


class LocationObject:
    # Class-level variables (default schema)
    success: Optional[str] = None
    provider: Optional[str] = None
    area: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[str] = None
    longitude: Optional[str] = None
    accuracy_meters: Optional[str] = None
    formatted: Optional[str] = None
    error: Optional[str] = None

    def __init__(self, data: Optional[Union[str, dict]] = None) -> None:
        # __init__ is now just 2 lines!
        if data:
            self.parse(data)

    def parse(self, data: Union[str, dict]) -> "LocationObject":
        """Parses JSON string or dictionary and stores all fields as strings."""
        if isinstance(data, str):
            data = json.loads(data)

        self.success = _to_str(data.get("success"))
        self.provider = _to_str(data.get("provider"))
        self.area = _to_str(data.get("area"))
        self.city = _to_str(data.get("city"))
        self.state = _to_str(data.get("state"))
        self.postal_code = _to_str(data.get("postal_code"))
        self.country = _to_str(data.get("country"))
        self.latitude = _to_str(data.get("latitude"))
        self.longitude = _to_str(data.get("longitude"))
        self.accuracy_meters = _to_str(data.get("accuracy_meters"))
        self.formatted = _to_str(data.get("formatted"))
        self.error = _to_str(data.get("error"))
        return self

    @classmethod
    def from_json(cls, data: Union[str, dict]) -> "LocationObject":
        """Factory method: LocationObject.from_json(raw_json_or_dict)."""
        return cls(data)

    @property
    def coordinates(self) -> Optional[Tuple[str, str]]:
        """Return (latitude, longitude) as string tuple."""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None

    def to_dict(self) -> dict:
        """Return dictionary of all location fields."""
        return {
            "success": self.success,
            "provider": self.provider,
            "area": self.area,
            "city": self.city,
            "state": self.state,
            "postal_code": self.postal_code,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "accuracy_meters": self.accuracy_meters,
            "formatted": self.formatted,
            "error": self.error,
        }





if __name__ == "__main__":
    # Test with original mixed-type sample (bool, float, int, str)
    raw_sample = {
        "success": True,
        "provider": "Windows Hardware Location (Wi-Fi/GPS)",
        "area": "Kotra Sultanabad",
        "city": "Bhopal",
        "state": "Madhya Pradesh",
        "postal_code": "462001",
        "country": "India",
        "latitude": 23.21628546729,
        "longitude": 77.3921657890769,
        "accuracy_meters": 192.0,
        "formatted": "Kotra Sultanabad, Bhopal, Madhya Pradesh, 462001, India",
    }

    print("=== Testing Basic LocationObject (String-converted) ===")
    loc = LocationObject.from_json(raw_sample)

    print("Type of loc.latitude:", type(loc.latitude), "Value:", repr(loc.latitude))
    print("Type of loc.accuracy_meters:", type(loc.accuracy_meters), "Value:", repr(loc.accuracy_meters))
    print("Type of loc.success:", type(loc.success), "Value:", repr(loc.success))
    print("Coordinates:", loc.coordinates)
    print("Area:", loc.area)
    print("City:", loc.city)