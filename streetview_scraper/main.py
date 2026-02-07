#!/usr/bin/env python3
"""Street View Scraper Grid — main CLI entry point.

Usage:
    python -m streetview_scraper "coffee shops in downtown Austin"
    python -m streetview_scraper "bike shops in Portland" --max-results 10 --output bikes.xlsx
"""

import argparse
import sys

from .api import search_places, quit_driver
from .grid_ui import GridSelector
from .export import save_to_spreadsheet


def main():
    parser = argparse.ArgumentParser(
        description="Search for places, preview images in a grid, "
                    "and save selected locations to a spreadsheet. "
                    "No API keys required."
    )
    parser.add_argument(
        "query",
        help='Search query, e.g. "pizza restaurants in Brooklyn"',
    )
    parser.add_argument(
        "--max-results", "-n",
        type=int,
        default=20,
        help="Maximum number of results to fetch (default: 20)",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output spreadsheet path (default: auto-generated from query)",
    )
    args = parser.parse_args()

    try:
        _run(args)
    finally:
        quit_driver()


def _run(args):
    print(f"Searching for: {args.query}")
    print("  (first run may take a moment to start the browser)\n")

    def on_progress(i, total, name):
        print(f"  [{i+1}/{total}] {name}")

    places, images = search_places(
        args.query,
        max_results=args.max_results,
        on_progress=on_progress,
    )

    if not places:
        print("No results found for that query.")
        sys.exit(0)

    print(f"\nOpening grid view — select the places you want to save...")
    selector = GridSelector(places, images)
    selected = selector.run()

    if not selected:
        print("No places selected. Nothing to save.")
        sys.exit(0)

    selected_places = [places[i] for i in selected]
    output_path = save_to_spreadsheet(selected_places, args.query, args.output)
    print(f"\nSaved {len(selected_places)} place(s) to: {output_path}")


if __name__ == "__main__":
    main()
