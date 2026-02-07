"""Place search + Street View capture via Selenium. No API keys needed."""

import hashlib
import time
import re
import json
from io import BytesIO
from pathlib import Path
from urllib.parse import quote_plus

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException

CACHE_DIR = Path("cache")

# Reusable browser instance
_driver: webdriver.Chrome | None = None


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
    options.add_argument("--window-size=800,600")
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


def search_places(query: str, max_results: int = 20) -> list[dict]:
    """Search for places using Google Maps search via Selenium.

    Returns a list of dicts with keys:
        name, address, lat, lng, place_id, types, maps_url
    """
    driver = _get_driver()
    url = f"https://www.google.com/maps/search/{quote_plus(query)}"
    driver.get(url)

    # Wait for results to load
    time.sleep(4)

    # Dismiss cookie/consent banner if present
    _dismiss_consent(driver)

    time.sleep(2)

    # Scroll the results panel to load more
    try:
        results_panel = driver.find_element(
            By.CSS_SELECTOR, "div[role='feed'], div[role='list']"
        )
        for _ in range(3):
            driver.execute_script(
                "arguments[0].scrollTop = arguments[0].scrollHeight", results_panel
            )
            time.sleep(1.5)
    except Exception:
        pass

    # Extract place links from the results
    places = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
        seen_urls = set()

        for link in links:
            href = link.get_attribute("href") or ""
            if href in seen_urls or "/maps/place/" not in href:
                continue
            seen_urls.add(href)

            # Extract name from the link's aria-label or text
            name = link.get_attribute("aria-label") or link.text.strip()
            if not name:
                continue

            places.append({
                "name": name,
                "address": "",
                "lat": 0.0,
                "lng": 0.0,
                "place_id": "",
                "types": [],
                "maps_url": href,
            })

            if len(places) >= max_results:
                break
    except Exception:
        pass

    # Now visit each place to get the address and coordinates
    for place in places:
        try:
            driver.get(place["maps_url"])
            time.sleep(3)
            _dismiss_consent(driver)

            # Get coordinates from the URL (Google Maps puts them in the URL)
            current_url = driver.current_url
            coord_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
            if coord_match:
                place["lat"] = float(coord_match.group(1))
                place["lng"] = float(coord_match.group(2))

            # Get address from the page
            try:
                addr_el = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[data-item-id='address'] div.fontBodyMedium, "
                    "button[data-item-id='oloc'] div.fontBodyMedium"
                )
                place["address"] = addr_el.text.strip()
            except Exception:
                # Try getting address from the meta/title
                try:
                    title = driver.title
                    if " - " in title:
                        place["address"] = title.split(" - ")[-1].strip()
                except Exception:
                    pass

        except Exception:
            continue

    return places


def _dismiss_consent(driver):
    """Dismiss Google cookie/consent dialogs."""
    try:
        btns = driver.find_elements(
            By.CSS_SELECTOR,
            "button[aria-label='Accept all'], "
            "button[aria-label='Reject all'], "
            "form[action*='consent'] button, "
            "button[jsname='b3VHJd']"
        )
        for btn in btns:
            if btn.is_displayed():
                btn.click()
                time.sleep(1)
                break
    except Exception:
        pass


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
    if lat == 0.0 and lng == 0.0:
        return None

    cached = _cache_path(lat, lng)
    if cached.exists():
        return Image.open(cached)

    url = (
        f"https://www.google.com/maps/@{lat},{lng},3a,75y,0h,90t/data=!3m6"
        f"!1e1!3m4!1s!2e0!7i16384!8i8192"
    )

    try:
        driver = _get_driver()
        driver.get(url)

        time.sleep(4)
        _dismiss_consent(driver)

        # Check if we actually landed in Street View
        try:
            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas, .widget-scene"))
            )
        except TimeoutException:
            return None

        time.sleep(1)

        # Take screenshot
        png_data = driver.get_screenshot_as_png()
        img = Image.open(BytesIO(png_data))

        # Cache to disk
        CACHE_DIR.mkdir(exist_ok=True)
        img.save(cached, "PNG")

        return img

    except Exception:
        return None
