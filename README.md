# Street View Scraper Grid

Search for businesses/places by query, preview their Google Street View images in a visual grid, select the ones you want, and export them to a spreadsheet. **No API keys required.**

## Quick Start (One-Click)

Just double-click the launcher file for your system:

- **Windows:** Double-click `run.bat`
- **Mac/Linux:** Double-click `run.sh` (or run `bash run.sh`)

A window will open asking what you want to search for. Type your query (e.g. "coffee shops in downtown Austin"), click Search, pick your favorites from the grid, and save to a spreadsheet.

The launcher automatically installs dependencies for you.

## Prerequisites

- **Python 3.10+** — [Download here](https://www.python.org/downloads/) (on Windows, check "Add Python to PATH" during install)
- **Google Chrome** or **Chromium** installed on your system

## How it works

1. **Search** — Finds places via [OpenStreetMap Nominatim](https://nominatim.openstreetmap.org/) (free, no key)
2. **Capture** — Opens Google Street View in headless Chrome and takes screenshots (via Selenium)
3. **Grid UI** — Displays results in a scrollable Tkinter grid with checkboxes
4. **Export** — Saves selected places to a styled `.xlsx` spreadsheet

## Advanced: Command-Line Usage

If you prefer the terminal:

```bash
pip install -r requirements.txt
python -m streetview_scraper "coffee shops in downtown Austin"
```

### Options

| Flag | Description |
|---|---|
| `--max-results N` / `-n N` | Number of results (default 20) |
| `--output FILE` / `-o FILE` | Output spreadsheet path (default: auto-generated) |

### Examples

```bash
python -m streetview_scraper "bike shops in Portland" -o bikes.xlsx
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
run.bat                      # Windows one-click launcher
run.sh                       # Mac/Linux one-click launcher
streetview_scraper/
├── __init__.py
├── __main__.py              # python -m entry point
├── main.py                  # CLI argument parsing and orchestration
├── launcher.py              # GUI launcher (no terminal needed)
├── api.py                   # Nominatim search + Selenium Street View capture
├── grid_ui.py               # Tkinter grid selection UI
└── export.py                # Excel spreadsheet export
```

## Notes

- Street View screenshots are cached locally in a `cache/` directory to avoid re-capturing the same locations
- Nominatim has a rate limit of 1 request/second which is respected automatically
- The headless Chrome instance is reused across captures for speed
