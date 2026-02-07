"""Place search + image capture via Selenium. No API keys needed."""

import hashlib
import time
import re
from io import BytesIO
from pathlib import Path
from urllib.parse import quote_plus

from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

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
    options.add_argument("--window-size=1200,900")
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


def _cache_path(name: str) -> Path:
    h = hashlib.md5(name.encode()).hexdigest()
    return CACHE_DIR / f"{h}.png"


def _capture_place_image(driver, place_name: str) -> Image.Image | None:
    """Capture the place's hero image from the currently-loaded Maps page.

    Tries to find the main photo element on the Google Maps place page
    and screenshots it. Falls back to a full-page screenshot cropped to
    the top-left area where the photo typically appears.
    """
    cached = _cache_path(place_name)
    if cached.exists():
        return Image.open(cached)

    try:
        # Try to find and screenshot the main place photo
        photo_el = None
        selectors = [
            "button[jsaction*='heroHeaderImage'] img",
            "img.Ep1eld",
            "div[class*='hero'] img",
            "a[data-photo-index='0'] img",
            "img[decoding='async'][src*='googleusercontent']",
        ]
        for sel in selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, sel)
                for el in elements:
                    if el.is_displayed() and el.size["height"] > 50:
                        photo_el = el
                        break
                if photo_el:
                    break
            except Exception:
                continue

        if photo_el:
            png_data = photo_el.screenshot_as_png
            img = Image.open(BytesIO(png_data))
        else:
            # Fallback: screenshot the whole page and crop the top portion
            # which usually shows the map + place info
            png_data = driver.get_screenshot_as_png()
            full = Image.open(BytesIO(png_data))
            # Crop to roughly the left panel area where the place info is
            w, h = full.size
            img = full.crop((0, 0, min(w, 400), min(h, 300)))

        CACHE_DIR.mkdir(exist_ok=True)
        img.save(cached, "PNG")
        return img

    except Exception:
        return None


def search_places(query: str, max_results: int = 20, on_progress=None) -> tuple[list[dict], list[Image.Image | None]]:
    """Search for places and capture images in one pass.

    Uses Google Maps search via Selenium. Visits each result page to
    extract address, coordinates, and a screenshot.

    Args:
        query: Search string (e.g. "metal shops in Houston TX")
        max_results: Max number of results to return.
        on_progress: Optional callback(current_index, total, place_name)
            called as each place is processed.

    Returns:
        Tuple of (places_list, images_list).
    """
    driver = _get_driver()
    url = f"https://www.google.com/maps/search/{quote_plus(query)}"
    driver.get(url)

    time.sleep(4)
    _dismiss_consent(driver)
    time.sleep(2)

    # Scroll the results panel to load more results
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

    # Extract place links from the search results
    place_links = []
    try:
        links = driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
        seen_urls = set()

        for link in links:
            href = link.get_attribute("href") or ""
            if href in seen_urls or "/maps/place/" not in href:
                continue
            seen_urls.add(href)

            name = link.get_attribute("aria-label") or link.text.strip()
            if not name:
                continue

            place_links.append({"name": name, "url": href})
            if len(place_links) >= max_results:
                break
    except Exception:
        pass

    # Visit each place to get details + capture image in one pass
    places = []
    images = []
    total = len(place_links)

    for i, pl in enumerate(place_links):
        if on_progress:
            on_progress(i, total, pl["name"])

        place = {
            "name": pl["name"],
            "address": "",
            "lat": 0.0,
            "lng": 0.0,
            "place_id": "",
            "types": [],
            "maps_url": pl["url"],
        }

        try:
            driver.get(pl["url"])
            time.sleep(3)
            _dismiss_consent(driver)

            # Coordinates from URL
            current_url = driver.current_url
            coord_match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", current_url)
            if coord_match:
                place["lat"] = float(coord_match.group(1))
                place["lng"] = float(coord_match.group(2))

            # Address
            try:
                addr_el = driver.find_element(
                    By.CSS_SELECTOR,
                    "button[data-item-id='address'] div.fontBodyMedium, "
                    "button[data-item-id='oloc'] div.fontBodyMedium"
                )
                place["address"] = addr_el.text.strip()
            except Exception:
                try:
                    title = driver.title
                    if " - " in title:
                        place["address"] = title.split(" - ")[-1].strip()
                except Exception:
                    pass

            # Capture the place photo/screenshot
            img = _capture_place_image(driver, pl["name"])

        except Exception:
            img = None

        places.append(place)
        images.append(img)

    return places, images
