"""
Location Tool for AI Agents (No Caching)
========================================
Modular, real-time physical location provider without caching.

Resolution Strategy:
1. Windows Native Location (System.Device.Location via PowerShell) for laptop Wi-Fi / GPS sensors.
2. IP-Based Geolocation (ip-api.com) as network fallback.
3. Reverse Geocoding (OpenStreetMap Nominatim / BigDataCloud) to convert coordinates to human-readable address.

Zero external pip dependencies (uses Python standard library).
"""

import sys
sys.dont_write_bytecode = True

import json
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


class BaseLocationProvider(ABC):
    """Abstract Base Class defining the contract for location providers."""

    @abstractmethod
    def get_coordinates(self) -> Optional[Tuple[float, float, Optional[float]]]:
        """
        Resolve coordinates.
        Returns: (latitude, longitude, accuracy_meters) or None if unavailable.
        """
        pass

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the provider implementation."""
        pass

    def reverse_geocode(self, lat: float, lon: float) -> Dict[str, str]:
        """
        Convert lat/lon to human-readable address components.
        Primary: OpenStreetMap Nominatim, Fallback: BigDataCloud.
        """
        area, city, state, postcode, country = "", "", "", "", ""

        # 1. Primary: OpenStreetMap Nominatim
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            req = urllib.request.Request(url, headers={"User-Agent": "Bella-Location-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                geo_data = json.loads(resp.read().decode("utf-8"))
                addr = geo_data.get("address", {})
                area = (
                    addr.get("suburb")
                    or addr.get("residential")
                    or addr.get("neighbourhood")
                    or addr.get("quarter")
                    or ""
                )
                city = addr.get("city") or addr.get("town") or addr.get("county") or ""
                state = addr.get("state", "")
                postcode = addr.get("postcode", "")
                country = addr.get("country", "")
        except Exception:
            # 2. Fallback: BigDataCloud Reverse Geocoding
            try:
                alt_url = (
                    f"https://api.bigdatacloud.net/data/reverse-geocode-client?"
                    f"latitude={lat}&longitude={lon}&localityLanguage=en"
                )
                req2 = urllib.request.Request(alt_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req2, timeout=5) as resp2:
                    alt_data = json.loads(resp2.read().decode("utf-8"))
                    city = alt_data.get("city") or alt_data.get("locality") or ""
                    state = alt_data.get("principalSubdivision", "")
                    country = alt_data.get("countryName", "")
            except Exception:
                pass

        return {
            "area": area,
            "city": city,
            "state": state,
            "postal_code": postcode,
            "country": country,
        }

    def get_full_location(self) -> Dict[str, Any]:
        """Template method that fetches coordinates and populates complete address details."""
        coords = self.get_coordinates()
        if not coords:
            return {
                "success": False,
                "provider": self.provider_name,
                "error": f"Failed to resolve coordinates from {self.provider_name}",
            }

        lat, lon, accuracy = coords
        address = self.reverse_geocode(lat, lon)
        formatted_parts = [
            p
            for p in [
                address["area"],
                address["city"],
                address["state"],
                address["postal_code"],
                address["country"],
            ]
            if p
        ]
        formatted_address = ", ".join(formatted_parts) if formatted_parts else f"{lat}, {lon}"

        return {
            "success": True,
            "provider": self.provider_name,
            "area": address["area"],
            "city": address["city"],
            "state": address["state"],
            "postal_code": address["postal_code"],
            "country": address["country"],
            "latitude": lat,
            "longitude": lon,
            "accuracy_meters": accuracy,
            "formatted": formatted_address,
        }


class WindowsNativeLocationProvider(BaseLocationProvider):
    """
    Native Windows provider that accesses hardware sensors and Wi-Fi
    triangulation via Windows Location Services (System.Device.Location).
    """

    @property
    def provider_name(self) -> str:
        return "Windows Hardware Location (Wi-Fi/GPS)"

    def get_coordinates(self) -> Optional[Tuple[float, float, Optional[float]]]:
        ps_cmd = """
Add-Type -ReferencedAssemblies System.Device -TypeDefinition @"
using System;
using System.Device.Location;
using System.Threading;
public class WinLocation {
    public static string GetCoordinates() {
        var watcher = new GeoCoordinateWatcher(GeoPositionAccuracy.High);
        var resetEvent = new ManualResetEvent(false);
        string result = "UNKNOWN";
        watcher.PositionChanged += (s, e) => {
            if (!e.Position.Location.IsUnknown) {
                result = e.Position.Location.Latitude + "," + e.Position.Location.Longitude + "," + e.Position.Location.HorizontalAccuracy;
                resetEvent.Set();
            }
        };
        watcher.StatusChanged += (s, e) => {
            if (e.Status == GeoPositionStatus.Disabled) {
                result = "DISABLED";
                resetEvent.Set();
            }
        };
        watcher.Start();
        if (!resetEvent.WaitOne(6000)) {
            result = "TIMEOUT:" + watcher.Status.ToString();
        }
        watcher.Stop();
        return result;
    }
}
"@; [WinLocation]::GetCoordinates()
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=10,
            )
            raw_output = res.stdout.strip()
            parts = raw_output.split(",")
            if len(parts) >= 2:
                lat = float(parts[0])
                lon = float(parts[1])
                accuracy = float(parts[2]) if len(parts) > 2 else None
                return (lat, lon, accuracy)
        except Exception:
            pass

        return None


class IPLocationProvider(BaseLocationProvider):
    """Network-based provider that resolves location from public IP address."""

    def __init__(self, ip: Optional[str] = None):
        self.target_ip = ip.strip() if ip and ip.strip() else ""

    @property
    def provider_name(self) -> str:
        return "IP-Based Geolocation (ip-api.com)"

    def get_coordinates(self) -> Optional[Tuple[float, float, Optional[float]]]:
        url = f"http://ip-api.com/json/{self.target_ip}" if self.target_ip else "http://ip-api.com/json/"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Bella-Location-Agent/1.0"})
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode("utf-8"))
            if data.get("status") == "success":
                lat = float(data["lat"])
                lon = float(data["lon"])
                return (lat, lon, None)
        except Exception:
            pass

        return None


# =====================================================================
# AGENT TOOL FUNCTION (NO CACHE)
# =====================================================================

def get_current_location() -> Dict[str, Any]:
    """
    Get the user's live physical location and address with no caching.

    First tries the laptop's native hardware location (Wi-Fi/GPS triangulation).
    If hardware location is disabled or unavailable, falls back to IP-based geolocation.
    Returns address details including area, city, state, country, and coordinates.

    Returns:
        Dict[str, Any]: {
            "success": bool,
            "provider": str,
            "area": str,
            "city": str,
            "state": str,
            "postal_code": str,
            "country": str,
            "latitude": float,
            "longitude": float,
            "accuracy_meters": Optional[float],
            "formatted": str
        }
    """
    # 1. Try Windows native hardware location
    windows_provider = WindowsNativeLocationProvider()
    res = windows_provider.get_full_location()
    if res.get("success"):
        return res

    # 2. Fallback to IP-based location
    ip_provider = IPLocationProvider()
    res_ip = ip_provider.get_full_location()
    if res_ip.get("success"):
        return res_ip

    return {
        "success": False,
        "error": "Failed to determine location from hardware sensor or network IP.",
    }








if __name__ == "__main__":
    print("Testing live location tool (no cache)...")
    result = get_current_location()
    print(json.dumps(result, indent=2))
