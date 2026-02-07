"""Export selected places to an Excel spreadsheet."""

from datetime import datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


HEADER_FILL = PatternFill(start_color="2D7D46", end_color="2D7D46", fill_type="solid")
HEADER_FONT = Font(bold=True, color="FFFFFF", size=11)
THIN_BORDER = Border(
    bottom=Side(style="thin", color="CCCCCC"),
)

COLUMNS = [
    ("Name", 30),
    ("Address", 50),
    ("Latitude", 14),
    ("Longitude", 14),
    ("Place ID", 30),
    ("Google Maps URL", 50),
    ("Types", 30),
]


def save_to_spreadsheet(
    places: list[dict],
    query: str,
    output_path: str | Path | None = None,
) -> Path:
    """Write place data to a styled .xlsx file.

    Args:
        places: List of place dicts (from api.search_places, filtered).
        query: The original search query (used in filename + sheet header).
        output_path: Explicit output file path. If None, auto-generates one.

    Returns:
        The Path of the saved file.
    """
    if output_path is None:
        safe_query = "".join(c if c.isalnum() or c in " -_" else "" for c in query)
        safe_query = safe_query.strip().replace(" ", "_")[:40]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(f"{safe_query}_{ts}.xlsx")
    else:
        output_path = Path(output_path)

    wb = Workbook()
    ws = wb.active
    ws.title = "Selected Places"

    # Header row
    for col_idx, (title, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=title)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center")
        ws.column_dimensions[cell.column_letter].width = width

    # Data rows
    for row_idx, place in enumerate(places, start=2):
        ws.cell(row=row_idx, column=1, value=place.get("name", ""))
        ws.cell(row=row_idx, column=2, value=place.get("address", ""))
        ws.cell(row=row_idx, column=3, value=place.get("lat", 0.0))
        ws.cell(row=row_idx, column=4, value=place.get("lng", 0.0))
        ws.cell(row=row_idx, column=5, value=place.get("place_id", ""))
        ws.cell(row=row_idx, column=6, value=place.get("maps_url", ""))
        ws.cell(row=row_idx, column=7, value=", ".join(place.get("types", [])))

        for col_idx in range(1, len(COLUMNS) + 1):
            ws.cell(row=row_idx, column=col_idx).border = THIN_BORDER

    # Freeze header row
    ws.freeze_panes = "A2"

    # Auto-filter
    ws.auto_filter.ref = ws.dimensions

    wb.save(output_path)
    return output_path
