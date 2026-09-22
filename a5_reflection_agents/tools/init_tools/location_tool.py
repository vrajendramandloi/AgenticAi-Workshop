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

import os
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import json
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple

try:
    from dotenv import find_dotenv, load_dotenv
    _root_env = Path(__file__).resolve().parent.parent.parent / ".env"
    if _root_env.exists():
        load_dotenv(dotenv_path=_root_env)
    else:
        load_dotenv(find_dotenv())
except ImportError:
    pass

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
        Primary: OpenStreetMap Nominatim with zoom=18 & addressdetails=1.
        Fallback: BigDataCloud Reverse Geocoding.
        """
        road, landmark, area, city, state, postcode, country, display_name = "", "", "", "", "", "", "", ""

        # 1. Primary: OpenStreetMap Nominatim (zoom=18 for maximum street/building level precision)
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LocationAgent/2.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                geo_data = json.loads(resp.read().decode("utf-8"))
                addr = geo_data.get("address", {})
                display_name = geo_data.get("display_name", "")

                # Specific road / street
                road = addr.get("road") or addr.get("pedestrian") or addr.get("street") or addr.get("footway") or ""

                # Nearby landmark, building, society, or point of interest
                landmark = (
                    addr.get("amenity")
                    or addr.get("building")
                    or addr.get("housing_estate")
                    or addr.get("residential")
                    or addr.get("commercial")
                    or addr.get("leisure")
                    or addr.get("tourism")
                    or addr.get("shop")
                    or ""
                )

                # Area / Suburb / Neighborhood
                area = (
                    addr.get("suburb")
                    or addr.get("neighbourhood")
                    or addr.get("quarter")
                    or addr.get("village")
                    or addr.get("subdistrict")
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
                    road = alt_data.get("localityInfo", {}).get("administrative", [{}])[-1].get("name", "") if alt_data.get("localityInfo") else ""
                    area = alt_data.get("locality", "")
                    city = alt_data.get("city") or alt_data.get("locality") or ""
                    state = alt_data.get("principalSubdivision", "")
                    country = alt_data.get("countryName", "")
                    display_name = f"{city}, {state}, {country}"
            except Exception:
                pass

        return {
            "landmark": landmark,
            "road": road,
            "area": area,
            "city": city,
            "state": state,
            "postal_code": postcode,
            "country": country,
            "display_name": display_name,
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
                address.get("landmark"),
                address.get("road"),
                address.get("area"),
                address.get("city"),
                address.get("state"),
                address.get("postal_code"),
                address.get("country"),
            ]
            if p
        ]
        formatted_address = ", ".join(formatted_parts) if formatted_parts else f"{lat}, {lon}"

        return {
            "success": True,
            "provider": self.provider_name,
            "landmark": address.get("landmark", ""),
            "road": address.get("road", ""),
            "area": address.get("area", ""),
            "city": address.get("city", ""),
            "state": address.get("state", ""),
            "postal_code": address.get("postal_code", ""),
            "country": address.get("country", ""),
            "display_name": address.get("display_name", ""),
            "latitude": lat,
            "longitude": lon,
            "accuracy_meters": accuracy,
            "formatted": formatted_address,
        }


class WindowsNativeLocationProvider(BaseLocationProvider):
    """
    Native Windows provider that accesses hardware sensors and Wi-Fi
    triangulation via Windows Location Services (System.Device.Location).
    Samples coordinate fixes with responsive timing to prevent process timeouts.
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
        var gotFirstReading = new ManualResetEvent(false);
        var allDone = new ManualResetEvent(false);
        double bestAccuracy = double.MaxValue;
        string bestResult = "UNKNOWN";
        object lockObj = new object();

        watcher.PositionChanged += (s, e) => {
            if (!e.Position.Location.IsUnknown) {
                double acc = e.Position.Location.HorizontalAccuracy;
                lock (lockObj) {
                    if (acc < bestAccuracy) {
                        bestAccuracy = acc;
                        bestResult = e.Position.Location.Latitude + "," + e.Position.Location.Longitude + "," + acc;
                    }
                }
                gotFirstReading.Set();
                // If pinpoint accuracy (<= 40m) reached, finish immediately
                if (acc <= 40.0) {
                    allDone.Set();
                }
            }
        };

        watcher.StatusChanged += (s, e) => {
            if (e.Status == GeoPositionStatus.Disabled) {
                lock (lockObj) {
                    if (bestResult == "UNKNOWN") {
                        bestResult = "DISABLED";
                    }
                }
                allDone.Set();
            }
        };

        watcher.Start();

        // Wait up to 3.5s for initial fix
        if (gotFirstReading.WaitOne(3500)) {
            // Once we have a fix, wait up to 1.0s to allow refinement
            allDone.WaitOne(1000);
        }

        watcher.Stop();
        return bestResult;
    }
}
"@; [WinLocation]::GetCoordinates()
"""
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=15,
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


class ConfiguredLocationProvider(BaseLocationProvider):
    """
    Calibrated / User-Configured High Precision Provider.
    Checks for exact desktop coordinates or address in:
    1. Environment variables: USER_LATITUDE, USER_LONGITUDE (or MY_LAT, MY_LON)
    2. Local file: location_config.json (in current directory or workspace)
    """

    @property
    def provider_name(self) -> str:
        return "User Calibrated Desktop Pinpoint (Exact GPS)"

    def get_coordinates(self) -> Optional[Tuple[float, float, Optional[float]]]:
        # 1. Check environment variables
        lat_env = os.environ.get("USER_LATITUDE") or os.environ.get("MY_LAT")
        lon_env = os.environ.get("USER_LONGITUDE") or os.environ.get("MY_LON")
        if lat_env and lon_env:
            try:
                lat = float(lat_env.strip())
                lon = float(lon_env.strip())
                acc = float(os.environ.get("USER_ACCURACY_METERS", "5.0"))
                return (lat, lon, acc)
            except ValueError:
                pass

        # 2. Check location_config.json
        candidate_paths = [
            Path.cwd() / "location_config.json",
            Path(__file__).resolve().parent / "location_config.json",
            Path(__file__).resolve().parent.parent / "location_config.json",
            Path(__file__).resolve().parent.parent.parent / "location_config.json",
        ]
        for cfg_path in candidate_paths:
            if cfg_path.exists():
                try:
                    with open(cfg_path, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                    if "latitude" in cfg and "longitude" in cfg:
                        lat = float(cfg["latitude"])
                        lon = float(cfg["longitude"])
                        acc = float(cfg.get("accuracy_meters", 5.0))
                        return (lat, lon, acc)
                except Exception:
                    pass

        return None


class GoogleWiFiLocationProvider(BaseLocationProvider):
    """
    High-precision Wi-Fi BSSID triangulation using Google Geolocation API.
    Scans surrounding Wi-Fi access points via Windows 'netsh wlan' and queries Google's
    Android Wi-Fi database (typically 15-30m accuracy).
    """

    @property
    def provider_name(self) -> str:
        return "Google Wi-Fi Triangulation (Android BSSID Database)"

    def _scan_nearby_wifi(self) -> list:
        """Scan visible Wi-Fi access point BSSIDs and signal strengths."""
        try:
            res = subprocess.run(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            output = res.stdout or ""
            bssids = []
            current_mac = None
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("BSSID") and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        mac = parts[1].strip()
                        if len(mac.split(":")) == 6 or len(mac.split("-")) == 6:
                            current_mac = mac.replace("-", ":")
                elif line.startswith("Signal") and current_mac:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        sig_str = parts[1].replace("%", "").strip()
                        try:
                            sig_pct = float(sig_str)
                            # Convert 0-100% to dBm (100% ~ -50 dBm, 0% ~ -100 dBm)
                            dbm = int((sig_pct / 2.0) - 100.0)
                            bssids.append({"macAddress": current_mac, "signalStrength": dbm})
                        except Exception:
                            pass
                        current_mac = None
            return bssids
        except Exception:
            return []

    def get_coordinates(self) -> Optional[Tuple[float, float, Optional[float]]]:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None

        wifi_aps = self._scan_nearby_wifi()
        if len(wifi_aps) < 2:
            return None

        url = f"https://www.googleapis.com/geolocation/v1/geolocate?key={api_key}"
        payload = json.dumps({"considerIp": False, "wifiAccessPoints": wifi_aps[:15]}).encode("utf-8")
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if "location" in data:
                lat = float(data["location"]["lat"])
                lon = float(data["location"]["lng"])
                accuracy = float(data.get("accuracy", 25.0))
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

    Priority Order:
    1. User Calibrated Pinpoint (USER_LATITUDE/USER_LONGITUDE in .env or location_config.json) [0-5m accuracy]
    2. Google Wi-Fi Triangulation (Scanning local Wi-Fi BSSIDs via Google API) [15-30m accuracy]
    3. Windows Native Hardware Location (Wi-Fi triangulation with accuracy sampling) [50-100m accuracy]
    4. Network IP Geolocation (ip-api.com fallback)

    Returns address details including landmark, road, area, city, state, country, and coordinates.
    """
    # 1. User Calibrated Pinpoint (Exact GPS)
    config_provider = ConfiguredLocationProvider()
    res_cfg = config_provider.get_full_location()
    if res_cfg.get("success"):
        return res_cfg

    # 2. Google Wi-Fi Triangulation (via local Wi-Fi BSSID scan)
    google_provider = GoogleWiFiLocationProvider()
    res_google = google_provider.get_full_location()
    if res_google.get("success"):
        return res_google

    # 3. Windows Native Hardware Location
    windows_provider = WindowsNativeLocationProvider()
    res_win = windows_provider.get_full_location()
    if res_win.get("success"):
        return res_win

    # 4. Fallback to IP-based location
    ip_provider = IPLocationProvider()
    res_ip = ip_provider.get_full_location()
    if res_ip.get("success"):
        return res_ip

    return {
        "success": False,
        "error": "Failed to determine location from any hardware, Wi-Fi, or network provider.",
    }








if __name__ == "__main__":
    print("Testing live location tool (no cache)...")
    result = get_current_location()
    print(json.dumps(result, indent=2))
