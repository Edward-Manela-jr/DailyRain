
"""Extract daily rainfall cells from a detected rainfall table."""

import csv
import os

import cv2

from extraction.grid_detector import detect_rainfall_grid
from templates.chikuni import MONTHS, YEAR_BY_MONTH, STATION_ID


def extract_daily_cells(image_path, output_directory):
    """
    Extract 31 x 12 rainfall cells.

    The first vertical interval is the day-number column.
    The next 12 intervals are July through June.
    """
    horizontal, vertical = detect_rainfall_grid(image_path)

    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"Could not read {image_path}")

    os.makedirs(output_directory, exist_ok=True)
    cells = []

    for day in range(1, 32):
        # horizontal[0] is the header interval; day 1 starts at
        # horizontal[1].
        row_index = day
        y1 = horizontal[row_index]
        y2 = horizontal[row_index + 1]

        for month_index, month in enumerate(MONTHS):
            column_index = month_index + 1
            x1 = vertical[column_index]
            x2 = vertical[column_index + 1]

            cell = image[y1:y2, x1:x2]

            month_directory = os.path.join(output_directory, month)
            os.makedirs(month_directory, exist_ok=True)

            path = os.path.join(month_directory, f"day_{day:02d}.png")
            if not cv2.imwrite(path, cell):
                raise RuntimeError(f"Could not write cell: {path}")

            cells.append({
                "station_id": STATION_ID,
                "year": YEAR_BY_MONTH[month],
                "month": month,
                "day": day,
                "path": path,
                "x1": x1,
                "y1": y1,
                "x2": x2,
                "y2": y2,
            })

    return cells
