"""Place search (Nominatim) + Street View capture (Selenium). No API keys needed."""

import hashlib
import time
from io import BytesIO
from pathlib import Path

import requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
CACHE_DIR = Path("cache")

# Nominatim requires a descriptive User-Agent (no API key needed)
_SESSION = requests.Session()
_SESSION.headers.update({
    "User-Agent": "StreetViewScraperGrid/1.0 (personal research tool)"
})

# Reusable browser instance
_driver: webdriver.Chrome | None = None


def search_places(query: str, max_results: int = 20) -> list[dict]:
    """Search for places using OpenStreetMap Nominatim (free, no API key).

    Returns a list of dicts with keys:
        name, address, lat, lng, place_id, types, maps_url
    """
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": min(max_results, 50),
    }

    resp = _SESSION.get(NOMINATIM_URL, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    results = []
    for place in data:
        lat = float(place.get("lat", 0))
        lng = float(place.get("lon", 0))
        results.append({
            "name": place.get("name") or place.get("display_name", "Unknown").split(",")[0],
            "address": place.get("display_name", ""),
            "lat": lat,
            "lng": lng,
            "place_id": str(place.get("place_id", "")),
            "types": [place.get("type", ""), place.get("category", "")],
            "maps_url": f"https://www.google.com/maps/@{lat},{lng},17z",
        })

    # Nominatim rate limit: 1 request/sec
    time.sleep(1)
    return results


def _get_driver() -> webdriver.Chrome:
    """Create or return a reusable headless Chrome instance."""
    global _driver
    if _driver is not None:
        return _driver

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=600,400")
    # Suppress console noise
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    _driver = webdriver.Chrome(options=options)
    return _driver


def quit_driver():
    """Shut down the reusable browser instance."""
    global _driver
    if _driver is not None:
        _driver.quit()
        _driver = None


def _cache_path(lat: float, lng: float) -> Path:
    key = f"{lat:.6f}_{lng:.6f}"
    h = hashlib.md5(key.encode()).hexdigest()
    return CACHE_DIR / f"{h}.png"


def fetch_street_view_image(lat: float, lng: float) -> Image.Image | None:
    """Capture a Street View screenshot via headless Chrome.

    Opens Google Maps Street View at the given coordinates and takes a
    screenshot. Returns a PIL Image, or None if Street View isn't available.
    Uses a local file cache to avoid duplicate captures.
    """
    cached = _cache_path(lat, lng)
    if cached.exists():
        return Image.open(cached)

    # Google Maps Street View URL — drops directly into street-level view
    url = (
        f"https://www.google.com/maps/@{lat},{lng},3a,75y,0h,90t/data=!3m6"
        f"!1e1!3m4!1s!2e0!7i16384!8i8192"
    )

    try:
        driver = _get_driver()
        driver.get(url)

        # Wait for the Street View canvas or imagery to load
        time.sleep(4)

        # Check if we actually landed in Street View by looking for the canvas
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas, .widget-scene"))
            )
        except TimeoutException:
            return None

        # Dismiss any consent/cookie dialogs that might overlay the view
        try:
            consent_btn = driver.find_element(
                By.CSS_SELECTOR,
                "button[aria-label='Accept all'], form[action*='consent'] button"
            )
            consent_btn.click()
            time.sleep(1)
        except Exception:
            pass

        # Take screenshot
        png_data = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png_data))

        # Cache to disk
        CACHE_DIR.mkdir(exist_ok=True)
        img.save(cached, "PNG")

        return img

    except Exception:
        return None
