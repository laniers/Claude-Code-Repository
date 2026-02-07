#!/usr/bin/env python3
"""Street View Scraper Grid — main CLI entry point.

Usage:
    python -m streetview_scraper "coffee shops in downtown Austin"
    python -m streetview_scraper "bike shops in Portland" --max-results 10 --output bikes.xlsx
"""

import argparse
import sys

from .api import search_places, fetch_street_view_image
from .grid_ui import GridSelector
from .export import save_to_spreadsheet


def main():
    parser = argparse.ArgumentParser(
        description="Search for places, preview Street View images in a grid, "
                    "and save selected locations to a spreadsheet."
    )
    parser.add_argument(
        "query",
        help='Search query, e.g. "pizza restaurants in Brooklyn"',
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=20,
        help="Maximum number of results to fetch (default: 20, max: 20)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output spreadsheet path (default: auto-generated from query)",
    )
    args = parser.parse_args()

    # 1. Search for places
    print(f"Searching for: {args.query}")
    places = search_places(args.query, max_results=args.max_results)

    if not places:
        print("No results found for that query.")
        sys.exit(0)

    print(f"Found {len(places)} places. Fetching Street View images...")

    # 2. Fetch Street View thumbnails
    images = []
    for i, place in enumerate(places):
        print(f"  [{i+1}/{len(places)}] {place['name']}", end="", flush=True)
        img = fetch_street_view_image(place["lat"], place["lng"])
        images.append(img)
        status = " ✓" if img else " (no imagery)"
        print(status)

    # 3. Show grid UI for selection
    print("Opening grid view — select the places you want to save...")
    selector = GridSelector(places, images)
    selected = selector.run()

    if not selected:
        print("No places selected. Nothing to save.")
        sys.exit(0)

    # 4. Export selected places to spreadsheet
    selected_places = [places[i] for i in selected]
    output_path = save_to_spreadsheet(selected_places, args.query, args.output)
    print(f"Saved {len(selected_places)} place(s) to: {output_path}")


if __name__ == "__main__":
    main()
