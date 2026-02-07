"""Google Places + Street View API integration."""

import os
import hashlib
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image

PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
STREET_VIEW_URL = "https://maps.googleapis.com/maps/api/streetview"
STREET_VIEW_META_URL = "https://maps.googleapis.com/maps/api/streetview/metadata"

CACHE_DIR = Path("cache")


def _get_api_key() -> str:
    key = os.environ.get("GOOGLE_API_KEY", "")
    if not key:
        raise RuntimeError(
            "GOOGLE_API_KEY not set. Export it or add it to a .env file.\n"
            "See .env.example for details."
        )
    return key


def search_places(query: str, max_results: int = 20) -> list[dict]:
    """Search for places using the Google Places Text Search API.

    Returns a list of dicts with keys:
        name, address, lat, lng, place_id, types
    """
    api_key = _get_api_key()

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": (
            "places.displayName,"
            "places.formattedAddress,"
            "places.location,"
            "places.id,"
            "places.types,"
            "places.googleMapsUri"
        ),
    }

    body = {
        "textQuery": query,
        "pageSize": min(max_results, 20),
    }

    resp = requests.post(PLACES_TEXT_SEARCH_URL, json=body, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for place in data.get("places", []):
        loc = place.get("location", {})
        results.append({
            "name": place.get("displayName", {}).get("text", "Unknown"),
            "address": place.get("formattedAddress", ""),
            "lat": loc.get("latitude", 0.0),
            "lng": loc.get("longitude", 0.0),
            "place_id": place.get("id", ""),
            "types": place.get("types", []),
            "maps_url": place.get("googleMapsUri", ""),
        })

    return results


def _cache_path(lat: float, lng: float, size: str) -> Path:
    """Return a deterministic cache file path for a street view image."""
    key = f"{lat:.6f}_{lng:.6f}_{size}"
    h = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.jpg"


def has_street_view(lat: float, lng: float) -> bool:
    """Check whether Street View imagery exists at this location."""
    api_key = _get_api_key()
    params = {"location": f"{lat},{lng}", "key": api_key}
    resp = requests.get(STREET_VIEW_META_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json().get("status") == "OK"


def fetch_street_view_image(
    lat: float,
    lng: float,
    size: str = "400x300",
    heading: int | None = None,
) -> Image.Image | None:
    """Fetch a Street View image for the given coordinates.

    Returns a PIL Image, or None if no imagery is available.
    Uses a local file cache to avoid duplicate API calls.
    """
    cached = _cache_path(lat, lng, size)
    if cached.exists():
        return Image.open(cached)

    api_key = _get_api_key()
    params = {
        "location": f"{lat},{lng}",
        "size": size,
        "key": api_key,
        "return_error_code": "true",
    }
    if heading is not None:
        params["heading"] = heading

    resp = requests.get(STREET_VIEW_URL, params=params, timeout=15)

    if resp.status_code != 200:
        return None

    img = Image.open(BytesIO(resp.content))

    # Cache to disk
    CACHE_DIR.mkdir(exist_ok=True)
    img.save(cached, "JPEG")

    return img
