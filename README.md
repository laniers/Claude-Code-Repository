# Street View Scraper Grid

Search for businesses/places by query, preview their Google Street View images in a visual grid, select the ones you want, and export them to a spreadsheet. **No API keys required.**

## How it works

1. **Search** — Finds places via [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) (free, no key)
2. **Capture** — Opens Google Street View in headless Chrome and takes screenshots (via Selenium)
3. **Grid UI** — Displays results in a scrollable Tkinter grid with checkboxes
4. **Export** — Saves selected places to a styled `.xlsx` spreadsheet

## Prerequisites

- **Python 3.10+**
- **Google Chrome** or **Chromium** installed on your system

## Setup

```bash
pip install -r requirements.txt
```

That's it. No API keys, no accounts, no configuration.

## Usage

```bash
python -m streetview_scraper "coffee shops in downtown Austin"
```

### Options

| Flag | Description |
|---|---|
| `--max-results N` / `-n N` | Number of results (default 20) |
| `--output FILE` / `-o FILE` | Output spreadsheet path (default: auto-generated) |

### Examples

```bash
# Search for bike shops, save to a specific file
python -m streetview_scraper "bike shops in Portland" -o bikes.xlsx

# Limit to 5 results
python -m streetview_scraper "barbershops in Brooklyn" -n 5
```

## Spreadsheet columns

| Column | Description |
|---|---|
| Name | Business/place name |
| Address | Full address |
| Latitude | GPS latitude |
| Longitude | GPS longitude |
| Place ID | OpenStreetMap place ID |
| Google Maps URL | Direct link to Google Maps |
| Types | Place type tags |

## Project structure

```
streetview_scraper/
├── __init__.py
├── __main__.py      # python -m entry point
├── main.py          # CLI argument parsing and orchestration
├── api.py           # Nominatim search + Selenium Street View capture
├── grid_ui.py       # Tkinter grid selection UI
└── export.py        # Excel spreadsheet export
```

## Notes

- Street View screenshots are cached locally in a `cache/` directory to avoid re-capturing the same locations
- Nominatim has a rate limit of 1 request/second which is respected automatically
- The headless Chrome instance is reused across captures for speed
