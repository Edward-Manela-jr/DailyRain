
"""Command-line entry point for RainfallDigitizer Phase 4."""

import argparse
import json

from pipeline.process_sheet import process_sheet
from extraction.cell_extractor import extract_daily_cells
from preprocessing.cell_quality import has_ink
import os
import csv


def main():
    parser = argparse.ArgumentParser(
        description="Process a ZMD rainfall sheet."
    )

    parser.add_argument(
        "image",
        help="Path to the rainfall sheet image.",
    )

    parser.add_argument(
        "--output",
        default="output",
        help="Output directory (default: output).",
    )

    parser.add_argument(
        "--screen-only",
        action="store_true",
        help="Extract cells and test blank/non-blank screening without OCR.",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("RAINFALLDIGITIZER - PHASE 4")
    print("=" * 70)
    print()
    print(f"Sheet:   {args.image}")
    print(f"Output:  {args.output}")
    print()

    if args.screen_only:
        cells = extract_daily_cells(
            args.image,
            os.path.join(args.output, "cells"),
        )

        manifest_path = os.path.join(args.output, "cell_manifest.csv")
        os.makedirs(args.output, exist_ok=True)

        manifest_columns = [
            "station_id", "year", "month", "day", "path",
            "x1", "y1", "x2", "y2", "occupied",
        ]

        occupied = 0
        manifest_rows = []

        for cell in cells:
            is_occupied = has_ink(cell["path"])
            if is_occupied:
                occupied += 1

            manifest_rows.append({
                **cell,
                "occupied": str(is_occupied).lower(),
            })

        with open(manifest_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=manifest_columns)
            writer.writeheader()
            writer.writerows(manifest_rows)

        print("Screening complete.")
        print()
        print(f"Total cells:     {len(cells)}")
        print(f"Probably blank:  {len(cells) - occupied}")
        print(f"Probably written: {occupied}")
        print()
        print(f"Manifest:         {manifest_path}")
        print()
        print("No OCR requests were made.")

        return

    summary = process_sheet(
        args.image,
        args.output,
    )

    print("Processing complete.")
    print()
    print(json.dumps(summary["statistics"], indent=2))
    print()
    print(f"Records: {args.output}/rainfall_records.csv")
    print(f"Review:  {args.output}/review_queue.csv")
    print(f"Summary: {args.output}/run_summary.json")


if __name__ == "__main__":
    main()
