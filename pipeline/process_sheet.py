
"""End-to-end Phase 4 rainfall-sheet processing."""

import csv
import json
import os
from datetime import datetime

from ocr_providers.mathpix import MathpixOCR
from preprocessing.cell_quality import has_ink
from preprocessing.upscale_cell import upscale_cell
from extraction.cell_extractor import extract_daily_cells
from normalization.rainfall_normalizer import normalize_rainfall
from validation.rainfall_validator import validate_rainfall


OUTPUT_COLUMNS = [
    "station_id",
    "year",
    "month",
    "day",
    "MAX",
    "MIN",
    "RAINFALL",
]


def process_sheet(image_path, output_directory="output"):
    """
    Process one rainfall sheet.

    Produces:
      output/cells/
      output/ocr/
      output/rainfall_records.csv
      output/review_queue.csv
      output/run_summary.json
    """
    cells_dir = os.path.join(output_directory, "cells")
    ocr_dir = os.path.join(output_directory, "ocr")

    cells = extract_daily_cells(image_path, cells_dir)
    ocr = MathpixOCR()

    records = []
    review_rows = []
    stats = {
        "total_cells": len(cells),
        "blank_cells": 0,
        "ocr_cells": 0,
        "accepted": 0,
        "review": 0,
        "errors": 0,
    }

    for cell in cells:
        base_record = {
            "station_id": cell["station_id"],
            "year": cell["year"],
            "month": cell["month"],
            "day": cell["day"],
            "MAX": "",
            "MIN": "",
            "RAINFALL": "",
        }

        # Do not call the paid OCR API for cells that appear blank.
        try:
            occupied = has_ink(cell["path"])
        except Exception as exc:
            stats["errors"] += 1
            review_rows.append({
                **cell,
                "raw_ocr": "",
                "normalized_value": "",
                "confidence": "",
                "confidence_rate": "",
                "status": "REVIEW",
                "reason": f"Cell screening error: {exc}",
            })
            records.append(base_record)
            continue

        if not occupied:
            stats["blank_cells"] += 1
            records.append(base_record)
            continue

        stats["ocr_cells"] += 1

        try:
            upscaled_path = os.path.join(
                ocr_dir,
                cell["month"],
                f"day_{cell['day']:02d}.png",
            )
            upscale_cell(cell["path"], upscaled_path, scale=4)

            result = ocr.recognize(upscaled_path)

            raw_text = result.get("text", "")
            normalized = normalize_rainfall(raw_text)
            confidence = result.get("confidence")
            confidence_rate = result.get("confidence_rate")

            validation = validate_rainfall(
                normalized,
                confidence,
            )

            if validation.status == "ACCEPT":
                base_record["RAINFALL"] = normalized
                stats["accepted"] += 1
            else:
                stats["review"] += 1

            row = {
                **cell,
                "raw_ocr": raw_text,
                "normalized_value": normalized or "",
                "confidence": confidence if confidence is not None else "",
                "confidence_rate": (
                    confidence_rate
                    if confidence_rate is not None
                    else ""
                ),
                "status": validation.status,
                "reason": validation.reason,
            }

            if validation.status == "REVIEW":
                review_rows.append(row)

            records.append(base_record)

        except Exception as exc:
            stats["errors"] += 1
            stats["review"] += 1
            review_rows.append({
                **cell,
                "raw_ocr": "",
                "normalized_value": "",
                "confidence": "",
                "confidence_rate": "",
                "status": "REVIEW",
                "reason": f"OCR error: {exc}",
            })
            records.append(base_record)

    os.makedirs(output_directory, exist_ok=True)

    # Keep a complete record of the screening decision for every cell.
    manifest_path = os.path.join(output_directory, "cell_manifest.csv")
    manifest_columns = [
        "station_id", "year", "month", "day", "path",
        "x1", "y1", "x2", "y2", "occupied",
    ]

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_columns)
        writer.writeheader()
        for cell in cells:
            try:
                occupied = has_ink(cell["path"])
            except Exception:
                occupied = False
            writer.writerow({
                **cell,
                "occupied": str(occupied).lower(),
            })

    records_path = os.path.join(
        output_directory,
        "rainfall_records.csv",
    )

    with open(records_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=OUTPUT_COLUMNS)
        writer.writeheader()
        writer.writerows(records)

    review_path = os.path.join(
        output_directory,
        "review_queue.csv",
    )

    review_columns = [
        "station_id", "year", "month", "day",
        "path", "raw_ocr", "normalized_value",
        "confidence", "confidence_rate",
        "status", "reason",
    ]

    with open(review_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=review_columns)
        writer.writeheader()
        writer.writerows(
            {key: row.get(key, "") for key in review_columns}
            for row in review_rows
        )

    summary = {
        "image": os.path.abspath(image_path),
        "processed_at": datetime.now().isoformat(timespec="seconds"),
        "statistics": stats,
    }

    summary_path = os.path.join(
        output_directory,
        "run_summary.json",
    )

    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary
