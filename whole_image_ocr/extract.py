
"""Whole-image extraction: one OCR call, parse LaTeX table into records."""

import csv
import os
import re
import json
from datetime import datetime

from whole_image_ocr.provider import MathpixOCR
from templates.chikuni import MONTHS, YEAR_BY_MONTH, STATION_ID
from normalization.rainfall_normalizer import normalize_rainfall
from validation.rainfall_validator import validate_rainfall


# Mathpix returns abbreviated month names in the table header.
# Map them to the canonical MONTHS list from templates/chikuni.py.
MONTH_ABBREV = {
    "july": "july",
    "aug": "august",
    "sept": "september",
    "oct": "october",
    "nov": "november",
    "dec": "december",
    "jan": "january",
    "feb": "february",
    "mar": "march",
    "apr": "april",
    "may": "may",
    "june": "june",
}


OUTPUT_COLUMNS = [
    "station_id", "year", "month", "day", "MAX", "MIN", "RAINFALL", "flag"
]

REVIEW_COLUMNS = [
    "station_id", "year", "month", "day",
    "source_path", "raw_ocr", "normalized",
    "confidence", "confidence_rate", "validation_status", "validation_reason",
    "upscaled_path", "request_id", "classification", "flag",
]

# Calendar month order for sorting output chronologically.
MONTH_ORDER = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
}

DAY_RE = re.compile(r"^\s*(\d{1,2})\s*$")


def _clean_cell(cell):
    """Strip LaTeX line endings and whitespace from a cell."""
    return cell.strip().rstrip("\\").strip()


def _parse_latex_table(text):
    """
    Parse the LaTeX tabular that Mathpix returns for a full rainfall sheet.

    Returns a dict: {(month, day): raw_cell_text}
    """
    matches = re.findall(
        r"\\begin\s*\{tabular\}.*?\\end\s*\{tabular\}",
        text,
        re.DOTALL,
    )
    if not matches:
        return {}

    tabular = matches[0]

    # Split rows on \hline
    raw_rows = re.split(r"\\hline", tabular)

    rows = []
    for raw in raw_rows:
        cells = [_clean_cell(c) for c in raw.split("&")]
        # Remove empty trailing cells.
        while cells and cells[-1] == "":
            cells.pop()
        if not cells or all(c == "" for c in cells):
            continue
        rows.append(cells)

    if not rows:
        return {}

    # Find the header row: the row containing month names.
    header_index = None
    for i, cells in enumerate(rows):
        month_count = sum(1 for c in cells if MONTH_ABBREV.get(c.lower()))
        if month_count >= 3:
            header_index = i
            break

    if header_index is None:
        return {}

    header_cells = rows[header_index]
    data_rows = rows[header_index + 1:]

    # Map column index -> month name.
    # Column 0 = day number, columns 1..12 = months.
    col_to_month = {}
    for idx, cell in enumerate(header_cells):
        cell_lower = cell.lower()
        month = MONTH_ABBREV.get(cell_lower)
        if month:
            col_to_month[idx] = month

    detected = {}

    for row in data_rows:
        if not row:
            continue
        day_match = DAY_RE.match(row[0])
        if not day_match:
            continue
        day = int(day_match.group(1))

        for col_index in range(1, len(row)):
            month = col_to_month.get(col_index)
            if month is None:
                continue
            cell_text = row[col_index]
            if cell_text == "":
                continue
            detected[(month, day)] = cell_text

    return detected


def _extract_confidence(page_confidence):
    """Extract a float confidence from Mathpix page_confidence (dict or float)."""
    if page_confidence is None:
        return None
    if isinstance(page_confidence, dict):
        for key in ("confidence", "text_confidence", "layout_confidence"):
            val = page_confidence.get(key)
            if val is not None:
                try:
                    return float(val)
                except (TypeError, ValueError):
                    pass
        return None
    try:
        return float(page_confidence)
    except (TypeError, ValueError):
        return None


def _normalize_value(raw_text):
    """
    Normalize a raw cell text into a rainfall value string.

    Handles hyphen-as-decimal (e.g. '18-0' -> '18.0') before delegating
    to the shared normalizer.
    """
    if not raw_text:
        return None
    # Mathpix sometimes renders a handwritten decimal point as a hyphen.
    text = re.sub(r"(?<=\d)\s*-\s*(?=\d)", ".", raw_text)
    return normalize_rainfall(text)


def extract_sheet(image_path):
    """
    Send the full sheet to Mathpix once, parse the LaTeX table into
    rainfall records, and return (records, review_rows, stats).
    """
    ocr = MathpixOCR()
    response = ocr.recognize(image_path)

    raw_text = response.get("text", "")
    page_confidence = response.get("page_confidence")
    confidence = _extract_confidence(page_confidence)
    detected = _parse_latex_table(raw_text)

    records = []
    review_rows = []
    stats = {
        "total_cells": 0,
        "ocr_cells": 0,
        "accepted": 0,
        "review": 0,
        "errors": 0,
    }

    for day in range(1, 32):
        for month in MONTHS:
            stats["total_cells"] += 1
            year = YEAR_BY_MONTH[month]

            base_record = {
                "station_id": STATION_ID,
                "year": year,
                "month": month,
                "day": day,
                "MAX": "",
                "MIN": "",
                "RAINFALL": "",
                "flag": "",
            }

            raw_text_cell = detected.get((month, day))
            if raw_text_cell is None:
                stats["review"] += 1
                base_record["flag"] = "empty"
                review_rows.append({
                    "station_id": STATION_ID,
                    "year": year,
                    "month": month,
                    "day": day,
                    "source_path": image_path,
                    "raw_ocr": "",
                    "normalized": "",
                    "confidence": confidence if confidence is not None else "",
                    "confidence_rate": "",
                    "validation_status": "REVIEW",
                    "validation_reason": "No value detected in whole-image OCR.",
                    "upscaled_path": "",
                    "request_id": "",
                    "classification": "REVIEW_FORMAT",
                    "flag": "empty",
                })
                records.append(base_record)
                continue

            stats["ocr_cells"] += 1
            normalized = _normalize_value(raw_text_cell)

            validation = validate_rainfall(
                normalized,
                confidence,
            )

            # Auto-accept any normalized value into RAINFALL.
            # The whole-image LaTeX parse is structured and reliable;
            # humans correct errors in the GUI rather than reviewing
            # every cell one-by-one.
            if normalized:
                base_record["RAINFALL"] = normalized
                base_record["flag"] = "review"
                stats["accepted"] += 1
            else:
                stats["review"] += 1
                base_record["flag"] = "empty"

            review_rows.append({
                "station_id": STATION_ID,
                "year": year,
                "month": month,
                "day": day,
                "source_path": image_path,
                "raw_ocr": raw_text_cell,
                "normalized": normalized or "",
                "confidence": confidence if confidence is not None else "",
                "confidence_rate": "",
                "validation_status": validation.status,
                "validation_reason": validation.reason,
                "upscaled_path": "",
                "request_id": "",
                "classification": validation.status,
                "flag": base_record["flag"],
            })

            records.append(base_record)

    return {
        "raw_text": raw_text,
        "records": records,
        "review_rows": review_rows,
        "stats": stats,
    }


def _sort_key(row):
    """Sort by year ascending, calendar month ascending, day ascending."""
    return (
        int(row["year"]),
        MONTH_ORDER.get(row["month"].lower(), 99),
        int(row["day"]),
    )


def write_outputs(output_directory, result, image_path):
    """Write rainfall_records.csv, review_queue.csv, run_summary.json."""
    os.makedirs(output_directory, exist_ok=True)

    # Sort records and review rows chronologically (year, month, day).
    records = sorted(result["records"], key=_sort_key)
    review_rows = sorted(result["review_rows"], key=_sort_key)

    records_path = os.path.join(output_directory, "rainfall_records.csv")
    with open(records_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    review_path = os.path.join(output_directory, "review_queue.csv")
    with open(review_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_COLUMNS)
        writer.writeheader()
        for row in review_rows:
            writer.writerow({key: row.get(key, "") for key in REVIEW_COLUMNS})

    summary = {
        "image": os.path.abspath(image_path),
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "statistics": result["stats"],
    }

    summary_path = os.path.join(output_directory, "run_summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return records_path, review_path, summary_path
