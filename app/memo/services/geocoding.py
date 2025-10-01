from math import atan2, cos, radians, sin, sqrt
from typing import Optional

import requests
from django.core.cache import cache


class GeocodingService:
    """Service for geocoding Norwegian addresses using Kartverket API"""

    KARTVERKET_SEARCH_URL = "https://ws.geonorge.no/adresser/v1/sok"
    CACHE_TIMEOUT = 86400 * 30  # 30 days

    @classmethod
    def geocode_address(cls, address: str) -> Optional[dict]:
        """
        Geocode a Norwegian address using Kartverket API

        Args:
            address: Norwegian address string

        Returns:
            dict: {'lat': float, 'lon': float, 'accuracy': str}
            None: if geocoding failed
        """
        if not address or not address.strip():
            return None

        # Normalize address for cache key (replace problematic characters)
        normalized_address = address.lower().strip().replace(" ", "_").replace(":", "_")
        cache_key = f"geocode_{normalized_address}"

        # Check cache first
        cached_result = cache.get(cache_key)
        if cached_result:
            return cached_result

        try:
            response = requests.get(
                cls.KARTVERKET_SEARCH_URL,
                params={"sok": address, "treffPerSide": 1},
                timeout=5,
            )

            if not response.ok:
                return None

            data = response.json()

            if data.get("adresser") and len(data["adresser"]) > 0:
                address_data = data["adresser"][0]

                if address_data.get("representasjonspunkt"):
                    result = {
                        "lat": address_data["representasjonspunkt"]["lat"],
                        "lon": address_data["representasjonspunkt"]["lon"],
                        "accuracy": "exact",
                    }
                    # Cache successful result
                    cache.set(cache_key, result, cls.CACHE_TIMEOUT)
                    return result

            return None

        except requests.exceptions.Timeout:
            print(f"Geocoding timeout for '{address}'")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Geocoding request error for '{address}': {e}")
            return None
        except Exception as e:
            print(f"Geocoding error for '{address}': {e}")
            return None

    @classmethod
    def calculate_distance(
        cls, lat1: float, lon1: float, lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates using Haversine formula

        Args:
            lat1, lon1: First coordinate (latitude, longitude)
            lat2, lon2: Second coordinate (latitude, longitude)

        Returns:
            float: Distance in meters
        """
        R = 6371e3  # Earth's radius in meters

        φ1 = radians(lat1)
        φ2 = radians(lat2)
        Δφ = radians(lat2 - lat1)
        Δλ = radians(lon2 - lon1)

        a = sin(Δφ / 2) * sin(Δφ / 2) + cos(φ1) * cos(φ2) * sin(Δλ / 2) * sin(Δλ / 2)
        c = 2 * atan2(sqrt(a), sqrt(1 - a))

        return R * c  # meters

    @classmethod
    def get_bounding_box(cls, lat: float, lon: float, radius: float) -> dict:
        """
        Calculate bounding box for proximity search

        Args:
            lat: Center latitude
            lon: Center longitude
            radius: Radius in meters

        Returns:
            dict: {'lat_min', 'lat_max', 'lon_min', 'lon_max'}
        """
        # Approximate degrees per meter
        # At latitude 60° (Norway), 1 degree lat ≈ 111km, 1 degree lon ≈ 55km
        lat_degrees_per_meter = 1 / 111000
        lon_degrees_per_meter = 1 / (111000 * cos(radians(lat)))

        lat_delta = radius * lat_degrees_per_meter
        lon_delta = radius * lon_degrees_per_meter

        return {
            "lat_min": lat - lat_delta,
            "lat_max": lat + lat_delta,
            "lon_min": lon - lon_delta,
            "lon_max": lon + lon_delta,
        }
