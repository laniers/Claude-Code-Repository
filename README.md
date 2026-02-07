# Street View Scraper Grid

Search for businesses/places by query, preview their Google Street View images in a visual grid, select the ones you want, and export them to a spreadsheet.

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get a Google API key

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or use an existing one)
3. Enable these APIs:
   - **Places API (New)**
   - **Street View Static API**
4. Create an API key under **APIs & Services → Credentials**

### 3. Set your API key

```bash
export GOOGLE_API_KEY="your_key_here"
```

Or copy `.env.example` to `.env` and fill it in (if you use a tool like `python-dotenv`).

## Usage

```bash
python -m streetview_scraper "coffee shops in downtown Austin"
```

### Options

| Flag | Description |
|---|---|
| `--max-results N` / `-n N` | Number of results (default 20, max 20) |
| `--output FILE` / `-o FILE` | Output spreadsheet path (default: auto-generated) |

### Examples

```bash
# Search for bike shops, save to a specific file
python -m streetview_scraper "bike shops in Portland" -o bikes.xlsx

# Limit to 5 results
python -m streetview_scraper "barbershops in Brooklyn" -n 5
```

## How it works

1. **Search** — Queries the Google Places Text Search API for matching businesses
2. **Fetch** — Downloads a Street View thumbnail for each result location
3. **Grid UI** — Opens a Tkinter window showing all results in a scrollable grid with checkboxes
4. **Export** — Saves the selected places (name, address, lat/lng, Google Maps link, etc.) to an `.xlsx` spreadsheet

## Spreadsheet columns

| Column | Description |
|---|---|
| Name | Business name |
| Address | Full formatted address |
| Latitude | GPS latitude |
| Longitude | GPS longitude |
| Place ID | Google Place ID |
| Google Maps URL | Direct link to Google Maps |
| Types | Place type tags |

## Project structure

```
streetview_scraper/
├── __init__.py
├── __main__.py      # python -m entry point
├── main.py          # CLI argument parsing and orchestration
├── api.py           # Google Places + Street View API calls
├── grid_ui.py       # Tkinter grid selection UI
└── export.py        # Excel spreadsheet export
```
