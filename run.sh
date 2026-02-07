#!/usr/bin/env bash
#
# Street View Scraper — one-click launcher for Mac/Linux
# Double-click this file or run: bash run.sh
#

set -e
cd "$(dirname "$0")"

echo ""
echo "  ================================"
echo "   Street View Scraper - Starting"
echo "  ================================"
echo ""

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "  Python 3 is not installed!"
    echo "  Install it:"
    echo "    Mac:   brew install python3"
    echo "    Linux: sudo apt install python3 python3-pip"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# Install dependencies
echo "  Installing dependencies..."
python3 -m pip install -q -r requirements.txt

echo "  Starting..."
echo ""

# Launch the GUI
python3 -m streetview_scraper.launcher
